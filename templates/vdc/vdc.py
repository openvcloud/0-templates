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
        for key in ['location']:
            if not self.data.get('location'):
                raise ValueError('%s is required' % key)

        if not self.data['account']:
            raise ValueError('account is required')

        # validate accounts
        accounts = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=self.data['account'])

        if len(accounts) != 1:
            raise RuntimeError('found %s accounts, requires exactly one' % len(accounts))

        # validate users
        for user in self.data['users']:
            users = self.api.services.find(template_uid=self.VDCUSER_TEMPLATE, name=user['name'])
            if len(users) != 1:
                raise ValueError('no vdcuser found with name "%s"', user['name'])

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

    @property
    def space(self):
        if self._space:
            return self._space
        acc = self.account
        return acc.space_get(name=self.name, location=self.data['location'])

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass
        acc = self.account

        # Set limits
        # if space does not exist, it will create it
        externalnetworkId = self.data.get('externalNetworkID', -1)
        if externalnetworkId == -1:
            externalnetworkId = None

        space = acc.space_get(
            name=self.name,
            location=self.data['location'],
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

        self._authorize_users(space)

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

    def _authorize_users(self, space):
        users = {}
        VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
        for user in self.data['users']:
            found = self.api.services.find(template_uid=VDCUSER_TEMPLATE, name=user['name'])
            if len(found) != 1:
                raise ValueError('no vdcuser found with name "%s"', user['name'])

            instance = found[0]
            task = instance.schedule_action('get_fqid')
            task.wait()

            users[task.result] = user.get('accesstype', 'ACDRUX')

        authorized = {user['userGroupId']: user['right'] for user in space.model['acl']}

        toremove = []
        for user, current_perm in authorized.items():
            new_perm = users.pop(user, None)
            if new_perm is None:
                # user has been removed
                # we delay removing the user to avoid deleting the last admin, in case a new one is added
                toremove.append(user)
            elif set(new_perm) != set(current_perm):
                space.update_access(username=user, right=new_perm)

        for user, new_perm in users.items():
            space.authorize_user(username=user, right=new_perm)

        for user in toremove:
            space.unauthorize_user(username=user)

    def uninstall(self):
        space = self.account.space_get(self.name, self.data['location'])
        space.delete()

    def enable(self):
        # Get space, raise error if not found
        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.name,
            location=self.data['location'],
            create=False
        )

        space.enable('The space should be enabled.')
        self.data['disabled'] = False

    def disable(self):
        # Get space, raise error if not found
        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.name,
            location=self.data['location'],
            create=False
        )

        space.disable('The space should be disabled.')
        self.data['disabled'] = True

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
                publicIp=space.get_space_ip(),
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
                        publicIp=space.get_space_ip(),
                        machineId=machineId,
                )

    def user_add(self, user):
        '''
        Add/Update user access to an space
        '''
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
        space = self.account.space_get(
            name=self.name,
            location=self.data['location'],
            create=False
        )

        self._authorize_users(space)

    def user_delete(self, username):
        '''
        Delete user access

        :param username: user instance name
        '''
        self.state.check('actions', 'install', 'ok')
        users = self.data['users']

        for user in users[:]:
            if user['name'] == username:
                users.remove(user)
                break
        else:
            # user not found (looped over all users)
            return

        self.data['users'] = users
        space = self.account.space_get(
            name=self.name,
            location=self.data['location'],
            create=False
        )
        self._authorize_users(space)

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
        # work around not supporting the **kwargs in actions call
        kwargs = locals()
        kwargs.pop('self')

        self.state.check('actions', 'install', 'ok')
        space = self.account.space_get(
            name=self.name,
            location=self.data['location'],
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


def get_user_accessright(username, service):
    for u in service.model.data.uservdc:
        if u.name == username:
            return u.accesstype


def execute_routeros_script(job):
    service = job.service
    if 'g8client' not in service.producers:
        raise j.exceptions.AYSNotFound("No producer g8client found. Cannot continue executing of %s" % service)
    script = service.model.data.script
    if not script:
        raise j.exceptions.AYSNotFound("Param script can't be empty. Cannot continue executing of %s" % service)
    script.replace("\n", ";")
    g8client = service.producers["g8client"][0]
    config_instance = "{}_{}".format(g8client.aysrepo.name, g8client.model.data.instance)
    cl = j.clients.openvcloud.get(instance=config_instance, create=False, die=True, sshkey_path="/root/.ssh/ays_repos_key")
    acc = cl.account_get(service.model.data.account)
    space = acc.space_get(service.model.dbobj.name, service.model.data.location)
    space.execute_routeros_script(script)
