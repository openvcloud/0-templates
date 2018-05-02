import re
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError
from zerorobot.template.decorator import retry


class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
    DISK_TEMPLATE = 'github.com/openvcloud/0-templates/disk/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._config = None
        self._ovc = None
        self._space = None
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

    def get_info(self):
        """ Get VM info """
        self.state.check('actions', 'install', 'ok')
        return {
            'name': self.data['name'],
            'id': self.data['machineId'],
            'vdc': self.data['vdc'],
            'disk_services': self.data['disks']
        }

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
        proxy = self.api.services.get(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])

        # get vdc info
        vdc_info = proxy.schedule_action(action='get_info').wait().result
        config['vdc'] = vdc_info['name']

        # get account name
        proxy = self.api.services.get(template_uid=self.ACCOUNT_TEMPLATE,  name=vdc_info['account'])
        account_info = proxy.schedule_action(action='get_info').wait().result
        config['account'] = account_info['name']

        # get connection instance name
        proxy = self.api.services.get(
            template_uid=self.OVC_TEMPLATE, name=account_info['openvcloud'])
        ovc_info = proxy.schedule_action(action='get_info').wait().result
        config['ovc'] = ovc_info['name']

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
    def space(self):
        """ Return space object """
        if not self._space:
            account = self.config['account']
            vdc = self.config['vdc']
            self._space = self.ovc.space_get(
                accountName=account,
                spaceName=vdc
            )
        return self._space

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
        proxy = self.api.services.get(
            template_uid=self.SSH_TEMPLATE, name=self.data['sshKey'])
        sshkey_info = proxy.schedule_action(action='get_info').wait().result

        self._machine = self.space.machine_create(
            name=data['name'],
            sshkeyname=sshkey_info['name'],
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
            raise RuntimeError('Bootdisk is expected to have size {}, has size {}'.format(
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
            fs_found = re.search('%s on %s type (.+?) ' %
                                 (device, mount_point), disk_info)
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
        """ Create a disk service

            :param disk: dict of data
            service_name: name of the disk service
        """
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
        service.schedule_action(action='install').wait()

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
            proxy = self.api.services.get(template_uid=self.DISK_TEMPLATE, name=disk)
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
        proxy = self.api.services.get(
            template_uid=self.DISK_TEMPLATE, name=disk_service_name)
        disk_info = proxy.schedule_action(action='get_info').wait().result

        # attach the disk
        self.machine.disk_attach(disk_info['diskId'])

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

        proxy = self.api.services.get(
            template_uid=self.DISK_TEMPLATE, name=disk_service_name)

        # fetch disk info
        disk_info = proxy.schedule_action(action='get_info').wait().result

        if disk_info['diskType'] == 'B':
            raise RuntimeError("Can't detach Boot disk")

        # detach disk
        self.machine.disk_detach(disk_info['diskId'])

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
        proxy = self.api.services.get(
            template_uid=self.DISK_TEMPLATE, name=disk_service_name)

        # uninstall detached disk
        proxy.schedule_action(action='uninstall').wait()
