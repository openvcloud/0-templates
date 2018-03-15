import time
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Vdc(TemplateBase):

    version = '0.0.1'
    template_name = "vdc"

    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._ovc = None
        self._account = None
        self._space = None

    def validate(self):
        if not self.data['account']:
            raise ValueError('account is required')

        # validate accounts
        accounts = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=self.data['account'])
        if len(accounts) != 1:
            raise RuntimeError('found %s accounts, requires exactly one' % len(accounts))

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        matches = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=self.data['account'])
        if len(matches) != 1:
            raise ValueError('found %s accounts with name "%s", required exactly one' % (len(matches), self.data['account']))

        instance = matches[0]
        # get connection
        task = instance.schedule_action('get_openvcloud')
        task.wait()
        self._ovc = j.clients.openvcloud.get(task.result)

        return self._ovc

    @property
    def account(self):
        """
        An account getter
        """
        if self._account is not None:
            return self._account
        ovc = self.ovc

        self._account = ovc.account_get(self.data['account'], create=False)
        return self._account

    def get_account(self):
        return self.data['account']

    @property
    def space(self):
        if self._space:
            return self._space
        acc = self.account
        return acc.space_get(name=self.name)

    @property
    def get_users(self):
        '''
        Fetch authorized vdc users
        '''
        self.space.refresh()
        users = []
        for user in self.space.model['acl']:
            users.append({'name' : user['userGroupId'], 'accesstype' : user['right']})
        self.data['users'] = users
        return self.data['users']

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass
        acc = self.account

        if not self.data['create']:
            space = acc.space_get(
                name=self.name,
                create=True
            )
            self.data['cloudspaceID'] = space.model['id']
            self.state.set('actions', 'install', 'ok')
            return

        # Set limits
        # if space does not exist, it will create it
        externalnetworkId = self.data.get('externalNetworkID', -1)
        if externalnetworkId == -1:
            externalnetworkId = None
        space = acc.space_get(
            name=self.name,
            create=True,
            maxMemoryCapacity=self.data.get('maxMemoryCapacity', -1),
            maxVDiskCapacity=self.data.get('maxDiskCapacity', -1),
            maxCPUCapacity=self.data.get('maxCPUCapacity', -1),
            maxNumPublicIP=self.data.get('maxNumPublicIP', -1),
            maxNetworkPeerTransfer=self.data.get('maxNetworkPeerTransfer', -1),
            externalnetworkId=externalnetworkId
        )

        # add space ID to data
        self.data['cloudspaceID'] = space.model['id']

        # fetch list of authorized users to self.data['users']
        self.get_users

        # update capacity incase cloudspace already existed update it
        space.model['maxMemoryCapacity'] = self.data.get('maxMemoryCapacity', -1)
        space.model['maxVDiskCapacity'] = self.data.get('maxDiskCapacity', -1)
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
        if not self.data['create']:
            raise RuntimeError('readonly cloudspace')
        space = self.account.space_get(self.name)
        space.delete()

    def enable(self):
        if not self.data['create']:
            raise RuntimeError('readonly cloudspace')
        # Get space, raise error if not found
        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.name,
            create=False
        )

        space.enable('The space should be enabled.')
        self.data['disabled'] = False

    def disable(self):
        if not self.data['create']:
            raise RuntimeError('readonly cloudspace')
        # Get space, raise error if not found
        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.name,
            create=False
        )

        space.disable('The space should be disabled.')
        self.data['disabled'] = True

    def get_public_ip(self):
        return self.space.ipaddr_pub

    def portforward_create(self, machineId=None, port_forwards=[], protocol='tcp'):
        """
        Create port forwards
        """
        ovc = self.ovc
        space = self.space

        # add portforwards
        for port in port_forwards:
            ovc.api.cloudapi.portforwarding.create(
                cloudspaceId=space.id,
                protocol=protocol,
                localPort=port['destination'],
                publicPort=port['source'],
                publicIp=space.ipaddr_pub,
                machineId=machineId,
                )

    def portforward_delete(self, machineId=None, port_forwards=[], protocol='tcp'):
        """
        Delete port forwards
        """
        ovc = self.ovc
        space = self.space
        existent_ports = [(port['publicPort'], port['localPort'], port['id'])
                            for port in ovc.api.cloudapi.portforwarding.list(
                                            cloudspaceId=space.id, machineId=machineId,
                                                )]
        # remove portfrowards
        for publicPort, localPort, id in existent_ports:
            for port in port_forwards:
                if str(port['source']) == publicPort and str(port['destination']) == localPort:
                    ovc.api.cloudapi.portforwarding.delete(
                        id=id,
                        cloudspaceId=space.id,
                        protocol=protocol,
                        localPort=port['destination'],
                        publicPort=port['source'],
                        publicIp=space.ipaddr_pub,
                        machineId=machineId,
                    )

    def user_add(self, user):
        '''
        Add/Update user access to a space
        :param user: user dictionary {'name': , 'accesstype': }
        '''
        if not self.data['create']:
            raise RuntimeError('readonly cloudspace')

        self.state.check('actions', 'install', 'ok')

        # fetch list of authorized users to self.data['users']
        self.get_users
        users = self.data['users']

        name = user['name']
        accesstype = user.get('accesstype')
        
        for existent_user in users:
            if existent_user['name'] != name:
                continue

            if existent_user['accesstype'] == accesstype:
                # nothing to do here
                break

            if self.space.update_access(username=name, right=accesstype) == True:
                existent_user['accesstype'] = accesstype
                break
            # fail to update access type
            raise RuntimeError('failed to update accesstype of user "%s"' % name)

        else:
            # user not found (looped over all users)
            if self.space.authorize_user(username=name, right=accesstype) == True:
                users.append(user)
            else:
                raise RuntimeError('failed to add user "%s"' % name)

        self.save()

    def user_delete(self, username):
        '''
        Delete user access

        :param username: user instance name
        '''
        if not self.data['create']:
            raise RuntimeError('readonly cloudspace')

        self.state.check('actions', 'install', 'ok')

        import ipdb; ipdb.set_trace()
        # fetch list of authorized users to self.data['users']
        self.get_users
        users = self.data['users']

        for user in users:
            if username == user['name']:
                if self.space.unauthorize_user(username=user['name']):
                    users.remove(user)
                    break
                else:
                    raise RuntimeError('failed to delete user "%s"' % user['name'])
        
        self.save()

    def update(self, maxMemoryCapacity=None, maxDiskCapacity=None, maxNumPublicIP=None,
               maxCPUCapacity=None, maxNetworkPeerTransfer=None):
        '''
        Update account flags

        :param maxMemoryCapacity: The limit on the memory capacity that can be used by the account
        :param maxCPUCapacity: The limit on the CPUs that can be used by the account.
        :param maxNumPublicIP: The limit on the number of public IPs that can be used by the account.
        :param maxDiskCapacity: The limit on the disk capacity that can be used by the account.
        :param maxNetworkPeerTransfer: Cloudspace limits, max sent/received network transfer peering(GB).
        '''
        if not self.data['create']:
            raise RuntimeError('readonly cloudspace')
        # work around not supporting the **kwargs in actions call
        kwargs = locals()
        kwargs.pop('self')

        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.name,
            create=False
        )

        self.data.update(kwargs)

        for key in ['maxMemoryCapacity', 'maxDiskCapacity', 'maxNumPublicIP',
                    'maxCPUCapacity', 'maxNetworkPeerTransfer']:
            value = kwargs[key]
            if value is not None:
                updated = True
                space.model[key] = self.data[key]

        if updated:
            space.save()

