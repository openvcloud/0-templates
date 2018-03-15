from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Account(TemplateBase):

    version = '0.0.1'
    template_name = "account"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        if not self.data['openvcloud']:
            raise ValueError('openvcloud is mandatory')

        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=self.data['openvcloud'])

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        # validate users
        for user in self.data['users']:
            users = self.api.services.find(template_uid=self.VDCUSER_TEMPLATE, name=user['name'])
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

        if not self.data['create']:
            account = cl.account_get(
                name=self.name,
                create=False
            )

            self.state.set('actions', 'install', 'ok')
            return

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
        if not self.data['create']:
            raise RuntimeError('readonly account')

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

        for user, current_perm in authorized.items():
            new_perm = users.pop(user, None)
            if new_perm is None:
                # user is not configured on this instance.
                # we don't update this user
                continue
            elif set(new_perm) != set(current_perm):
                account.update_access(username=user, right=new_perm)

        for user, new_perm in users.items():
            account.authorize_user(username=user, right=new_perm)

    def uninstall(self):
        if not self.data['create']:
            raise RuntimeError('readonly account')
        self.state.check('actions', 'install', 'ok')
        cl = self.ovc
        acc = cl.account_get(self.name, create=False)
        acc.delete()

    def user_add(self, user):
        '''
        Add/Update user access to an account
        '''
        if not self.data['create']:
            raise RuntimeError('readonly account')

        self.state.check('actions', 'install', 'ok')
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

    def user_delete(self, username):
        '''
        Delete user access

        :param username: user instance name
        '''
        if not self.data['create']:
            raise RuntimeError('readonly account')

        self.state.check('actions', 'install', 'ok')
        users = self.data['users']

        for user in users[:]:
            if user['name'] == username:
                users.remove(user)
                break
        else:
            # user not found (looped over all users)
            return

        cl = self.ovc
        account = cl.account_get(name=self.name, create=False)
        account.unauthorize_user(username=username)
        self.data['users'] = users

    def update(self, maxMemoryCapacity=None, maxDiskCapacity=None,
               maxNumPublicIP=None, maxCPUCapacity=None):
        '''
        Update account flags

        :param maxMemoryCapacity: The limit on the memory capacity that can be used by the account
        :param maxCPUCapacity: The limit on the CPUs that can be used by the account.
        :param maxNumPublicIP: The limit on the number of public IPs that can be used by the account.
        :param maxDiskCapacity: The limit on the disk capacity that can be used by the account.
        '''
        if not self.data['create']:
            raise RuntimeError('readonly account')

        # work around not supporting the **kwargs in actions call
        kwargs = locals()

        self.state.check('actions', 'install', 'ok')
        cl = self.ovc
        account = cl.account_get(name=self.name, create=False)

        for key in ['maxMemoryCapacity', 'maxDiskCapacity',
                    'maxNumPublicIP', 'maxCPUCapacity']:
            value = kwargs[key]
            if value is None:
                continue

            updated = True
            self.data[key] = value
            account.model[key] = value

        if updated:
            account.save()
