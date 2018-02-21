from js9 import j
from zerorobot.template.base import TemplateBase

class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._ovc = None
        self._vdc = None
        self._machine = None

    def validate(self):
        if not self.data['vdc']:
            raise RuntimeError('vdc name should be given')
        # ensure uploaded key
        self.sshkey

    def update_data(self, data):
        # merge the new data
        self.data.update(data)
        self.save()

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc
        
        vdc = self.vdc
        instance = vdc.ovc.instance
        self._ovc = j.clients.openvcloud.get(instance=instance)

        return self._ovc

    @property
    def vdc(self):
        if self._vdc:
            return self._vdc

        # Get object for an VDC service, make sure exactly one is running
        vdc = self.api.services.find(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        if len(vdc) != 1:
            raise RuntimeError('found %s vdc, requires exactly 1' % len(vdc))
        
        self._vdc = vdc[0]

        return self._vdc

    @property
    def space(self):
        return self.ovc.space_get(
            accountName=None,
            spaceName=self.data['vdc']
            )

    @property
    def sshkey(self):
        """ Get a path and keyname of the sshkey service """

        sshkeys = self.api.services.find(template_uid=self.SSH_TEMPLATE)
        if not len(sshkeys):
            raise RuntimeError('no %s ssh services found' % len(sshkeys))

        # Get key name and path
        path = sshkeys[0].data['path']
        key = path.split('/')[-1]

        return key         

    @property
    def machine(self):
        if self._machine:
            return self._machine
        return self.space.machines.get(self.name)

    def install(self):
        machine = self.machine
        if not machine:
            machine = self._machine_create()

        # Get data from the vm
        ip_private, vm_info = machine.machineip_get()
        self.data['sshLogin'] = vm_info['accounts'][0]['login']
        self.data['sshPassword']= vm_info['accounts'][0]['password']
        self.data['ipPrivate'] = ip_private
        self.data['ipPublic'] = machine.space.model['publicipaddress']
        self.data['machineId'] = machine.id

        self.portforward_create(self.data['ports'])
        # TODO: self._configure_disks()

        self.state.set('actions', 'install', 'ok')
        self.save()

    def uninstall(self):
        # check if the machine is in the space
        machine = self.machine
        if machine:
            self.machine.delete()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def _machine_create(self):
        """ Create a new machine """

        self._machine =  self.space.machine_create(
            name=self.data['name'],
            sshkeyname= self.sshkey,
            image=self.data['osImage'],
            disksize=self.data['bootDiskSize'],
            datadisks=self.data['disks'],
            sizeId=self.data['sizeId'],
            )
        return self._machine

    def portforward_create(self, portforwards={}):
        """ Add portforwards """

        machine = self.machine
        machine_ip, _ = machine.machineip_get()

        space = self.space
        vdc = self.vdc
        task = vdc.schedule_action(
            'portforward_create', 
            {'machineId':machine.id, 
            'port_forwards':portforwards, 
            'protocol':'tcp'})
        task.wait()

    def portforward_delete(self, portforwards={}):
        """ Delete portforwards """

        machine = self.machine
        machine_ip, _ = machine.machineip_get()

        space = self.space
        vdc = self.vdc
        task = vdc.schedule_action(
            'portforward_delete', 
            {'machineId':machine.id, 
            'port_forwards':self.data['ports'], 
            'protocol':'tcp'})
        task.wait()        
 

    def start(self):
        """ Start the VM """

        machine = self.machine
        if machine:
            machine.start()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def stop(self):
        """ Stop the VM """

        machine = self.machine
        if machine:
            machine.stop()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def restart(self):
        """ Restart the VM """

        machine = self.machine
        if machine:
            machine.restart()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def pause(self):
        """ Pause the VM """

        machine = self.machine
        if machine:
            machine.pause()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def resume(self):
        """ Resume the VM """

        machine = self.machine
        if machine:
            machine.resume()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def reset(self):
        """ Reset the VM """

        machine = self.machine
        if machine:
            machine.reset()    
        else:
            raise RuntimeError('machine %s in not found' % self.name)      

    def snapshot(self):
        """
        Action that creates a snapshot of the machine
        """
        machine = self.machine
        if machine:
            machine.snapshot_create()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def snapshot_rollback(self, snapshot_epoch=None):
        """
        Action that rolls back the machine to a snapshot
        """    
        if not snapshot_epoch:
            raise RuntimeError('"snapshot_epoch" should be given')

        machine = self.machine
        if machine:       
            machine.snapshot_rollback(snapshot_epoch)
            machine.start()
        else:
            raise RuntimeError('machine %s in not found' % self.name)

    def snapshot_delete(self,  snapshot_epoch=None):
        """
        Action that deletes a snapshot of the machine
        """
        if not snapshot_epoch:
            raise RuntimeError('"snapshot_epoch" should be given')

        machine = self.machine
        if machine and snapshot_epoch:       
            machine.snapshot_delete(snapshot_epoch)
        else:
            raise RuntimeError('machine %s in not found' % self.name)        

    def list_snapshots(self):
        """
        Action that lists snapshots of the machine
        """
        machine = self.machine
        if not machine:
            raise RuntimeError('machine %s in not found' % self.name)      

        return machine.snapshots
    
    def clone(self, clone_name):
        """
        Action that creates a clone of a machine.
        """
        if not clone_name:
            raise RuntimeError('"clone_name" should be given')

        machine = self.machine
        if not machine:       
            raise RuntimeError('machine %s in not found' % self.name)

        machine.clone(clone_name)
        machine.start()