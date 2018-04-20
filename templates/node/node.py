import re
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError
from zerorobot.template.decorator import retry


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
        """
        Validate service data received during creation
        """

        if not self.data['name']:
            raise ValueError('VM name is required')

        if not self.data['vdc']:
            raise ValueError('vdc service name is required')

        if not self.data['sshKey']:
            raise ValueError('sshKey service name is required')

    def _execute_task(self, proxy, action, args={}):
        task = proxy.schedule_action(action=action, args=args)
        task.wait()
        if task.state is not 'ok':
            raise RuntimeError(
                    'error occurred when executing action "%s" on service "%s"' %
                    (action, proxy.name))
        return task.result

    def get_info(self):
        """ Get VM info """
        self.state.check('actions', 'install', 'ok')
        return {
            'name' : self.data['name'],
            'id' : self.data['machineId'],
            'vdc' : self.data['vdc'],
            'disk_services' : self.data['disks']
        }

    def _get_proxy(self, template_uid, service_name):
        """
        Get proxy object of the service 

        :param service_name: name of the service
        """

        matches = self.api.services.find(template_uid=template_uid, name=service_name)
        if len(matches) != 1:
            raise RuntimeError('found %d services with name "%s", required exactly one' % (len(matches), service_name))
        return matches[0]

    @property
    def config(self):
        """
        returns an object with names of vdc, account, and ovc
        """
        if self._config is not None:
            return self._config
        
        config = {}
        # traverse the tree up words so we have all info we need to return, connection and

        # get vdc proxy
        vdc = self._get_proxy(self.VDC_TEMPLATE, self.data['vdc'])
        self._vdc = vdc

        # get vdc info
        vdc_info = self._execute_task(proxy=vdc, action='get_info')
        config['vdc'] = vdc_info['name']

        # get account name
        account = self._get_proxy(self.ACCOUNT_TEMPLATE, vdc_info['account'])
        account_info = self._execute_task(proxy=account, action='get_info')
        config['account'] = account_info['name']

        # get connection
        config['ovc'] = account_info['openvcloud']
        
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
        """ Vdc service instance """
        self.config
        return self._vdc

    @property
    def space(self):
        """ Return space object """

        account = self.config['account']
        vdc = self.config['vdc']

        return self.ovc.space_get(
            accountName=account,
            spaceName=vdc
        )

    @property
    def machine(self):
        """ Return VM object """

        if not self._machine:
            if self.data['name'] in self.space.machines:
                self._machine = self.space.machine_get(name=self.data['name'])

        return self._machine

    @retry((BaseException),
            tries=5, delay=3, backoff=2, logger=None)
    def install(self):
        """ Install VM """

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
        sshkey_info = self._execute_task(proxy=sshkey_proxy, action='get_info')
        sshkey = sshkey_info['name']

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

    def _create_disk_service(self, disk, service_name=None):
        # create a disk service
        if not service_name:
            service_name = 'Disk%s' % str(disk['id'])

        service = self.api.services.find_or_create(
            template_uid=self.DISK_TEMPLATE,
            service_name=service_name,
            data={'vdc': self.data['vdc'],
                  'diskId': disk['id'],
                  'type': disk['type'],
                  'node': self.name},
        )
        # update data in the disk service
        self._execute_task(proxy=service, action='install')

        # append service name to the list of attached disks
        if service_name not in self.data['disks']:
            self.data['disks'].append(service_name)

    def _get_prefab(self):
        """ Get prefab """

        if not self.data.get('managedPrivate', False):
            return self.machine.prefab

        return self.machine.prefab_private  

    def uninstall(self):
        """ 
        Uninstall VM
        """

        if self.machine:
            self.machine.delete()
        self.state.delete('actions', 'install')

        # delete services for disks attached to the vm
        while self.data['disks']:
            disk = self.data['disks'].pop()
            proxy = self._get_proxy(self.DISK_TEMPLATE, disk)
            proxy.delete()

        self._machine = None


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
        Create a snapshot of the VM
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
        Action that deletes a snapshot of the VM
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
        """ Create a clone of the VM """

        self.state.check('actions', 'install', 'ok')
        if not clone_name:
            raise RuntimeError('"clone_name" should be given')

        self.machine.clone(clone_name)

    def disk_attach(self, disk_service_name):
        """
        Attach disk to the VM

        :param disk_service_name: name of the disk service
        """

        self.state.check('actions', 'install', 'ok')

        # get diskId
        disk_proxy = self._get_proxy(self.DISK_TEMPLATE, disk_service_name)
        disk_info = self._execute_task(proxy=disk_proxy, action='get_info')
        disk_id = disk_info['diskId']

        # attach the disk
        self.machine.disk_attach(disk_id)

        # add service name to data
        self.data['disks'].append(disk_service_name)

    def disk_detach(self, disk_service_name):
        """
        Detach disk from the machine

        :param disk_service_name: name of the disk service
        """

        self.state.check('actions', 'install', 'ok')

        if disk_service_name not in self.data['disks']:
            return
        # get disk id and type

        disk_proxy = self._get_proxy(self.DISK_TEMPLATE, disk_service_name)
        
        # fetch disk info
        disk_info = self._execute_task(proxy=disk_proxy, action='get_info')
        disk_id = disk_info['diskId']
        disk_type = disk_info['diskType']

        if disk_type == 'B':
            raise RuntimeError("Can't detach Boot disk")
        
        # detach disk
        self.machine.disk_detach(disk_id)

        # delete disk from list of attached disks
        self.data['disks'].remove(disk_service_name)

    def disk_add(self, name, disk_service_name=None, description='Data disk', size=10, type='D'):
        """
        Create new disk at the VM
        """        
        self.state.check('actions', 'install', 'ok')

        disk_id = self.machine.disk_add(name=name, description=description, 
                                        size=size, type=type)
        disk = {'id': disk_id,
                'description': description,
                'name': name,
                'type': type,
                'size': size}
        self._create_disk_service(disk, service_name=disk_service_name)

    def disk_delete(self, disk_service_name):
        """
        Delete disk at the machine
        """
        
        self.state.check('actions', 'install', 'ok')

        if disk_service_name not in self.data['disks']:
            return

        # first detach disk
        self.disk_detach(disk_service_name=disk_service_name)

        # get disk service proxy
        proxy = self._get_proxy(self.DISK_TEMPLATE, disk_service_name)

        # uninstall detached disk
        # get diskId
        self._execute_task(proxy=proxy, action='uninstall')
