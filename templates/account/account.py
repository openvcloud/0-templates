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
        self._account = None

    def validate(self):
        if not self.data['openvcloud']:
            raise ValueError('openvcloud is mandatory')

        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=self.data['openvcloud'])

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

    @property
    def ovc(self):
        return j.clients.openvcloud.get(self.data['openvcloud'])

    @property
    def account(self):
        if not self._account:
            self._account = self.ovc.account_get(
                                        name=self.name,
                                        create=False
                                     )
        return self._account

    @property
    def users(self):
        '''
        Fetch authorized account users
        '''
        self.data['users'] = []
        for user in self.account.model['acl']:
            self.data['users'].append({'name' : user['userGroupId'], 'accesstype' : user['right']} )
        
        return self.data['users']

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
            self.account

            self.state.set('actions', 'install', 'ok')
            return

        # Set limits
        # if account does not exist, it will create it
        self._account = cl.account_get(
            name=self.name,
            create=True,
            maxMemoryCapacity=self.data['maxMemoryCapacity'],
            maxVDiskCapacity=self.data['maxDiskCapacity'],
            maxCPUCapacity=self.data['maxCPUCapacity'],
            maxNumPublicIP=self.data['maxNumPublicIP'],
        )

        self.data['accountID'] = self.account.model['id']
        # get list of authorized users
        self.data['users'] = self.account.authorized_users

        # update capacity in case account already existed
        self.account.model['maxMemoryCapacity'] = self.data['maxMemoryCapacity']
        self.account.model['maxVDiskCapacity'] = self.data['maxDiskCapacity']
        self.account.model['maxNumPublicIP'] = self.data['maxNumPublicIP']
        self.account.model['maxCPUCapacity'] = self.data['maxCPUCapacity']
        self.account.save()

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        if not self.data['create']:
            raise RuntimeError('readonly account')
        self.state.check('actions', 'install', 'ok')
        cl = self.ovc
        acc = cl.account_get(self.name, create=False)
        acc.delete()

    def user_add(self, users):
        '''
        Add/Update user access to an account
        :param users: list of users if form of dictionary {'name': , 'accesstype': }
        '''
        if not self.data['create']:
            raise RuntimeError('readonly account')

        self.state.check('actions', 'install', 'ok')
        import ipdb; ipdb.set_trace()
        existent_users = self.users
        for user in users:
            name = user['name']
            accesstype = user.get('accesstype')
            
            for existent_user in existent_users:
                if existent_user['name'] != name:
                    continue

                if existent_user['accesstype'] == accesstype:
                    # nothing to do here
                    break

                self.account.update_access(username=name, right=accesstype)
                break
            else:
                # user not found (looped over all users)
                self.account.authorize_user(username=name, right=accesstype)
            
        self.users
        self.save()

    def user_delete(self, usernames):
        '''
        Delete user access
        :param usernames: list of user instance names
        '''
        if not self.data['create']:
            raise RuntimeError('readonly account')

        self.state.check('actions', 'install', 'ok')
        users = self.users
        for username in usernames:
            for user in users:
                if username == user['name']:
                    self.account.unauthorize_user(username=user['name'])
                    break
        
        self.users
        self.save()

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
