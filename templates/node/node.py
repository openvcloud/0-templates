from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError

class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
    DISK_TEMPLATE = 'github.com/openvcloud/0-templates/disk/0.0.1'

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
        
        instance = self.vdc.ovc.instance
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
        if len(sshkeys) == 0:
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
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass        

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

        self.portforward_create(self.data.get('ports', None))
        self._configure_disks()
        self.save()

        self.state.set('actions', 'install', 'ok')

    def _machine_create(self):
        """ Create a new machine """
        data = self.data
        space = self.space
        self._machine = space.machine_create(
            name=self.name,
            sshkeyname= self.sshkey,
            image=data['osImage'],
            disksize=data['bootDiskSize'],
            datadisks=[data['dataDiskSize']],
            sizeId=data['sizeId'],
            )

        return self._machine

    def _configure_disks(self):
        """
        Configure one boot disk and one data disk when installing a machine.
        """
        machine = self.machine
        space_name = machine.space.model['name']
        if machine:
            machine.start()
        else:
            raise RuntimeError('machine %s in not found' % self.name)        

        for disk in machine.disks:
            # create a disk service
            service = self.api.services.create(
                template_uid=self.DISK_TEMPLATE, 
                service_name= 'Disk%s' % str(disk['id']),
                data={'vdc' : space_name},
            )
            # update data in the disk service
            task = service.schedule_action('update_data', {'data':disk})
            task.wait()

        # set default values
        fs_type = 'ext4'
        mount_point = '/var'
        device = '/dev/vdb'
        
        # create file system and mount data disk
        prefab = machine.prefab
        prefab.system.filesystem.create(fs_type=fs_type, device=device)
        prefab.system.filesystem.mount(mount_point=mount_point, device=device, 
                                       reboot=True, copy=True, 
                                       fs_type=fs_type)

        # update data
        self.data['dataDiskFilesystem'] = fs_type
        self.data['dataDiskMountpoint'] = mount_point
        self.save()

    def uninstall(self):
        """ Uninstall machine """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)
        self.machine.delete()

    def portforward_create(self, ports):
        """ Add portforwards """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        # get vdc service
        self.vdc.schedule_action('portforward_create', 
                                {'machineId':self.machine.id, 'port_forwards':ports, 'protocol':'tcp'})

    def portforward_delete(self, ports):
        """ Delete portforwards """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.vdc.schedule_action('portforward_delete', 
                                {'machineId':self.machine.id, 'port_forwards':ports, 'protocol':'tcp'})

    def start(self):
        """ Start the VM """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)
            
        self.machine.start()
    
    def stop(self):
        """ Stop the VM """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.machine.stop()

    def restart(self):
        """ Restart the VM """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.machine.restart()

    def pause(self):
        """ Pause the VM """

        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.machine.pause()

    def resume(self):
        """ Resume the VM """

        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.machine.resume()

    def reset(self):
        """ Reset the VM """

        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.machine.reset()    

    def snapshot(self):
        """
        Action that creates a snapshot of the machine
        """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.machine.snapshot_create()

    def snapshot_rollback(self, snapshot_epoch):
        """
        Action that rolls back the machine to a snapshot
        """    
        if not snapshot_epoch:
            raise RuntimeError('"snapshot_epoch" should be given')

        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        self.machine.snapshot_rollback(snapshot_epoch)
        self.machine.start()

    def snapshot_delete(self,  snapshot_epoch):
        """
        Action that deletes a snapshot of the machine
        """
        if not snapshot_epoch:
            raise RuntimeError('"snapshot_epoch" should be given')

        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)       

        self.machine.snapshot_delete(snapshot_epoch)

    def list_snapshots(self):
        """
        Action that lists snapshots of the machine
        """
        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)

        return self.machine.snapshots
    
    def clone(self, clone_name):
        """
        Action that creates a clone of a machine.
        """
        if not clone_name:
            raise RuntimeError('"clone_name" should be given')

        if not self.machine:
            raise RuntimeError('machine %s in not found' % self.name)     

        self.machine.clone(clone_name)
        self.machine.start()