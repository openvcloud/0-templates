import time
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError
from zerorobot.template.decorator import retry

class Vdc(TemplateBase):

    version = '0.0.1'
    template_name = "vdc"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    DISK_TEMPLATE = 'github.com/openvcloud/0-templates/disk/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._ovc = None
        self._account = None
        self._space = None

    def validate(self):
        """
        Validate service data received during creation
        """
        
        if not self.data['name']:
            raise ValueError('vdc name is required')

        if not self.data['account']:
            raise ValueError('account service name is required')
        
        for key in ['maxMemoryCapacity', 'maxCPUCapacity', 'maxVDiskCapacity', 'maxNumPublicIP']:
            if self.data[key] < -1:
                raise RuntimeError("A resource limit should be a positive number or -1 (unlimited)")

    def get_info(self):
        """ Return vdc info """
        self.state.check('actions', 'install', 'ok')
        return {
            'name' : self.data['name'],
            'account' : self.data['account'],
            'users' : self._get_users(),
            'external_ip': self.space.ipaddr_pub,
        }

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if not self._ovc:
            # get name of ovc service
            proxy = self.api.services.get(
                template_uid=self.ACCOUNT_TEMPLATE, name=self.data['account'])
            acc_info = proxy.schedule_action(action='get_info').wait(die=True).result

            # get name of ovc connection instance
            proxy = self.api.services.get(
                template_uid=self.OVC_TEMPLATE, name=acc_info['openvcloud'])
            ovc_info = proxy.schedule_action(action='get_info').wait(die=True).result
            self._ovc = j.clients.openvcloud.get(ovc_info['name'])

        return self._ovc

    @property
    def account(self):
        """ An account getter """

        if self._account is not None:
            return self._account

        # get actual account name
        proxy = self.api.services.get(
            template_uid=self.ACCOUNT_TEMPLATE, name=self.data['account'])
        acc_info = proxy.schedule_action(action='get_info').wait(die=True).result
        self._account = self.ovc.account_get(acc_info['name'], create=False)

        return self._account

    @property
    def space(self):
        """ A space getter """

        if self._space:
            return self._space

        self._space = self.account.space_get(name=self.data['name'], create=False)
        return self._space

    def _get_users(self, refresh=True):
        """
        Fetch authorized vdc users
        """
        if refresh:
            self.space.refresh()
        users = []
        for user in self.space.model['acl']:
            users.append({'name' : user['userGroupId'], 'accesstype' : user['right']})
        self.data['users'] = users
        return self.data['users']

    @retry((BaseException),
            tries=5, delay=3, backoff=2, logger=None)
    def install(self):
        """
        Install vdc. Will be created if doesn't exist
        """

        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        if not self.data['create']:
            space = self.space
            self._get_users(refresh=False)
            self.data['cloudspaceID'] = space.model['id']
            self.state.set('actions', 'install', 'ok')
            return

        # Set limits
        # if space does not exist, it will create it
        externalnetworkId = self.data.get('externalNetworkID', -1)
        if externalnetworkId == -1:
            externalnetworkId = None
        self._space = self.account.space_get(
            name=self.data['name'],
            create=True,
            maxMemoryCapacity=self.data.get('maxMemoryCapacity', -1),
            maxVDiskCapacity=self.data.get('maxVDiskCapacity', -1),
            maxCPUCapacity=self.data.get('maxCPUCapacity', -1),
            maxNumPublicIP=self.data.get('maxNumPublicIP', -1),
            maxNetworkPeerTransfer=self.data.get('maxNetworkPeerTransfer', -1),
            externalnetworkId=externalnetworkId
        )
        space = self.space
        # add space ID to data
        self.data['cloudspaceID'] = space.model['id']
        # fetch list of authorized users to self.data['users']
        self._get_users(refresh=False)

        # update capacity incase cloudspace already existed update it
        space.model['maxMemoryCapacity'] = self.data.get('maxMemoryCapacity', -1)
        space.model['maxVDiskCapacity'] = self.data.get('maxVDiskCapacity', -1)
        space.model['maxNumPublicIP'] = self.data.get('maxNumPublicIP', -1)
        space.model['maxCPUCapacity'] = self.data.get('maxCPUCapacity', -1)
        space.model['maxNetworkPeerTransfer'] = self.data.get('maxNetworkPeerTransfer', -1)
        space.save()

        status = space.model['status']
        timeout_limit = time.time() + 60
        while time.time() < timeout_limit:
            if status == 'DEPLOYED':
                break
            time.sleep(5)
            status = self.ovc.api.cloudapi.cloudspaces.get(cloudspaceId=self.data['cloudspaceID'])['status']
        else:
            raise j.exceptions.Timeout("VDC not yet deployed")

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        """
        Delete VDC
        """
        if not self.data['create']:
            raise RuntimeError('"%s" is readonly cloudspace' % self.data['name'])

        # check if space exists on account
        for space in self.account.spaces:
            if space.model['name'] == self.data['name']:
                self.space.delete()
                break

        self.state.delete('actions', 'install')

    def enable(self):
        """ Enable VDC """

        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('"%s" is readonly cloudspace' % self.data['name'])

        # Get space, raise error if not found
        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.data['name'],
            create=False
        )

        space.enable('The space should be enabled.')
        self.data['disabled'] = False

    def disable(self):
        """ Disable VDC """

        self.state.check('actions', 'install', 'ok')
        if not self.data['create']:
            raise RuntimeError('"%s" is readonly cloudspace' % self.data['name'])
            
        # Get space, raise error if not found
        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.data['name'],
            create=False
        )

        space.disable('The space should be disabled.')
        self.data['disabled'] = True

    def portforward_create(self, node_service, ports, protocol='tcp'):
        """
        Create port forwards

        :param node_service: name of the service managing the vm
        :param ports: list of portforwards given in form {'source': str, 'destination': str}
        """
        self.state.check('actions', 'install', 'ok')

        proxy = self.api.services.get(
            template_uid=self.NODE_TEMPLATE, name=node_service)
        node_info = proxy.schedule_action(action='get_info').wait(die=True).result
        # add portforwards
        for port in ports:
            self.ovc.api.cloudapi.portforwarding.create(
                cloudspaceId=self.space.id,
                protocol=protocol,
                localPort=port['destination'],
                publicPort=port['source'],
                publicIp=self.space.ipaddr_pub,
                machineId=node_info['id'],
            )

    def portforward_delete(self, node_service, ports, protocol='tcp'):
        """
        Delete port forwards

        :param node_service: name of the service managing the vm
        :param ports: list of portforwards given in form {'source': str, 'destination': str}
        
        """
        self.state.check('actions', 'install', 'ok')

        proxy = self.api.services.get(
            template_uid=self.NODE_TEMPLATE, name=node_service)
        node_info = proxy.schedule_action(action='get_info').wait(die=True).result
        machine_id = node_info['id']
        existent_ports = [(port['publicPort'], port['localPort'], port['id'])
                            for port in self.ovc.api.cloudapi.portforwarding.list(
                                            cloudspaceId=self.space.id, machineId=machine_id,
                                                )]
        # remove portfrowards
        for publicPort, localPort, id in existent_ports:
            for port in ports:
                if str(port['source']) == publicPort and str(port['destination']) == localPort:
                    self.ovc.api.cloudapi.portforwarding.delete(
                        id=id,
                        cloudspaceId=self.space.id,
                        protocol=protocol,
                        localPort=port['destination'],
                        publicPort=port['source'],
                        publicIp=self.space.ipaddr_pub,
                        machineId=machine_id,
                    )

    def user_authorize(self, vdcuser, accesstype='R'):
        """
        Add/Update user access to a space
        :param vdcuser: reference to the vdc user service
        :param accesstype: accesstype that will be set for the user
        """
        self.state.check('actions', 'install', 'ok')

        if not self.data['create']:
            raise RuntimeError('"%s" is readonly cloudspace' % self.data['name'])
        
        # fetch list of authorized users to self.data['users']
        users = self._get_users()

        # derive service name from username
        proxy = self.api.services.get(
            template_uid=self.VDCUSER_TEMPLATE, name=vdcuser)
        user_info = proxy.schedule_action(action='get_info').wait(die=True).result
        name = user_info['name']

        for existent_user in users:
            if existent_user['name'] != name:
                continue

            if existent_user['accesstype'] == accesstype:
                # nothing to do here
                break
            if self.space.update_access(username=name, right=accesstype):
                existent_user['accesstype'] = accesstype
                break
            # fail to update access type
            raise RuntimeError('failed to update accesstype of user "%s"' % name)

        else:
            # user not found (looped over all users)
            if self.space.authorize_user(username=name, right=accesstype):
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
            raise RuntimeError('"%s" is readonly cloudspace' % self.data['name'])

        self.state.check('actions', 'install', 'ok')
        
        # fetch user name from the vdcuser service
        proxy = self.api.services.get(
            template_uid=self.VDCUSER_TEMPLATE, name=vdcuser)
        user_info = proxy.schedule_action(action='get_info').wait(die=True).result
        username = user_info['name']

        # get user access on the cloudspace
        users = self._get_users()

        for user in users:
            if username == user['name']:
                if self.space.unauthorize_user(username=user['name']):
                    self.data['users'].remove(user)
                    break
                raise RuntimeError('failed to remove user "%s"' % username)

    def update(self, maxMemoryCapacity=None, maxVDiskCapacity=None, maxNumPublicIP=None,
               maxCPUCapacity=None, maxNetworkPeerTransfer=None):
        """
        Update account flags

        :param maxMemoryCapacity: The limit on the memory capacity that can be used by the account
        :param maxCPUCapacity: The limit on the CPUs that can be used by the account.
        :param maxNumPublicIP: The limit on the number of public IPs that can be used by the account.
        :param maxVDiskCapacity: The limit on the disk capacity that can be used by the account.
        :param maxNetworkPeerTransfer: Cloudspace limits, max sent/received network transfer peering(GB).
        """

        self.state.check('actions', 'install', 'ok')
        if not self.data['create']:
            raise RuntimeError('"%s" is readonly cloudspace' % self.data['name'])
        # work around not supporting the **kwargs in actions call
        kwargs = locals()
        kwargs.pop('self')

        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.data['name'],
            create=False
        )

        self.data.update(kwargs)

        for key in ['maxMemoryCapacity', 'maxVDiskCapacity', 'maxNumPublicIP',
                    'maxCPUCapacity', 'maxNetworkPeerTransfer']:
            value = kwargs[key]
            if value is not None:
                updated = True
                space.model[key] = self.data[key]

        if updated:
            space.save()
