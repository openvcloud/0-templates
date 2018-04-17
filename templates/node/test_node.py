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
            'name': 'nodeName',
            'vdc': 'vdcName', 
            'sshKey': 'keyName'
            }

    def tearDown(self):
        patch.stopall()

    def test_validate_success(self):
        """
        Test successfull validation
        """
        name = 'test'
        instance = self.type(name=name, guid=None, data=self.valid_data)

        @mock.patch.object(instance, 'api')
        def validate(instance, api):
            api.services.find.return_value = [None]
            instance.validate()
        
        data ={
            'vdc': 'vdcName',
            'sshKey': 'keyName',
            'name': 'nodeName',
        }

        instance = self.type(name=name, guid=None, data=data)
        try:
            instance.validate()
        except ValueError as err:
            pytest.fail("Validate should be successfull!\nGot error: %s" % err)

    def test_validate_fail(self):
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

        # test missing name
        invalid_data ={
            'vdc': 'vdcName',
            'sshKey': 'keyName'
            }

        instance = self.type(name=name, guid=None, data=invalid_data)
        with pytest.raises(ValueError,
                           message='VM name is required'):
            instance.validate()
        instance.delete()              

        # test missing sshkey service name
        invalid_data ={
            'name': 'nodeName',
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
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.valid_data)
        vdc_name = 'test_vdc'
        account_name = 'test_account'
        ovc_name = 'test_ovc' 

        with patch.object(instance, 'api') as api:
            result = mock.PropertyMock()
            result.side_effect = [account_name, ovc_name]
            task_mock = MagicMock()
            type(task_mock).result = result
            mock_find_acc = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            task_mock = MagicMock(result=vdc_name)
            mock_find_vdc = MagicMock(schedule_action=MagicMock(return_value=task_mock))

            api.services.find.side_effect = [[mock_find_vdc],[mock_find_acc]]
            instance.config
            self.assertEqual(instance.config['ovc'], ovc_name)
            self.assertEqual(instance.config['account'], account_name)

    def test_config_invalid_vdc(self):
        """
        Test getting config from a vdc service
        """
        instance = self.type(name='test', data=self.valid_data)
        vdc_name = 'test_vdc'

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

    def test_config_invalid_account(self):
        """
        Test getting config from a account service
        """
        instance = self.type(name='test', data=self.valid_data)
        vdc_name = 'test_vdc'
        account_name = 'test_account'

        with patch.object(instance, 'api') as api:
            # test when no account service is found
            task_mock = MagicMock(result=vdc_name)
            mock_find_vdc = MagicMock(schedule_action=MagicMock(return_value=task_mock))            
            api.services.find.side_effect = [ [mock_find_vdc], []]
            with pytest.raises(RuntimeError,
                               message='found 0 accounts with name "%s", required exactly one' % account_name):
                instance.config

            # test when more than 1 account service is found
            api.services.find.side_effect = [ [mock_find_vdc], [None, None]]
            with pytest.raises(RuntimeError,
                               message='found 2 accounts with name "%s", required exactly one' % account_name):
                instance.config

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_when_already_installed(self, ovc):
        """
        Test successfull install VM action
        """
        # if installed, do nothing
        instance = self.type(name='test', data=self.valid_data)
        instance.state.set('actions', 'install', 'ok')
        instance.install()
        ovc.get.return_value.space_get.return_value.machine_create.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_existent_machine(self, ovc):
        """
        Test successfull install VM action
        """
        instance = self.type(name='test', data=self.valid_data)
        key_name = 'keyName'
        account_service = 'account_service'
        account_name = 'account_name'
        sshkey_name = 'sshkey_name'
        ovc_name = 'ovc_name'

        # mock ovc client
        def get_ovc_client(instance):
            boot_disk = {'id':int, 'type':'B', 'sizeMax':10}
            data_disk = {'id':int, 'type':'D', 'sizeMax':10}
            disks = mock.PropertyMock()
            disks.side_effect=[[boot_disk, data_disk], [boot_disk, data_disk],
                               [boot_disk], [boot_disk, data_disk]]
            machine_mock = MagicMock()
            type(machine_mock).disks=disks

            # set device mounted
            machine_mock.prefab.core.run.return_value = (None, '/dev/vdb on /var type ext4 ', None)
            space_mock = MagicMock(machine_get=MagicMock(return_value=machine_mock),
                                   machines={'nodeName':MagicMock(delete=MagicMock())})

            ovc_mock=MagicMock(space_get=MagicMock(return_value=space_mock)) 
            return ovc_mock           

        # mock finding services
        def find(template_uid, name):     
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [
                key_name, account_service, account_name,
                sshkey_name, ovc_name
                ]
            task_mock = MagicMock()
            type(task_mock).result = result_mock 
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            ovc.get.side_effect = get_ovc_client
            ovc_mock = ovc.get("instance")
            # test when device is mounted
            ovc_mock.space_get.return_value.\
                                 machine_get.return_value. \
                                 prefab.core.run.return_value = (None, '/dev/vdb on /var type ext4 ', None)

            instance.install()

            # check call to get/create machine
            instance.space.machine_get.assert_called_once_with(
                create=True,
                name=instance.get_name(),
                sshkeyname=self.valid_data['sshKey'],
                sizeId=1,
                managed_private=False,
                datadisks=[10],
                disksize=10,
                image='Ubuntu 16.04'
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_and_mount_device(self, ovc):
        """
        Test successfull install VM action
        """
        name = 'test'
        instance = self.type(name=name, data=self.valid_data)

        key_name = 'keyName'
        account_service = 'account_service'
        account_name = 'account_name'
        sshkey_name = 'sshkey_name'
        ovc_name = 'ovc_name'

        # mock ovc client
        def get_ovc_client(instance):
            boot_disk = {'id':int, 'type':'B', 'sizeMax':10}
            data_disk = {'id':int, 'type':'D', 'sizeMax':10}
            disks = mock.PropertyMock()
            disks.side_effect=[[boot_disk], [boot_disk, data_disk]]
            machine_mock = MagicMock()
            type(machine_mock).disks=disks
            # set device mounted
            machine_mock.prefab.core.run.return_value = (None, '', None)
            space_mock = MagicMock(machine_get=MagicMock(return_value=machine_mock),
                                   machines={'nodeName':MagicMock(delete=MagicMock())})

            ovc_mock=MagicMock(space_get=MagicMock(return_value=space_mock)) 
            return ovc_mock           

        # mock finding services
        def find(template_uid, name):     
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [
                key_name, account_service, account_name,
                sshkey_name, ovc_name
                ]
            task_mock = MagicMock()
            type(task_mock).result = result_mock 
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            # test when device is not mounted and disk is not present
            api.services.find.side_effect = find
            ovc.get.return_value = get_ovc_client('instance')
            ovc_mock = ovc.get()
            # check call to create a filesystem
            instance.install()
            # check call to add disk
            instance.machine.disk_add.assert_called_once_with(
                name='Disk nr 1', description='Machine disk of type D',
                size=10, type='D')
            ovc.get.return_value.space_get.return_value. \
                                 machine_get.return_value.\
                                 prefab.system.filesystem.create.assert_called_once_with(
                                    fs_type='ext4', device='/dev/vdb'
                                 )

            # state install must be ok 
            instance.state.check('actions', 'install', 'ok')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_fail_wrong_data_disk_size(self, ovc):
        """
        Test failing install VM action.
        Data disk size is not correct.
        """
        name = 'test'
        key_name = 'keyName'
        account_service = 'account_service'
        account_name = 'account_name'
        sshkey_name = 'sshkey_name'
        ovc_name = 'ovc_name'

        # set up ovc mock
        def get_ovc_client(instance):
            boot_disk = {'id':int, 'type':'B', 'sizeMax':10}
            data_disk = {'id':int, 'type':'D', 'sizeMax':11}
            disks = [boot_disk, data_disk]
            machine_mock = MagicMock(prefab=MagicMock(return_value=None), id=1)
            machine_mock.disks=disks
            machine_mock.prefab.core.run.return_value = (None, '/dev/vdb on /var type ext4 ', None)
            space_mock = MagicMock(machine_get=MagicMock(return_value=machine_mock))
            ovc_mock = MagicMock(space_get=MagicMock(return_value=space_mock))
            return ovc_mock

        # mock finding services
        def find(template_uid, name):     
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [
                key_name, account_service, account_name,
                sshkey_name, ovc_name
                ]
            task_mock = MagicMock()
            type(task_mock).result = result_mock 
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        instance = self.type(name=name, data=self.valid_data)
        with patch.object(instance, 'api') as api:
            # setup mocks
            api.services.find.side_effect = find
            ovc.get.side_effect = get_ovc_client
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            
            # boot disk has wrong size 
            with self.assertRaisesRegex(RuntimeError,
                                        'Datadisk is expected to have size 10, has size 11'):
                instance.install()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_fail_wrong_boot_disk_size(self, ovc):
        """
        Test failing install VM action.
        Boot disk size is not correct
        """
        name = 'test'
        key_name = 'keyName'
        account_service = 'account_service'
        account_name = 'account_name'
        sshkey_name = 'sshkey_name'
        ovc_name = 'ovc_name'

        # set up ovc mock
        def get_ovc_client(instance):
            boot_disk = {'id':int, 'type':'B', 'sizeMax':11}
            disks = [boot_disk] #, data_disk]
            machine_mock = MagicMock(prefab=MagicMock(return_value=None), id=1)
            machine_mock.disks=disks
            machine_mock.prefab.core.run.return_value = (None, '/dev/vdb on /var type ext4 ', None)
            space_mock = MagicMock(machine_get=MagicMock(return_value=machine_mock))
            ovc_mock = MagicMock(space_get=MagicMock(return_value=space_mock))
            return ovc_mock

        # mock finding services
        def find(template_uid, name):     
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [
                key_name, account_service, account_name,
                sshkey_name, ovc_name
                ]
            task_mock = MagicMock()
            type(task_mock).result = result_mock 
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        instance = self.type(name=name, data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            ovc.get.side_effect = get_ovc_client
            # boot disk has wrong size 
            with pytest.raises(RuntimeError,
                              message='Bootdisk is expected to have size 10, has size 11'):
                instance.install()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, ovc):
        """
        Test uninstall VM action
        """
        instance = self.type(name='test', data=self.valid_data)

        def get_ovc_client(instance):
            space_mock = MagicMock(machines={'nodeName' : MagicMock(delete=MagicMock())})
            ovc_mock=MagicMock(space_get=MagicMock(return_value=space_mock))
            return ovc_mock

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            ovc.get.return_value = get_ovc_client('instance')

            instance.uninstall()

            ovc.get.return_value.space_get.return_value. \
                                 machine_get.return_value.\
                                 delete.assert_called_once_with()

        # state install must be unset
        with pytest.raises(StateCheckError,
                           message='actions:install:ok should be unset'):
            instance.state.check('actions', 'install', 'ok')

    def test_start_success(self):
        """
        Test successfull start action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.start()
        instance.machine.start.assert_called_once_with()

    def test_start_fail(self):
        """
        Test failing start action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.start()

    def test_stop_success(self):
        """
        Test successfull stop action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.stop()
        instance.machine.stop.assert_called_once_with()

    def test_stop_fail(self):
        """
        Test failing stop action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.stop()

    def test_restart_success(self):
        """
        Test successfull restart action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.restart()
        instance.machine.restart.assert_called_once_with()

    def test_restart_fail(self):
        """
        Test failing restart action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.restart()

    def test_pause_success(self):
        """
        Test successfull pause action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.pause()
        instance.machine.pause.assert_called_once_with()

    def test_pause_fail(self):
        """
        Test failing pause action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.pause()

    def test_resume_success(self):
        """
        Test successfull resume action
        """
        instance = self.type(name='test', data=self.valid_data)
        
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.resume()
        instance.machine.resume.assert_called_once_with()
    
    def test_resume_fail(self):
        """
        Test failing resume action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.resume()

    def test_reset_success(self):
        """
        Test successfull reset action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.reset()
        instance.machine.reset.assert_called_once_with()

    def test_reset_fail(self):
        """
        Test failing reset action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.reset()

    def test_snapshot_success(self):
        """
        Test successfull snapshot action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot()
        instance.machine.snapshot_create.assert_called_once_with()

    def test_snapshot_fail(self):
        """
        Test failing snapshot action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.snapshot()

    def test_clone_success(self):
        """
        Test successfull clone action
        """
        instance = self.type(name='test', data=self.valid_data)
        clone_name = 'test_clone'

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.clone(clone_name)
        instance.machine.clone.assert_called_once_with(clone_name)

    def test_clone_fail(self):
        """
        Test failing clone action
        """
        instance = self.type(name='test', data=self.valid_data)
        clone_name = 'test_clone'

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.clone(clone_name)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with pytest.raises(TypeError,
                           message="clone() missing 1 required positional argument: 'clone_name'"):
            instance.clone()

    def test_snapshot_rollback_success(self):
        """
        Test successfull snapshot_rollback action
        """
        instance = self.type(name='test', data=self.valid_data)
        snapshot_epoch = 'test_epoch'

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_rollback(snapshot_epoch)
        instance.machine.snapshot_rollback.assert_called_once_with(snapshot_epoch)

    def test_snapshot_rollback_fail(self):
        """
        Test failing snapshot_rollback action
        """
        instance = self.type(name='test', data=self.valid_data)
        snapshot_epoch = 'test_epoch'

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.snapshot_rollback(snapshot_epoch)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with pytest.raises(TypeError,
                           message="snapshot_rollback() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_rollback()

    def test_snapshot_delete_success(self):
        """
        Test successfull snapshot delete action
        """
        instance = self.type(name='test', data=self.valid_data)
        snapshot_epoch = 'test_epoch'

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_delete(snapshot_epoch)
        instance.machine.snapshot_delete.assert_called_once_with(snapshot_epoch) 

    def test_snapshot_delete_fail(self):
        """
        Test failing snapshot delete action
        """
        instance = self.type(name='test', data=self.valid_data)
        snapshot_epoch = 'test_epoch'

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.snapshot_delete(snapshot_epoch)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with pytest.raises(TypeError,
                           message="snapshot_delete() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_delete()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_add_success(self, ovc):
        """
        Test successfull add disk action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            instance._machine = MagicMock()
            instance.disk_add(name='test')
            instance.machine.disk_add.assert_called_with(
                name='test', description='Data disk', size=10, type='D'
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_add_fail(self, ovc):
        """
        Test failing add disk action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.disk_add(name='test')

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with pytest.raises(TypeError,
                           message="disk_add() missing 1 required positional argument: 'name'"):
            instance.disk_add()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_attach_success(self, ovc):
        """
        Test successfull attach disk action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        disk_id = 1
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock(return_value=MagicMock(result=disk_id)))]
            instance._machine = MagicMock()
            instance.disk_attach(disk_service_name='test')
            instance.machine.disk_attach.assert_called_with(disk_id)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_attach_fail(self, ovc):
        """
        Test failing attach disk action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.disk_attach(disk_service_name=str)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with pytest.raises(TypeError,
                           message="disk_attach() missing 1 required positional argument: 'disk_service_name'"):
            instance.disk_attach()

        # fail if disk service is not running
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            with pytest.raises(RuntimeError):
                instance.disk_attach(disk_service_name='test')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_detach_success(self, ovc):
        """
        Test successfull detach disk action
        """
        instance = self.type(name='test', data=self.valid_data)

        instance.state.set('actions', 'install', 'ok')
        disk_id = 1
        disk_type = 'D'
        disk_service_name = 'test_disk'
        instance.data['disks'] = [disk_service_name]

        actions_mock = mock.PropertyMock()
        actions_mock.side_effect = [disk_type, disk_id, disk_type]
        service_mock = MagicMock(
            name=disk_service_name, 
            schedule_action=MagicMock(
                )
            )
        type(service_mock.schedule_action.return_value).result = actions_mock

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [service_mock]
            instance._machine = MagicMock()
            instance.disk_detach(disk_service_name=disk_service_name)
            instance.machine.disk_detach.assert_called_with(disk_id)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_detach_fail(self, ovc):
        """
        Test failing detach disk action
        """
        instance = self.type(name='test', data=self.valid_data)

        # fails if not installed
        with pytest.raises(StateCheckError):
            instance.disk_detach(disk_service_name=str)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with pytest.raises(TypeError,
                           message="disk_detach() missing 1 required positional argument: 'disk_service_name'"):
            instance.disk_detach()

        # fails if disk service is not running
        disk_service_name = 'test_disk'
        instance.data['disks'] = [disk_service_name]
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            with pytest.raises(RuntimeError):
                instance.disk_detach(disk_service_name=disk_service_name)
