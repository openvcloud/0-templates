import re
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'

    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
    DISK_TEMPLATE = 'github.com/openvcloud/0-templates/disk/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._config = None
        self._ovc = None
        self._vdc = None
        self._machine = None

    def validate(self):
        '''
        Validate service data received during creation
        '''

        if not self.data['name']:
            raise ValueError('VM name is required')

        if not self.data['vdc']:
            raise ValueError('vdc service name is required')

        if not self.data['sshKey']:
            raise ValueError('sshKey service name is required')

    def get_name(self):
        '''
        Return name of the VM
        '''

        return self.data['name']

    def get_disk_services(self):
        '''
        Return service names of the disks attached to the VM
        '''        
        
        return self.data['disks']

    def get_space(self):
        '''
        Return vdc service name
        '''           
        return self.data['vdc']

    def _get_proxy(self, template_uid, service_name):
        '''
        Get proxy object of the service with name @service_name
        '''

        matches = self.api.services.find(template_uid=template_uid, name=service_name)
        if len(matches) != 1:
            raise RuntimeError('found %d services with name "%s", required exactly one' % (len(matches), service_name))
        return matches[0]

    @property
    def config(self):
        '''
        returns an object with names of vdc, account, and ovc
        '''
        if self._config is not None:
            return self._config

        config = {}
        # traverse the tree up words so we have all info we need to return, connection and

        # get vdc proxy
        vdc = self._get_proxy(self.VDC_TEMPLATE, self.data['vdc'])
        self._vdc = vdc

        # get vdc name
        task = vdc.schedule_action('get_name')
        task.wait()
        config['vdc'] = task.result

        # get account service name
        task = vdc.schedule_action('get_account')
        task.wait()
        account_service = task.result


        # get account name
        account = self._get_proxy(self.ACCOUNT_TEMPLATE, account_service)
        task = account.schedule_action('get_name')
        task.wait()
        config['account'] = task.result

        # get connection
        task = account.schedule_action('get_openvcloud')
        task.wait()
        config['ovc'] = task.result
        
        self._config = config
        return self._config

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        self._ovc = j.clients.openvcloud.get(instance=self.config['ovc'])

        return self._ovc

    @property
    def vdc(self):
        '''
        vdc service instance
        '''
        self.config
        return self._vdc

    @property
    def space(self):
        account = self.config['account']
        vdc = self.config['vdc']

        return self.ovc.space_get(
            accountName=account,
            spaceName=vdc
        )

    @property
    def machine(self):
        '''
        Return VM object
        '''

        if not self._machine:
            if self.data['name'] in self.space.machines:
                self._machine = self.space.machine_get(name=self.data['name'])

        return self._machine

    def install(self):
        '''
        Install VM
        '''
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # get new vm
        machine = self._machine_create()

        # Get data from the vm
        self.data['sshLogin'] = machine.model['accounts'][0]['login']
        self.data['sshPassword'] = machine.model['accounts'][0]['password']
        self.data['ipPrivate'] = machine.ipaddr_priv
        self.data['ipPublic'] = machine.ipaddr_public
        self.data['machineId'] = machine.id

        # configure disks of the vm
        self._configure_disks()
        self.state.set('actions', 'install', 'ok')

    def _machine_create(self):
        """ 
        Create a new machine
        """
        data = self.data

        # get name of sshkey       
        sshkey_proxy = self._get_proxy(self.SSH_TEMPLATE, self.data['sshKey'])
        task = sshkey_proxy.schedule_action('get_name')
        task.wait()
        sshkey = task.result

        self._machine = self.space.machine_get(
            create = True,
            name=data['name'],
            sshkeyname=sshkey,
            image=data['osImage'],
            disksize=data['bootDiskSize'],
            datadisks=[data['dataDiskSize']],
            sizeId=data['sizeId'],
            managed_private=data.get('managedPrivate', False)
        )

        return self._machine

    def _configure_disks(self):
        """
        Configure one boot disk and one data disk when installing a machine.
        """
        machine = self.machine

        # set defaults for datadisk
        fs_type = 'ext4'
        mount_point = '/var'
        device = '/dev/vdb'
        # update data
        self.data['dataDiskFilesystem'] = fs_type
        self.data['dataDiskMountpoint'] = mount_point
        
        # make sure machine is started
        machine.start()
        # get disks from the vm
        disks = machine.disks

        # check that bootdisk has correct size
        boot_disk = [disk for disk in disks if disk['type'] == 'B'][0]
        if boot_disk['sizeMax'] != self.data['bootDiskSize']:
            raise RuntimeError('Datadisk is expected to have size {}, has size {}'.format(
                                self.data['bootDiskSize'], boot_disk['sizeMax'])
                              )

        # identify data disks
        data_disks = [disk for disk in disks if disk['type'] == 'D']
        if len(data_disks) > 1:
            raise RuntimeError('Exactly one data disk is expected, VM "{vm}" has {nr} data disks'.format(
                                vm=machine.name, nr=len(data_disks))
                                )
        elif len(data_disks) == 1:
            # check that datadisk has correct size
            if data_disks[0]['sizeMax'] != self.data['dataDiskSize']:
                raise RuntimeError('Datadisk is expected to have size {}, has size {}'.format(
                                    self.data['dataDiskSize'], data_disks[0]['sizeMax'])
                                )
        else:
            # if no datadisks, create one
            machine.disk_add(name='Disk nr 1', description='Machine disk of type D',
                             size=self.data['dataDiskSize'], type='D')

        for disk in machine.disks:
            # create a disk service
            self._create_disk_service(disk)

        prefab = self._get_prefab()

        # check if device is already mounted
        _, disk_info, _ = prefab.core.run('mount')
        if disk_info.find(device) != -1:
            # check if mount point is correct
            mp_found = re.search('%s on (.+?) ' % device, disk_info)

            if mp_found == None or mp_found.group(1) != mount_point:
                raise RuntimeError('mount point of device "{device}" is "{mp_found}", expected "{mp}"'.format(
                    device=device, mp_found=mp_found, mp=mount_point
                ))

            # check type of the filesystem           
            fs_found = re.search('%s on %s type (.+?) ' % (device, mount_point), disk_info)
            if fs_found == None or fs_found.group(1) != fs_type:
                raise RuntimeError('VM "{vm}" has volume mounted on {mp} with filesystem "{fs}", should be "{fs_type}"'.format(
                                    vm=self.data['name'], mp=mount_point, fs=fs_found, fs_type=fs_type))
            # if filesystem is correct, install is complete
            return

        # create file system and mount data disk
        prefab.system.filesystem.create(fs_type=fs_type, device=device)
        prefab.system.filesystem.mount(mount_point=mount_point, device=device,
                                       copy=True, append_fstab=True, fs_type=fs_type)

        machine.restart()

        prefab = self._get_prefab()
        prefab.executor.sshclient.connect()

    def _create_disk_service(self, disk):
        # create a disk service
        service_name = 'Disk%s' % str(disk['id'])
        service = self.api.services.create(
            template_uid=self.DISK_TEMPLATE,
            service_name=service_name,
            data={'vdc': self.data['vdc'], 'diskId': disk['id'], 'type': disk['type']},
        )
        # update data in the disk service
        task = service.schedule_action('install')
        task.wait()

        # append service name to the list of attached disks
        self.data['disks'].append(service_name)

    def _get_prefab(self):
        '''
        Get prefab
        '''

        if self.data.get('managedPrivate', False) is False:
            return self.machine.prefab

        return self.machine.prefab_private  

    def uninstall(self):
        ''' 
        Uninstall VM
        '''

        if self.machine:
            self.machine.delete()

        # uninstall services for disks attached to the vm
        for disk in self.data['disks']:
            proxy = self._get_proxy(self.DISK_TEMPLATE, disk)
            proxy.schedule_action('uninstall')

        self._machine = None

        self.state.delete('actions', 'install')

    def portforward_create(self, ports):
        """ Add portforwards """

        self.state.check('actions', 'install', 'ok')

        # get vdc service
        self.vdc.schedule_action(
            'portforward_create',
            {
                'machineId': self.machine.id,
                'port_forwards': ports,
                'protocol': 'tcp'
            }
        )

    def portforward_delete(self, ports):
        """ Delete portforwards """
        
        self.state.check('actions', 'install', 'ok')

        if self.data['managedPrivate']:
            return

        self.vdc.schedule_action(
            'portforward_delete',
            {
                'machineId': self.machine.id,
                'port_forwards': ports,
                'protocol': 'tcp'
            }
        )

    def start(self):
        """ Start the VM """

        self.state.check('actions', 'install', 'ok')
        self.machine.start()

    def stop(self):
        """ Stop the VM """

        self.state.check('actions', 'install', 'ok')
        self.machine.stop()

    def restart(self):
        """ Restart the VM """

        self.state.check('actions', 'install', 'ok')
        self.machine.restart()

    def pause(self):
        """ Pause the VM """

        self.state.check('actions', 'install', 'ok')
        self.machine.pause()

    def resume(self):
        """ Resume the VM """

        self.state.check('actions', 'install', 'ok')
        self.machine.resume()

    def reset(self):
        """ Reset the VM """

        self.state.check('actions', 'install', 'ok')
        self.machine.reset()

    def snapshot(self):
        """
        Action that creates a snapshot of the machine
        """
        self.state.check('actions', 'install', 'ok')
        self.machine.snapshot_create()

    def snapshot_rollback(self, snapshot_epoch):
        """
        Action that rolls back the machine to a snapshot
        """
        self.state.check('actions', 'install', 'ok')
        if not snapshot_epoch:
            raise RuntimeError('"snapshot_epoch" should be given')

        self.machine.snapshot_rollback(snapshot_epoch)
        self.machine.start()

    def snapshot_delete(self, snapshot_epoch):
        """
        Action that deletes a snapshot of the machine
        """
        self.state.check('actions', 'install', 'ok')
        if not snapshot_epoch:
            raise RuntimeError('"snapshot_epoch" should be given')

        self.machine.snapshot_delete(snapshot_epoch)

    def list_snapshots(self):
        """
        Action that lists snapshots of the machine
        """
        self.state.check('actions', 'install', 'ok')
        return self.machine.snapshots

    def clone(self, clone_name):
        """
        Action that creates a clone of a machine.
        """
        self.state.check('actions', 'install', 'ok')

        if not clone_name:
            raise RuntimeError('"clone_name" should be given')

        self.machine.clone(clone_name)

    def disk_attach(self, disk_service_name):
        '''
        Attach disk to the machine
        @disk_service_name is the name of the disk service
        '''        
        self.state.check('actions', 'install', 'ok')

        matches = self.api.services.find(template_uid=self.DISK_TEMPLATE, name=disk_service_name)
        if len(matches) != 1:
            raise RuntimeError('found %s services of type "%s", expected exactly one' % (len(matches), disk_service_name))

        proxy = matches[0]
        # get diskId
        task = proxy.schedule_action(action='get_id')
        task.wait()
        disk_id = task.result

        # attach the disk
        self.machine.disk_attach(disk_id)

        # add service name to data
        self.data['disks'].append(disk_service_name)

    def disk_detach(self, disk_service_name):
        '''
        Detach disk from the machine
        @disk_service_name is the name of the disk service
        '''
        self.state.check('actions', 'install', 'ok')

        if disk_service_name not in self.data['disks']:
            return
        # get disk id and type

        proxy = self._get_proxy(self.DISK_TEMPLATE, disk_service_name)

        task = proxy.schedule_action(action='get_type')
        disk_type = task.result

        if disk_type == 'B':
            raise RuntimeError("Can't detach Boot disk")

        task = proxy.schedule_action(action='get_id')
        task.wait()
        disk_id = task.result

        # detach disk
        self.machine.disk_detach(disk_id)

        # delete disk from list of attached disks
        self.data['disks'].remove(disk_service_name)

    def disk_add(self, name, description='Data disk', size=10, type='D'):
        '''
        Create new disk at the VM
        '''        
        self.state.check('actions', 'install', 'ok')

        disk_id = self.machine.disk_add(name=name, description=description, 
                                        size=size, type=type)
        disk = {'id': disk_id,
                'description': description,
                'name': name,
                'type': type,
                'size': size}
        self._create_disk_service(disk)

    def disk_delete(self, disk_service_name):
        '''
        Delete disk at the machine
        '''        
        self.state.check('actions', 'install', 'ok')

        # find service in the list of services
        proxy = self._get_proxy(self.DISK_TEMPLATE, disk_service_name)

        task = proxy.schedule_action('uninstall')
        task.wait()
        self.data['disks'].remove(disk_service_name)

