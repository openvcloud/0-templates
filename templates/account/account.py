from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError
from zerorobot.template.decorator import retry


class Account(TemplateBase):

    version = '0.0.1'
    template_name = "account"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        self._account = None
        self._ovc = None

    def validate(self):
        """
        Validate service data received during creation
        """
        for key in ['name', 'openvcloud']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

    @property
    def ovc(self):
        """ Get ovc client """
        if not self._ovc:
            proxy = self.api.services.get(
                template_uid=self.OVC_TEMPLATE, name=self.data['openvcloud'])
            ovc_info = proxy.schedule_action(action='get_info').wait().result
            self._ovc = j.clients.openvcloud.get(ovc_info['name'])
        return self._ovc

    @property
    def account(self):
        if not self._account:
            self._account = self.ovc.account_get(
                name=self.data['name'],
                create=False)
        return self._account

    def get_info(self):
        """ Get account info """
        self.state.check('actions', 'install', 'ok')
        return {
            'name' : self.data['name'],
            'openvcloud' : self.data['openvcloud'],
            'users' : self._get_users()
        }

    def _get_users(self, refresh=True):
        """ Fetch authorized vdc users """
        if refresh:
            self.account.refresh()
        users = []
        for user in self.account.model['acl']:
            users.append({'name': user['userGroupId'],
                          'accesstype': user['right']})
        self.data['users'] = users
        return users

    @retry((BaseException),
            tries=5, delay=3, backoff=2, logger=None)
    def install(self):
        """ Install account
            
            If action was not successfull it will be retried
        """
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
        self._get_users(refresh=False)

        # update capacity in case account already existed
        self.account.model['maxMemoryCapacity'] = self.data['maxMemoryCapacity']
        self.account.model['maxVDiskCapacity'] = self.data['maxVDiskCapacity']
        self.account.model['maxNumPublicIP'] = self.data['maxNumPublicIP']
        self.account.model['maxCPUCapacity'] = self.data['maxCPUCapacity']
        self.account.save()

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):

        # check if account is listed on given ovc connection
        for acc in self.ovc.accounts:
            if self.data['name'] == acc.model['name']:
                break
        else:
            # if account doesn't exist, do nothing
            return

        if not self.data['create']:
            raise RuntimeError('readonly account')

        # check if account is empty
        if self.account.spaces:
            raise RuntimeError('not empty account cannot be deleted')

        self.account.delete()
        self.state.delete('actions', 'install')

    def user_authorize(self, vdcuser, accesstype='R'):
        """
        Add/Update user access to an account
        :param vdcuser: reference to the vdc user service
        :param accesstype: accesstype that will be set for the user
        """
        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('readonly account')

        # fetch user name from the vdcuser service
        proxy = self.api.services.get(
            template_uid=self.VDCUSER_TEMPLATE, name=vdcuser)
        user_info = proxy.schedule_action(action='get_info').wait().result
        name = user_info['name']  

        users = self._get_users()

        for existent_user in users:
            if existent_user['name'] != name:
                continue

            if existent_user['accesstype'] == accesstype:
                # nothing to do here
                break
            if self.account.update_access(username=name, right=accesstype):
                existent_user['accesstype'] = accesstype
                break
            raise RuntimeError(
                'failed to update access type of user "%s"' % name)
        else:
            # user not found (looped over all users)
            if self.account.authorize_user(username=name, right=accesstype):
                new_user = {
                    "name": name,
                    "accesstype": accesstype
                }
                self.data['users'].append(new_user)
            else:
                raise RuntimeError('failed to add user "%s"' % name)

    def user_unauthorize(self, vdcuser):
        """
        Delete user access
        :param vdcuser: service name
        """

        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('readonly account')

        self.state.check('actions', 'install', 'ok')

        # fetch user name from the vdcuser service
        proxy = self.api.services.get(
            template_uid=self.VDCUSER_TEMPLATE, name=vdcuser)
        user_info = proxy.schedule_action(action='get_info').wait().result
        username = user_info['name']

        # get user access on the account
        users = self._get_users()

        for user in users:
            if username == user['name']:
                if self.account.unauthorize_user(username=user['name']):
                    self.data['users'].remove(user)
                    break
                raise RuntimeError('failed to remove user "%s"' % username)

    def update(self, maxMemoryCapacity=None, maxVDiskCapacity=None,
               maxNumPublicIP=None, maxCPUCapacity=None):
        """
        Update account flags

        :param maxMemoryCapacity: The limit on the memory capacity that can be used by the account
        :param maxVDiskCapacity: The limit on the disk capacity that can be used by the account.
        :param maxNumPublicIP: The limit on the number of public IPs that can be used by the account.
        :param maxCPUCapacity: The limit on the CPUs that can be used by the account.
        """

        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('readonly account')

        # work around not supporting the **kwargs in actions call
        kwargs = locals()

        self.state.check('actions', 'install', 'ok')

        account = self.ovc.account_get(name=self.data['name'], create=False)

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
