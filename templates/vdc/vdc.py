import time
from js9 import j
from zerorobot.template.base import TemplateBase


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

        # validate accounts
        accounts = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=self.data.get('account', None))

        if len(accounts) != 1:
            raise RuntimeError('found %s accounts, requires exactly one' % len(accounts))

        self.data['account'] = accounts[0].name

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
        ovc = self.ovc

        self._account = ovc.account_get(self.data['account'])
        return self._account

    @property
    def space(self):
        if self._space:
            return self._space
        acc = self.account
        return acc.space_get(name=self.name, location=self.data['location'])

    def install(self):
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

        self.state.set('acitons', 'install', 'ok')

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

            users[task.result] = user['accesstype']

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
        space = self.account.space_get(
            name=self.name,
            location=self.data['location'],
            create=False
        )

        space.enable('The space should be enabled.')
        self.data['disabled'] = False

    def disable(self):
        # Get space, raise error if not found
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

def get_user_accessright(username, service):
    for u in service.model.data.uservdc:
        if u.name == username:
            return u.accesstype


def processChange(job):
    service = job.service

    args = job.model.args
    category = args.pop('changeCategory')

    if 'g8client' not in service.producers:
        raise j.exceptions.AYSNotFound("No producer g8client found. Cannot continue processChange of %s" % service)
    g8client = service.producers["g8client"][0]

    config_instance = "{}_{}".format(g8client.aysrepo.name, g8client.model.data.instance)
    cl = j.clients.openvcloud.get(instance=config_instance, create=False, die=True, sshkey_path="/root/.ssh/ays_repos_key")
    acc = cl.account_get(service.model.data.account)

    # Get given space, raise error if not found
    space = acc.space_get(name=service.model.dbobj.name,
                          location=service.model.data.location,
                          create=False)
    if category == "dataschema" and service.model.actionsState['install'] == 'ok':
        for key, value in args.items():
            if key == 'uservdc':
                # value is a list of (uservdc)
                if not isinstance(value, list):
                    raise j.exceptions.Input(message="%s should be a list" % key)
                if 'uservdc' in service.producers:
                    for s in service.producers['uservdc']:
                        if not any(v['name'] == s.name for v in value):
                            service.model.producerRemove(s)
                        for v in value:
                            accessRight = v.get('accesstype', '')
                            if v['name'] == s.name and accessRight != get_user_accessright(s.name, service):
                                name = s.name + '@' + s.model.data.provider if s.model.data.provider else s.name
                                space.update_access(name, accessRight)
                for v in value:
                    userservice = service.aysrepo.serviceGet('uservdc', v['name'])
                    if userservice not in service.producers.get('uservdc', []):
                        service.consume(userservice)
            elif key == 'location' and service.model.data.location != value:
                raise RuntimeError("Cannot change attribute location")
            setattr(service.model.data, key, value)

        authorization_user(space, service)

        # update capacity incase cloudspace already existed update it
        space.model['maxMemoryCapacity'] = service.model.data.maxMemoryCapacity
        space.model['maxVDiskCapacity'] = service.model.data.maxDiskCapacity
        space.model['maxNumPublicIP'] = service.model.data.maxNumPublicIP
        space.model['maxCPUCapacity'] = service.model.data.maxCPUCapacity
        space.save()

        service.save()


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
