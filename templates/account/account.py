from js9 import j
from zerorobot.template.base import TemplateBase


class Account(TemplateBase):

    version = '0.0.1'
    template_name = "account"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
        ovcs = self.api.services.find(template_uid=OVC_TEMPLATE, name=self.data.get('openvcloud', None))

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['openvcloud'] = ovcs[0].name

        # validate users
        VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
        for user in self.data['users']:
            users = self.api.services.find(template_uid=VDCUSER_TEMPLATE, name=user['name'])
            if len(users) != 1:
                raise ValueError('no vdcuser found with name "%s"', user['name'])

    @property
    def ovc(self):
        return j.clients.openvcloud.get(self.data['openvcloud'])

    def get_openvcloud(self):
        return self.data['openvcloud']

    def install(self):
        cl = self.ovc
        # Set limits
        # if account does not exist, it will create it
        account = cl.account_get(
            name=self.name,
            create=True,
            maxMemoryCapacity=self.data['maxMemoryCapacity'],
            maxVDiskCapacity=self.data['maxDiskCapacity'],
            maxCPUCapacity=self.data['maxCPUCapacity'],
            maxNumPublicIP=self.data['maxNumPublicIP'],
        )

        self.data['accountID'] = account.model['id']

        self._authorize_users(account)

        # update capacity in case account already existed
        account.model['maxMemoryCapacity'] = self.data['maxMemoryCapacity']
        account.model['maxVDiskCapacity'] = self.data['maxDiskCapacity']
        account.model['maxNumPublicIP'] = self.data['maxNumPublicIP']
        account.model['maxCPUCapacity'] = self.data['maxCPUCapacity']
        account.save()

        self.state.set('actions', 'install', 'ok')

    def _authorize_users(self, account):
        users = {}
        VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
        for user in self.data['users']:
            found = self.api.services.find(template_uid=VDCUSER_TEMPLATE, name=user['name'])
            if len(found) != 1:
                raise ValueError('no vdcuser found with name "%s"', user['name'])

            instance = found[0]
            task = instance.schedule_action('get_fqid')
            task.wait()

            users[task.result] = user['accesstype']

        authorized = {user['userGroupId']: user['right'] for user in account.model['acl']}

        toremove = []
        for user, current_perm in authorized.items():
            new_perm = users.pop(user, None)
            if new_perm is None:
                # user has been removed
                # we delay removing the user to avoid deleting the last admin, in case a new one is added
                toremove.append(user)
            elif set(new_perm) != set(current_perm):
                account.update_access(username=user, right=new_perm)

        for user, new_perm in users.items():
            account.authorize_user(username=user, right=new_perm)

        for user in toremove:
            account.unauthorize_user(username=user)

    def uninstall(self):
        cl = self.ovc
        acc = cl.account_get(self.name)
        acc.delete()

    def update_data(self, data):
        cl = self.ovc
        account = cl.account_get(name=self.name, create=False)

        self.data.update(data)

        if 'users' in data:
            # sync users
            self._authorize_users(account)

        updated = False
        for key in ['maxMemoryCapacity', 'maxDiskCapacity',
                    'maxNumPublicIP', 'maxCPUCapacity']:
            if key in data:
                updated = True
                account.model[key] = self.data[key]

        if updated:
            account.save()
