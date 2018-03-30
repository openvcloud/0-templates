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
        self._disk_services = {}

    def validate(self):
        if not self.data['vdc']:
            raise ValueError('vdc name is required')

        if not self.data['sshKey']:
            raise ValueError('sshKey name is required')

        matches = self.api.services.find(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        if len(matches) != 1:
            raise RuntimeError('found %d vdcs with name "%s"' % (len(matches), self.data['vdc']))

        matches = self.api.services.find(template_uid=self.SSH_TEMPLATE, name=self.data['sshKey'])
        if len(matches) != 1:
            raise RuntimeError('found %s ssh keys with name "%s"' % (len(matches), self.data['sshKey']))

    @property
    def config(self):
        '''
        returns an object with names of vdc, account, and ovc
        '''
        if self._config is not None:
            return self._config

        config = {
            'vdc': self.data['vdc'],
        }
        # traverse the tree up words so we have all info we need to return, connection and
        # account
        matches = self.api.services.find(template_uid=self.VDC_TEMPLATE, name=config['vdc'])
        if len(matches) != 1:
            raise RuntimeError('found %d vdcs with name "%s", required exactly one' % (len(matches), config['vdc']))

        vdc = matches[0]
        self._vdc = vdc
        task = vdc.schedule_action('get_account')
        task.wait()

        config['account'] = task.result

        matches = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=config['account'])
        if len(matches) != 1:
            raise RuntimeError('found %s accounts with name "%s", required exactly one' % (len(matches), config['account']))

        account = matches[0]
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
        space = self.space
        self._machine = space.machine_get(
            create = True,
            name=self.name,
            sshkeyname=data['sshKey'],
            image=data['osImage'],
            disksize=data['bootDiskSize'],
            datadisks=[data['dataDiskSize']],
            sizeId=data['sizeId'],
            managed_private=self.data.get('managedPrivate', False)
        )

        return self._machine

    def _configure_disks(self):
        """
        Configure one boot disk and one data disk when installing a machine.
        """
        # TODO: add ssh portforward if none
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
                                self.data['bootDiskSize'], boot_disk[0]['sizeMax'])
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
            service_name = 'Disk%s' % str(disk['id'])
            service = self.api.services.create(
                template_uid=self.DISK_TEMPLATE,
                service_name=service_name,
                data={'vdc': self.data['vdc'], 'diskId': disk['id']},
            )
            # update data in the disk service
            task = service.schedule_action('install')
            task.wait()

            # append service name to the list of attached disks
            self.data['disks'].append(service_name)
            self._disk_services[service_name] = service

        prefab = self._get_prefab()

        # check if device is already mounted
        _, mount_output, _ = prefab.core.run('mount')
        if mount_output.find(device) != -1:
            # check if filesystem on the device is correct
            _, disk_info, _ = prefab.core.run("blkid '/dev/vdb' -s TYPE")

            # check type of the filesystem           
            fs_found = re.search('TYPE="(.+?)"', disk_info).group(1)
            if fs_found != fs_type:
                raise RuntimeError('VM "{vm}" has volume mounted on {mp} with filesystem "{fs}", should be "{fs_type}"'.format(
                                    vm=self.name, mp=mount_point, fs=fs_found, fs_type=fs_type))
            # if filesystem is correct, install is complete
            return

        # create file system and mount data disk
        prefab.system.filesystem.create(fs_type=fs_type, device=device)
        prefab.system.filesystem.mount(mount_point=mount_point, device=device,
                                       copy=True, append_fstab=True, fs_type=fs_type)

        machine.restart()

        prefab = self._get_prefab()
        prefab.executor.sshclient.connect()


    def _get_prefab(self):
        '''
        Get prefab
        '''

        if self.data.get('managedPrivate', False) is False:
            return self.machine.prefab

        return self.machine.prefab_private  

    def uninstall(self):
        """ Uninstall machine """

        if self.name in self.space.machines:
            self.machine.delete()

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
        self._disk_services[disk_service_name] = proxy
        self.logger('data disk attached')

    def disk_detach(self, disk_service_name):
        '''
        Detach disk from the machine
        @disk_service_name is the name of the disk service
        '''
        self.state.check('actions', 'install', 'ok')

        if disk_service_name not in self.data['disks']:
            return

        # get disk id and type
        proxy = self._disk_services.get(disk_service_name)
        task = proxy.schedule_action(action='get_type')
        disk_type = task.result

        if disk_type == 'B':
            raise RuntimeError("Can't detach Boot disk")

        task = proxy.schedule_action(action='get_id')
        task.wait()
        disk_id = task.result

        # detach disk
        self.machine.disk_detach(disk_id)
        import ipdb; ipdb.set_trace()
        # delete disk from list of attached disks
        self.data['disks'].remove(disk_service_name)
        del self._disk_services[disk_service_name]
        self.logger('data disk detached')