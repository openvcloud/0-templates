from js9 import j
from zerorobot.template.base import TemplateBase

class Nodeovc(TemplateBase):

    version = '0.0.1'
    template_name = "nodeovc"

    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self.data['name'] = name
        self._ovc = None

    def validate(self):
        # Get object for an OVC service, make sure exactly one is running
        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=self.data.get('openvcloud', None))
        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['openvcloud'] = ovcs[0].name
        
        # Get object for an account service, make sure exactly one is running
        accounts = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=self.data.get('account', None))
        if len(accounts) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['account'] = accounts[0].name

        # Get loccation
        locations = self.ovc.locations
        if len(locations) != 1:
            raise RuntimeError('found %s openvcloud locations, requires exactly 1' % len(locations))

        self.data['location'] = locations[0]['name']

        # Get a path of the ssh-key uploaded to the ssh-agent
        sshkeys = self.api.services.find(template_uid=self.SSH_TEMPLATE)
        if len(sshkeys) != 1:
            raise RuntimeError('found %s ssh services, requires exactly 1' % len(sshkeys))

        # Get key name
        self.data['sshkeyname'] = sshkeys[0].data['path'].split('/')[-1]

    def update_data(self):
        pass

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        self._ovc = j.clients.openvcloud.get(self.data['openvcloud'])
        return self._ovc

    def install(self):        
        machine = self.machine
        if not machine:
            self._machine_create()

        self._configure_ports(machine)

    @property
    def space(self):
        return self.ovc.space_get(accountName=self.data['account'],
                                 spaceName=self.data['openvcloud'],
                                 location=self.data['location'])

    @property
    def machine(self):
        return self.space.machines.get(self.data['name'])

    def _machine_create(self):
        return self.space.machine_create(
                name=self.data['name'],
                sshkeyname= self.data['sshkeyname'],
        )
                # image=self.data['osImage'],
                # memsize=self.data['memsize'],
                # vcpus=self.data['vcpus'],
                # disksize=self.data['bootDiskSize'],
                # datadisks=self.data['disks'],
                # sizeId=self.data['sizeId'

    def _configure_ports(self, machine):

        # get list of existing ports at the vm
        existent_ports = [port['publicPort'] for port in machine.portforwards]

        for port in self.data['ports']:
            # check if ports do not exist yet
            if port['destination'] not in existent_ports:
                # create portforward
                machine.portforward_create(
                    publicport=port['destination'], 
                    localport=port['source'], 
                    protocol='tcp',
                    )

    def uninstall(self):
        space = self.space

        # check if the machine is in the space
        if self.machine:
            self.machine.delete()

    def start(self):
        machine = self.machine
#        _check_ssh_authorization(job.service, machine)
        machine.start()


    def stop(self):
        machine = self.machine
#        _check_ssh_authorization(job.service, machine)
        machine.stop()


    def restart(self):
        machine = self.machine
#        _check_ssh_authorization(job.service, machine)
        machine.restart()


    def pause(self):
        machine = self.machine
#        _check_ssh_authorization(job.service, machine)
        machine.pause()


    def resume(self):
        machine = self.machine
#        _check_ssh_authorization(job.service, machine)
        machine.resume()


    def reset(self):
        machine = self.machine
#        _check_ssh_authorization(job.service, machine)
        machine.reset()    
        

