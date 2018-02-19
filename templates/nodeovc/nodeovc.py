from js9 import j
from zerorobot.template.base import TemplateBase

class Nodeovc(TemplateBase):

    version = '0.0.1'
    template_name = "nodeovc"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self.data['name'] = name
        self._ovc = None
        self._machine = None

    def validate(self):
        # Get object for an OVC service, make sure exactly one is running
        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=self.data.get('openvcloud', None))
        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['openvcloud'] = ovcs[0].name
        
        # ensure uploaded key
        self.sshkey

    def update_data(self, data):
        # merge the new data
        self.data.update(data)
        
        self.save()

    @property
    def sshkey(self):
        """ Get a path and keyname of the sshkey service """
        sshkeys = self.api.services.find(template_uid=self.SSH_TEMPLATE)
        if len(sshkeys) != 1:
            raise RuntimeError('found %s ssh services, requires exactly 1' % len(sshkeys))

        # Get key name and path
        path = sshkeys[0].data['path']
        key = path.split('/')[-1]

        return key         

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        self._ovc = j.clients.openvcloud.get(self.data['openvcloud'])
        return self._ovc

    @property
    def space(self):
        return self.ovc.space_get(accountName=None,
                                 spaceName=self.data['openvcloud'])

    @property
    def machine(self):
        if self._machine:
            return self._machine
        return self.space.machines.get(self.data['name'])

    def install(self):
        machine = self.machine
        if not machine:
            machine = self._machine_create()
        # else:
        #     machine.configure_machine(machine, machine.name, self.sshkey)
        self._configure_ports()

        # Get data from the vm
        ip_private, vm_info = machine.machineip_get()
        self.data['sshLogin'] = vm_info['accounts'][0]['login']
        self.data['sshPassword']= vm_info['accounts'][0]['password']
        self.data['ipPrivate'] = ip_private
        self.data['ipPublic'] = machine.space.model['publicipaddress']
        self.data['machineId'] = machine.id

#        self._ssh_authorize_root()

        self.state.set('actions', 'install', 'ok')
        self.save()

    def uninstall(self):
        # check if the machine is in the space
        if self.machine:
            self.machine.delete()

        self.state.set('actions', 'uninstall', 'ok')

    def _machine_create(self):
        self._machine =  self.space.machine_create(
            name=self.data['name'],
            sshkeyname= self.sshkey,
            image=self.data['osImage'],
            disksize=self.data['bootDiskSize'],
            datadisks=self.data['disks'],
            sizeId=self.data['sizeId'],
            )
        return self._machine

    def _configure_ports(self):
        """
        Configure portforwards
        """
        machine = self.machine
        port_forwards = self.data['ports']
        
        # get list of existing ports at the vm
        existent_ports = [port['publicPort'] for port in machine.portforwards]

        # list of requested ports
        requested_ports = [port['destination'] for port in port_forwards]

        # check if port 22 is already created or requested
        ssh_present = ('22' in existent_ports) or ('22' in requested_ports)

        # if port 22 is not created, add to requested
        if not ssh_present:
            ssh_port = {'source':'22', 'destination': '22'}
            port_forwards.append(ssh_port)

        for port in port_forwards:
            # check if ports do not exist yet
            if port['destination'] not in existent_ports:
                # create portforward
                machine.portforward_create(
                    publicport=port['destination'], 
                    localport=port['source'], 
                    protocol='tcp',
                    )

    def start(self):
        """ Start the VM """
        machine = self.machine
        if machine:
            machine.start()
        else:
            self.err_log_machine_not_found()

    def stop(self):
        """ Stop the VM """
        machine = self.machine
        if machine:
            machine.stop()
        else:
            self.err_log_machine_not_found()

    def restart(self):
        """ Restart the VM """
        machine = self.machine
        if machine:
            machine.restart()
        else:
            self.err_log_machine_not_found()

    def pause(self):
        """ Pause the VM """
        machine = self.machine
        if machine:
            machine.pause()
        else:
            self.err_log_machine_not_found()

    def resume(self):
        """ Resume the VM """
        machine = self.machine
        if machine:
            machine.resume()
        else:
            self.err_log_machine_not_found()

    def reset(self):
        """ Reset the VM """
        machine = self.machine
        if machine:
            machine.reset()    
        else:
            self.err_log_machine_not_found()      

    def snapshot(self):
        """
        Action that creates a snapshot of the machine
        """
        machine = self.machine
        if machine:
            machine.snapshot_create()
        else:
            self.err_log_machine_not_found()

    def snapshot_rollback(self, snapshot_epoch=None):
        """
        Action that rolls back the machine to a snapshot
        """    
        machine = self.machine
        if machine and snapshot_epoch:       
            machine.snapshot_rollback(snapshot_epoch)
            machine.start()
        else:
            self.err_log_machine_not_found()

    def snapshot_delete(self,  snapshot_epoch=None):
        """
        Action that deletes a snapshot of the machine
        """
        machine = self.machine
        if machine and snapshot_epoch:       
            machine.snapshot_delete(snapshot_epoch)
        else:
            self.err_log_machine_not_found()        

    def list_snapshots(self):
        """
        Action that deletes a snapshot of the machine
        """
        machine = self.machine
        if machine:       
            self.data['snapshots'] = machine.snapshots
            self.save()
        else:
            self.err_log_machine_not_found()      


    def err_log_machine_not_found(self):
            self.logger.error('machine %s in not created in the openvcloud %s'%(
                self.data['name'],
                self.data['openvcloud'])
                )
