from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
import tempfile
import shutil
import os
import pytest

from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot import config, template_collection
from zerorobot.template_uid import TemplateUID
from zerorobot.template.state import StateCheckError



class TestNode(TestCase):

    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

        self.valid_data ={
            'vdc': 'vdcName', 
            'sshKey': 'keyName'
            }

        # define machine mock properties
        boot_disk = {'id':int, 'type':'B', 'sizeMax':10}
        data_disk = {'id':int, 'type':'D', 'sizeMax':10}
        data_disk_wrong_size = {'id':int, 'type':'D', 'sizeMax':11}
        boot_disk_wrong_size = {'id':int, 'type':'B', 'sizeMax':11}
        disks = mock.PropertyMock()
        disks.side_effect=[[boot_disk, data_disk], [boot_disk, data_disk],
                           [boot_disk], [boot_disk, data_disk],
                           [boot_disk_wrong_size, data_disk], 
                           [boot_disk, data_disk_wrong_size]]
        self.machine_mock = MagicMock(prefab=MagicMock(return_value=None),
                                 id=1)
        type(self.machine_mock).disks=disks

        space_mock = MagicMock(machine_get=MagicMock(return_value=self.machine_mock),
                                machines={'test':MagicMock(delete=MagicMock())})

        self.ovc_mock=MagicMock(space_get=MagicMock(return_value=space_mock))

    def tearDown(self):
        patch.stopall()

    def test_validate(self):
        """
        Test validate method
        """
        name = 'test'
        instance = self.type(name=name, guid=None, data=self.valid_data)

        @mock.patch.object(instance, 'api')
        def validate(instance, api):
            api.services.find.return_value = [None]
            instance.validate()

        validate(instance)
        instance.delete()

        # test missing sshkey service name
        invalid_data ={
            'vdc': 'vdcName',
            }

        instance = self.type(name=name, guid=None, data=invalid_data)
        with pytest.raises(ValueError,
                           message='sshKey name is required'):
            instance.validate()
        instance.delete()              

        # test missing sshkey service name
        invalid_data ={
            'sshKey': 'sshkeyName',
            }
        with pytest.raises(ValueError,
                           message='vdc name is required'):
            instance.validate()
        instance.delete()

    def test_config(self):
        '''
        Test fetching config from vdc, account, and ovc services
        '''
        instance = self.type(name='test', data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = [[], [None,None]]
            # test when no vdc service is found
            with pytest.raises(RuntimeError,
                               message='found 0 vdcs with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

            # test when more than 1 vdc service is found
            with pytest.raises(RuntimeError,
                               message='found 2 vdcs with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

            # test when no account service is found
            account_name = 'test_account'
            task_mock = MagicMock(result=account_name)
            mock_find_ovc = MagicMock(schedule_action=MagicMock(return_value=task_mock))            
            api.services.find.side_effect = [ [mock_find_ovc], []]
            with pytest.raises(RuntimeError,
                               message='found 0 accounts with name "%s", required exactly one' % account_name):
                instance.config

            # test when more than 1 account service is found
            api.services.find.side_effect = [ [mock_find_ovc], [None, None]]
            with pytest.raises(RuntimeError,
                               message='found 2 accounts with name "%s", required exactly one' % account_name):
                instance.config

            # test success
            ovc_name = 'test_ovc'
            task_mock = MagicMock(result=ovc_name)
            mock_find_acc = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            api.services.find.side_effect = [ [mock_find_ovc], [mock_find_acc]]
            instance.config

            self.assertEqual(instance.config['ovc'], ovc_name)
            self.assertEqual(instance.config['account'], account_name)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, ovc):
        """
        Test install VM
        """
        # if installed, do nothing
        name = 'test'
        instance = self.type(name=name, data=self.valid_data)
        instance.state.set('actions', 'install', 'ok')
        instance.install()
        ovc.get.return_value.space_get.return_value.machine_create.assert_not_called()

        # test installing vm
        instance.state.delete('actions', 'install')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            ovc.get.return_value = self.ovc_mock

            # test when device is mounted
            instance.state.delete('actions', 'install')
            ovc.get.return_value.space_get.return_value.\
                                 machine_get.return_value. \
                                 prefab.core.run.return_value = (None, '/dev/vdb on /var type ext4 ', None)
            instance.install()
            ovc.get.return_value.space_get.return_value. \
                                 machine_get.return_value.\
                                 prefab.system.filesystem.create.assert_not_called()            

            # check call to get/create machine
            ovc.get.return_value.space_get.return_value.machine_get.assert_called_once_with(
                create=True,
                name=name,
                sshkeyname=self.valid_data['sshKey'],
                sizeId=1,
                managed_private=False,
                datadisks=[10],
                disksize=10,
                image='Ubuntu 16.04'
            )

            # test when device is not mounted and disk is not present
            ovc.get.return_value.space_get.return_value.\
                                 machine_get.return_value. \
                                 prefab.core.run.return_value = (None, 'test when not mounted', None)
            instance.state.delete('actions', 'install')

            instance.install()
            # check call to add disk
            instance.machine.disk_add.assert_called_once_with(
                name='Disk nr 1', description='Machine disk of type D',
                size=10, type='D')

            # check call to create a filesystem
            ovc.get.return_value.space_get.return_value. \
                                 machine_get.return_value.\
                                 prefab.system.filesystem.create.assert_called_once_with(
                                    fs_type='ext4', device='/dev/vdb'
                                 )

            # state install must be ok 
            instance.state.check('actions', 'install', 'ok')

            del instance

        # test fail when data disk size is not correct
        instance = self.type(name=name, data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            
            # boot disk has wrong size 
            with pytest.raises(RuntimeError,
                              message='Datadisk is expected to have size 10, has size 11'):
                instance.install()

        # test fail when boot disk size is not correct
        instance = self.type(name=name, data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            
            # boot disk has wrong size 
            with pytest.raises(RuntimeError,
                              message='Bootdisk is expected to have size 10, has size 11'):
                instance.install()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, ovc):
        """
        Test uninstall VM
        """
        
        instance = self.type(name='test', data=self.valid_data)

        # test success
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]

            # test uninstall
            ovc.get.return_value = self.ovc_mock

            instance.uninstall()
            ovc.get.return_value.space_get.return_value. \
                                 machine_get.return_value.\
                                 delete.assert_called_once_with()

        # state install must be unset
        with pytest.raises(StateCheckError,
                           message='check for state actions:install:ok failed'):
            instance.state.check('actions', 'install', 'ok')

    def test_start(self):
        '''
        Test start action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.start()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.start()
        instance.machine.start.assert_called_once_with()


    def test_stop(self):
        '''
        Test stop action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.stop()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.stop()
        instance.machine.stop.assert_called_once_with()

    def test_restart(self):
        '''
        Test restart action
        '''
        instance = self.type(name='test', data=self.valid_data)

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.restart()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.restart()
        instance.machine.restart.assert_called_once_with()

    def test_pause(self):
        '''
        Test pause action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.pause()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.pause()
        instance.machine.pause.assert_called_once_with()

    def test_resume(self):
        '''
        Test resume action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.resume()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.resume()
        instance.machine.resume.assert_called_once_with()

    def test_reset(self):
        '''
        Test reset action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.reset()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.reset()
        instance.machine.reset.assert_called_once_with()

    def test_snapshot(self):
        '''
        Test snapshot action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot()
        instance.machine.snapshot_create.assert_called_once_with()  

    def test_clone(self):
        '''
        Test clone action
        '''
        instance = self.type(name='test', data=self.valid_data)  
        clone_name = 'test_clone'

        # test call without arguments
        with pytest.raises(TypeError,
                           message="clone() missing 1 required positional argument: 'clone_name'"):
            instance.clone()

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.clone(clone_name)
        instance.machine.clone.assert_called_once_with(clone_name)

    def test_snapshot_rollback(self):
        '''
        Test snapshot_rollback action
        '''
        instance = self.type(name='test', data=self.valid_data)  
        snapshot_epoch = 'test_epoch'

        # test call without arguments
        with pytest.raises(TypeError,
                           message="snapshot_rollback() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_rollback()


        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_rollback(snapshot_epoch)
        instance.machine.snapshot_rollback.assert_called_once_with(snapshot_epoch)            

    def test_snapshot_delete(self):
        '''
        Test snapshot delete action
        '''
        instance = self.type(name='test', data=self.valid_data)  
        snapshot_epoch = 'test_epoch'

        # test call without arguments
        with pytest.raises(TypeError,
                           message="snapshot_delete() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_delete()


        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_delete(snapshot_epoch)
        instance.machine.snapshot_delete.assert_called_once_with(snapshot_epoch) 

    @mock.patch.object(j.clients, '_openvcloud')
    def test_portforward_create(self, ovc):
        '''
        Test creating portforward
        '''
        instance = self.type(name='test', data=self.valid_data)
        ports = {'source':22, 'destination':22}
        
        # test call without arguments
        with pytest.raises(TypeError,
                           message="portforward_create() missing 1 required positional argument: 'ports'"):
            instance.portforward_create()
        

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.portforward_create(ports)
        
        # success
        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            instance._machine = self.machine_mock
            test_machine_id = 1
            instance.machine.id = test_machine_id

            instance.portforward_create(ports)
            instance.vdc.schedule_action.assert_called_with(
                'portforward_create', 
                {'machineId': test_machine_id, 
                'port_forwards': ports, 
                'protocol': 'tcp'}
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_portforward_delete(self, ovc):
        '''
        Test deleting portforward
        '''
        instance = self.type(name='test', data=self.valid_data)
        ports = {'source':22, 'destination':22}
        
        # test call without arguments
        with pytest.raises(TypeError,
                           message="portforward_create() missing 1 required positional argument: 'ports'"):
            instance.portforward_delete()

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.portforward_delete(ports)
        
        # success
        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            instance._machine = self.machine_mock
            test_machine_id = 1
            instance.portforward_delete(ports)
            instance.vdc.schedule_action.assert_called_with(
                'portforward_delete', 
                {'machineId': test_machine_id,
                'port_forwards': ports, 
                'protocol': 'tcp'}
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_add(self, ovc):
        '''
        Test add disk
        '''
        instance = self.type(name='test', data=self.valid_data)
        
        # test call without arguments
        with pytest.raises(TypeError,
                           message="portforward_create() missing 1 required positional argument: 'ports'"):
            instance.portforward_delete()

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.disk_add()
        
        # success
        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            instance._machine = self.machine_mock
            instance.disk_add()
            instance.machine.disk_add.assert_called_with(
                name='Data disk', description=None, size=10, type='D'
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_attach(self, ovc):
        '''
        Test attach disk
        '''
        instance = self.type(name='test', data=self.valid_data)
        
        # test call without arguments
        with pytest.raises(TypeError,
                           message="disk_attach() missing 1 required positional argument: 'disk_service_name'"):
            instance.portforward_delete()

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.disk_attach(disk_service_name=str)
        
        # success
        instance.state.set('actions', 'install', 'ok')
        disk_id = 1
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock(return_value=MagicMock(result=disk_id)))]
            instance._machine = self.machine_mock
            instance.disk_attach(disk_service_name='test')
            instance.machine.disk_attach.assert_called_with(disk_id)

        # fail if disk service is not running
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            with pytest.raises(RuntimeError):
                instance.disk_attach(disk_service_name='test')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_detach(self, ovc):
        '''
        Test detach disk
        '''
        instance = self.type(name='test', data=self.valid_data)
        
        # test call without arguments
        with pytest.raises(TypeError,
                           message="disk_detach() missing 1 required positional argument: 'disk_service_name'"):
            instance.portforward_delete()

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.disk_detach(disk_service_name=str)
        
        # success
        instance.state.set('actions', 'install', 'ok')
        disk_id = 1
        disk_service_name = 'test_disk'
        with patch.object(instance, 'api') as api:
            service_mock = MagicMock(name=disk_service_name, schedule_action=MagicMock(
                return_value=MagicMock(result=disk_id)))
#            api.services.find.return_value = [service_mock]
            instance._machine = self.machine_mock
            # import ipdb; ipdb.set_trace()
            instance.data['disks'] = [service_mock]
            instance.disk_detach(disk_service_name=disk_service_name)
            instance.machine.disk_detach.assert_called_with(disk_id)

        # fail if disk service is not running
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            with pytest.raises(RuntimeError):
                instance.disk_detach(disk_service_name=disk_service_name)                 