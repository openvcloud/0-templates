from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Account(TemplateBase):

    version = '0.0.1'
    template_name = "account"

    VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'

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
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

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
        '''
        Authorize users will make sure the account users are synced to the userd configured
        on the account. Hence, it's better for add_user and delete_user to update the data
        of the instance, and then call this method
        '''
        users = {}

        for user in self.data['users']:
            found = self.api.services.find(template_uid=self.VDCUSER_TEMPLATE, name=user['name'])
            if len(found) != 1:
                raise ValueError('no vdcuser found with name "%s"', user['name'])

            instance = found[0]
            task = instance.schedule_action('get_fqid')
            task.wait()

            users[task.result] = user.get('accesstype', 'ACDRUX')

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

    def add_user(self, user):
        '''
        Add/Update user access to an account
        '''
        name = user['name']

        found = self.api.services.find(template_uid=self.VDCUSER_TEMPLATE, name=name)
        if len(found) != 1:
            raise ValueError('no vdcuser found with name "%s"', name)

        accesstype = user.get('accesstype', 'ACDRUX')
        users = self.data['users']

        for user in users:
            if user['name'] != name:
                continue

            if user['accesstype'] == accesstype:
                # nothing to do here
                return

            user['accesstype'] = accesstype
            break
        else:
            # user not found (looped over all users)
            users.append({'name': name, 'accesstype': accesstype})

        self.data['users'] = users
        cl = self.ovc
        account = cl.account_get(name=self.name, create=False)
        self._authorize_users(account)

    def delete_user(self, username):
        '''
        Delete user access

        :param username: user instance name
        '''
        users = self.data['users']

        for user in users[:]:
            if user['name'] == username:
                users.remove(user)
                break
        else:
            # user not found (looped over all users)
            return

        self.data['users'] = users
        cl = self.ovc
        account = cl.account_get(name=self.name, create=False)
        self._authorize_users(account)

    def update(self, **kwargs):
        '''
        Update account flags

        :param maxMemoryCapacity: The limit on the memory capacity that can be used by the account
        :param maxCPUCapacity: The limit on the CPUs that can be used by the account.
        :param maxNumPublicIP: The limit on the number of public IPs that can be used by the account.
        :param maxDiskCapacity: The limit on the disk capacity that can be used by the account.
        '''
        cl = self.ovc
        account = cl.account_get(name=self.name, create=False)

        self.data.update(kwargs)

        for key in ['maxMemoryCapacity', 'maxDiskCapacity',
                    'maxNumPublicIP', 'maxCPUCapacity']:
            if key in kwargs:
                updated = True
                account.model[key] = self.data[key]

        if updated:
            account.save()
