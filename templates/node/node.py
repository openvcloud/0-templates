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

    def update(self, **kwards):
        '''
        Update data on the service
        '''
        for key, value in kwards.items():
            if key in self.data.keys():
                if isinstance(value, type(self.data['key'])):
                    self.data['key'] = value
                else:
                    raise ValueError('argument "%s" is type %s, should be %s' 
                                     %(key, type(value), type(self.data['key'])))
            else:
                raise ValueError('argument "%s" is not supported')

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
        if not self._machine:
            self._machine = self.space.machines.get(self.name)
        return self._machine

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # if this vm already exists, delete the vm
        if self.machine:
            self.machine.delete()

        # get new machine
        machine = self._machine_create()

        # Get data from the vm
        self.data['sshLogin'] = machine.model['accounts'][0]['login']
        self.data['sshPassword'] = machine.model['accounts'][0]['password']
        self.data['ipPrivate'] = machine.ipaddr_priv
        self.data['ipPublic'] = machine.ipaddr_public
        self.data['machineId'] = machine.id

        self._configure_disks()
        self.state.set('actions', 'install', 'ok')

    def _machine_create(self):
        """ Create a new machine """
        data = self.data
        space = self.space
        self._machine = space.machine_create(
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
        machine = self.machine
        space_name = machine.space.model['name']
        if machine:
            machine.start()
        else:
            raise RuntimeError('machine %s is not found' % self.name)

        for disk in machine.disks:
            # create a disk service
            service = self.api.services.create(
                template_uid=self.DISK_TEMPLATE,
                service_name='Disk%s' % str(disk['id']),
                data={'vdc': space_name, 'diskId': disk['id']},
            )
            # update data in the disk service
            task = service.schedule_action('update_data', {'data': disk})
            task.wait()

        # set default values
        fs_type = 'ext4'
        mount_point = '/var'
        device = '/dev/vdb'

        # create file system and mount data disk
        if self.data.get('managedPrivate', False) is False:
            prefab = machine.prefab
        else:
            prefab = machine.prefab_private
        prefab.system.filesystem.create(fs_type=fs_type, device=device)
        prefab.system.filesystem.mount(mount_point=mount_point, device=device,
                                       copy=True, append_fstab=True, fs_type=fs_type)

        machine.restart()
        if self.data.get('managedPrivate', False) is False:
            prefab = machine.prefab
        else:
            prefab = machine.prefab_private
        prefab.executor.sshclient.connect()

        # update data
        self.data['dataDiskFilesystem'] = fs_type
        self.data['dataDiskMountpoint'] = mount_point

    def uninstall(self):
        """ Uninstall machine """

        self.state.check('actions', 'install', 'ok')

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