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
        self._ovc_instance = None

    def validate(self):
        '''
        Validate service data received during creation
        '''
        for key in ['name', 'openvcloud']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=self.data['openvcloud'])

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections with name "%s", requires exactly 1' % (len(ovcs), self.data['openvcloud']))

    def _get_proxy(self, template_uid, service_name):
        '''
        Get proxy object of the service of type @template_uid with name @service_name
        '''

        matches = self.api.services.find(template_uid=template_uid, name=service_name)
        if len(matches) != 1:
            raise RuntimeError('found %d services with name "%s", required exactly one' % (len(matches), service_name))
        return matches[0]

    @property
    def ovc(self):
        '''
        Get ovc client
        '''
        if not self._ovc_instance:
            self._ovc_proxy = self._get_proxy(self.OVC_TEMPLATE, self.data['openvcloud'])
            task = self._ovc_proxy.schedule_action('get_name')
            task.wait()
            self._ovc_instance = task.result
        return j.clients.openvcloud.get(self._ovc_instance)

    @property
    def account(self):
        if not self._account:
            self._account = self.ovc.account_get(
                                        name=self.data['name'],
                                        create=False)
        return self._account

    def get_name(self):
        '''
        Returns the OVC account name.
        Raises StateCheckError when install was not successfully run before.
        '''
        self.state.check('actions', 'install', 'ok')
        return self.data['name']

    def get_users(self, refresh=True):
        '''
        Fetch authorized vdc users
        '''
        if refresh:
            self.account.refresh()
        users = []
        for user in self.account.model['acl']:
            users.append({'name' : user['userGroupId'], 'accesstype' : user['right']})
        self.data['users'] = users
        return users

    def get_openvcloud(self):
        '''
        Return name of ovc instance
        '''
        return self._ovc_instance

    def install(self):
        '''
        Install account
        '''
        
        try:
            self.state.check('actions', 'install', 'ok')
        except StateCheckError:
            pass

        # Set limits
        # if account does not exist, it will create it, 
        # unless 'create' flag is set to False
        self._account = self.ovc.account_get(
            name=self.data['name'],
            create=self.data['create'],
            maxMemoryCapacity=self.data['maxMemoryCapacity'],
            maxVDiskCapacity=self.data['maxVDiskCapacity'],
            maxCPUCapacity=self.data['maxCPUCapacity'],
            maxNumPublicIP=self.data['maxNumPublicIP'],
        )

        self.data['accountID'] = self.account.model['id']

        # get user access info
        self.get_users(refresh=False)

        # update capacity in case account already existed
        self.account.model['maxMemoryCapacity'] = self.data['maxMemoryCapacity']
        self.account.model['maxVDiskCapacity'] = self.data['maxVDiskCapacity']
        self.account.model['maxNumPublicIP'] = self.data['maxNumPublicIP']
        self.account.model['maxCPUCapacity'] = self.data['maxCPUCapacity']
        self.account.save()

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        if not self.data['create']:
            raise RuntimeError('readonly account')

        acc = self.ovc.account_get(self.data['name'], create=False)
        acc.delete()

        self.state.delete('actions', 'install')

    def _fetch_user_name(self, service_name):
        '''
        Get vdcuser name. Succeed only if vdcuser service is installed.
        :param service_name: name of the vdc service 
        '''

        find = self.api.services.find(template_uid=self.VDCUSER_TEMPLATE, name=service_name)
        if len(find) != 1:
            raise ValueError('found %s vdcuser services with name "%s", requires exactly 1' % (len(find), service_name))

        vdcuser = find[0]
        task = vdcuser.schedule_action('get_name')
        task.wait()
        return task.result

    def user_authorize(self, vdcuser, accesstype='R'):
        '''
        Add/Update user access to an account
        :param vdcuser: reference to the vdc user service
        :param accesstype: accesstype that will be set for the user
        '''
        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('readonly account')

        # fetch user name from the vdcuser service
        name = self._fetch_user_name(vdcuser)

        users = self.get_users()
        
        for existent_user in users:
            if existent_user['name'] != name:
                continue

            if existent_user['accesstype'] == accesstype:
                # nothing to do here
                break
            if self.account.update_access(username=name, right=accesstype) == True:
                existent_user['accesstype'] = accesstype
                break
            raise RuntimeError('failed to update access type of user "%s"' % name)
        else:
            # user not found (looped over all users)
            if self.account.authorize_user(username=name, right=accesstype) == True:
                new_user = {
                    "name": name, 
                    "accesstype": accesstype
                    }
                self.data['users'].append(new_user)
            else:
                raise RuntimeError('failed to add user "%s"' % name)

    def user_unauthorize(self, vdcuser):
        '''
        Delete user access
        :param vdcuser: service name
        '''

        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('readonly account')

        self.state.check('actions', 'install', 'ok')
        
        # fetch user name from the vdcuser service
        username = self._fetch_user_name(vdcuser)

        # get user access on the account
        users = self.get_users()

        for user in users:
            if username == user['name']:
                if self.account.unauthorize_user(username=user['name']) == True:
                    self.data['users'].remove(user)
                    break
                raise RuntimeError('failed to remove user "%s"' % username)

    def update(self, maxMemoryCapacity=None, maxVDiskCapacity=None,
               maxNumPublicIP=None, maxCPUCapacity=None):
        '''
        Update account flags

        :param maxMemoryCapacity: The limit on the memory capacity that can be used by the account
        :param maxVDiskCapacity: The limit on the disk capacity that can be used by the account.
        :param maxNumPublicIP: The limit on the number of public IPs that can be used by the account.
        :param maxCPUCapacity: The limit on the CPUs that can be used by the account.
        '''

        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('readonly account')

        # work around not supporting the **kwargs in actions call
        kwargs = locals()

        self.state.check('actions', 'install', 'ok')
        cl = self.ovc
        account = cl.account_get(name=self.data['name'], create=False)

        for key in ['maxMemoryCapacity', 'maxVDiskCapacity',
                    'maxNumPublicIP', 'maxCPUCapacity']:
            value = kwargs[key]
            if value is None:
                continue

            updated = True
            self.data[key] = value
            account.model[key] = value

        if updated:
            account.save()
