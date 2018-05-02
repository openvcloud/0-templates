from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
from unittest import skip
import tempfile
import shutil
import os

from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot import config, template_collection
from zerorobot.template_uid import TemplateUID
from zerorobot.template.state import StateCheckError
from zerorobot.service_collection import ServiceNotFoundError


class TestNode(TestCase):

    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

        self.ovc = {
            'service': 'test_ovc_service',
            'info': {'name': 'connection_instance_name'}
        }        
        self.acc = {'service': 'test_account-service',
                    'info': {'name': 'test_account_real_name',
                             'openvcloud': self.ovc['service']}
                    }
        self.vdc = {'service': 'test-vdc-service',
                    'info': {'name': 'test_vdc_real_name',
                             'account': self.acc['service']}
                    }
        self.disk = {'service': 'test_disk_service',
                     'info': {'name': 'disk_real_name',
                              'vdc': self.vdc['service'],
                              'diskId': 1,
                              'diskType': 'D',
                        },
                }
        self.sshkey = {
            'service': 'test_node_service',
            'info': {
                    'name': 'test_sshkey_name',
                }
        }                 
        self.node = {
            'service': 'test_node_service',
            'info': {
                    'name': 'test_node_name',
                    'vdc': self.vdc['service'],
                    'sshKey': self.sshkey['service']
                }
        }   

    def tearDown(self):
        patch.stopall()

    def ovc_mock(self, instance):
        disks = [{'type': 'B', 'sizeMax': 10, 'id': 1234}, 
                 {'type': 'D', 'sizeMax': 10, 'id': 4321}]
        machine_mock = MagicMock(disks=disks)
        machine_mock.prefab.core.run.return_value = (
                    None, '/dev/vdb on /var type ext4 ', None)
        space_mock = MagicMock(machines=[self.node['info']['name']],
                               machine_create=MagicMock(return_value=machine_mock))
        return MagicMock(space_get=MagicMock(return_value=space_mock))

    @staticmethod
    def set_up_proxy_mock(result=None, name='service_name'):
        """ Setup a mock for a proxy of zrobot service  """
        proxy = MagicMock(schedule_action=MagicMock())
        proxy.schedule_action().wait = MagicMock()
        proxy.schedule_action().wait().result = result
        proxy.name = name
        return proxy

    def get_service(self, template_uid, name):
        if template_uid == self.type.OVC_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.ovc['info'], name=name)
        elif template_uid == self.type.ACCOUNT_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.acc['info'], name=name)
        elif template_uid == self.type.VDC_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.vdc['info'], name=name)            
        elif template_uid == self.type.DISK_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.disk['info'], name=name)
        elif template_uid == self.type.SSH_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.sshkey['info'], name=name)            
        else:
            proxy = None
        return proxy

    def test_validate_success(self):
        """
        Test successfull validation
        """
        name = 'test'
        instance = self.type(name=name, guid=None, data=self.node['info'])
        instance.validate()

    def test_validate_fail_missing_vdc(self):
        """
        Test validate method
        """

        # test missing name
        invalid_data = {
            'vdc': 'vdcName',
            'sshKey': 'keyName'
        }

        instance = self.type(name='test', guid=None, data=invalid_data)
        with self.assertRaisesRegex(ValueError, 'VM name is required'):
            instance.validate()

    def test_validate_fail_missing_sshkey(self):
        # test missing sshkey service name
        invalid_data = {
            'name': 'nodeName',
            'vdc': 'vdcName',
        }

        instance = self.type(name='test', guid=None, data=invalid_data)
        with self.assertRaisesRegex(ValueError, 'sshKey service name is required'):
            instance.validate()

    def test_validate_fail_missing_vm_name(self):
        # test missing sshkey service name
        invalid_data = {
            'name': 'nodeName',
            'sshKey': 'sshkeyName',
        }
        instance = self.type(name='test', guid=None, data=invalid_data)
        with self.assertRaisesRegex(ValueError, 'vdc service name is required'):
            instance.validate()

    def test_config_success(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.node['info'])

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.config
            
        self.assertEqual(
            instance.config['ovc'], self.ovc['info']['name'])
        self.assertEqual(
            instance.config['account'], self.acc['info']['name'])
        self.assertEqual(
            instance.config['vdc'], self.vdc['info']['name'])

    def test_config_fail_no_vdc_service(self):
        """
        Test getting config from a vdc service
        """
        instance = self.type(name='test', data=self.node['info'])

        with self.assertRaises(ServiceNotFoundError):
            instance.config

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_when_already_installed(self, ovc):
        """
        Test successfull install VM action
        """
        # if installed, do nothing
        instance = self.type(name='test', data=self.node['info'])
        instance.state.set('actions', 'install', 'ok')
        instance.install()
        ovc.get.return_value.space_get.return_value.machine_create.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_existent_vm_success(self, ovc):
        """
        Test successfull install VM action
        """
        instance = self.type(name='test', data=self.node['info'])

        disk = self.disk

        def find_or_create(template_uid, service_name, data):
            self.assertEqual(template_uid, self.type.DISK_TEMPLATE)
            return self.set_up_proxy_mock(result=disk['info'], name=disk['service'])

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            api.services.find_or_create.side_effect = find_or_create
            instance.install()

            # check call to get/create machine
            instance.space.machine_create.assert_called_once_with(
                name=instance.data['name'],
                sshkeyname=self.sshkey['info']['name'],
                sizeId=1,
                managed_private=False,
                datadisks=[10],
                disksize=10,
                image='Ubuntu 16.04'
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_fail_wrong_data_disk_size(self, ovc):
        """
        Test failing install VM action.
        Data disk size is not correct.
        """

        instance = self.type(name=self.node['service'], data=self.node['info'])
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        space = client.space_get.return_value
        machine = space.machine_create.return_value
        machine.disks=[
            {'id': int, 'type': 'B', 'sizeMax': 10},
            {'id': int, 'type': 'D', 'sizeMax': 11}
        ]

        with patch.object(instance, 'api') as api:
            # setup mocks
            api.services.get.side_effect = self.get_service

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
        instance = self.type(name=self.node['service'], data=self.node['info'])
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        space = client.space_get.return_value
        machine = space.machine_create.return_value
        machine.disks=[
            {'id': int, 'type': 'B', 'sizeMax': 11},
            {'id': int, 'type': 'D', 'sizeMax': 10}
        ]

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service

            # boot disk has wrong size
            with self.assertRaisesRegex(RuntimeError,
                                       'Bootdisk is expected to have size 10, has size 11'):
                instance.install()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, ovc):
        """
        Test uninstall VM action
        """
        instance = self.type(name='test', data=self.node['info'])

        ovc.get.side_effect = self.ovc_mock
        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.uninstall()
            instance.machine.delete.assert_called_once_with()

        # state install must be unset
        with self.assertRaises(StateCheckError):
            instance.state.check('actions', 'install', 'ok')

    def test_start_success(self):
        """
        Test successfull start action
        """
        instance = self.type(name='test', data=self.node['info'])

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.start()
        instance.machine.start.assert_called_once_with()

    def test_start_fail(self):
        """
        Test failing start action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.start()

    def test_stop_success(self):
        """
        Test successfull stop action
        """
        instance = self.type(name='test', data=self.node['info'])

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.stop()
        instance.machine.stop.assert_called_once_with()

    def test_stop_fail(self):
        """
        Test failing stop action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.stop()

    def test_restart_success(self):
        """
        Test successfull restart action
        """
        instance = self.type(name='test', data=self.node['info'])

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.restart()
        instance.machine.restart.assert_called_once_with()

    def test_restart_fail(self):
        """
        Test failing restart action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.restart()

    def test_pause_success(self):
        """
        Test successfull pause action
        """
        instance = self.type(name='test', data=self.node['info'])

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.pause()
        instance.machine.pause.assert_called_once_with()

    def test_pause_fail(self):
        """
        Test failing pause action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.pause()

    def test_resume_success(self):
        """
        Test successfull resume action
        """
        instance = self.type(name='test', data=self.node['info'])

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.resume()
        instance.machine.resume.assert_called_once_with()

    def test_resume_fail(self):
        """
        Test failing resume action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.resume()

    def test_reset_success(self):
        """
        Test successfull reset action
        """
        instance = self.type(name='test', data=self.node['info'])

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.reset()
        instance.machine.reset.assert_called_once_with()

    def test_reset_fail(self):
        """
        Test failing reset action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.reset()

    def test_snapshot_success(self):
        """
        Test successfull snapshot action
        """
        instance = self.type(name='test', data=self.node['info'])

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot()
        instance.machine.snapshot_create.assert_called_once_with()

    def test_snapshot_fail(self):
        """
        Test failing snapshot action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.snapshot()

    def test_clone_success(self):
        """
        Test successfull clone action
        """
        instance = self.type(name='test', data=self.node['info'])
        clone_name = 'test_clone'

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.clone(clone_name)
        instance.machine.clone.assert_called_once_with(clone_name)

    def test_clone_fail(self):
        """
        Test failing clone action
        """
        instance = self.type(name='test', data=self.node['info'])
        clone_name = 'test_clone'

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.clone(clone_name)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with self.assertRaises(TypeError):
            instance.clone()

    def test_snapshot_rollback_success(self):
        """
        Test successfull snapshot_rollback action
        """
        instance = self.type(name='test', data=self.node['info'])
        snapshot_epoch = 'test_epoch'

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_rollback(snapshot_epoch)
        instance.machine.snapshot_rollback.assert_called_once_with(
            snapshot_epoch)

    def test_snapshot_rollback_fail(self):
        """
        Test failing snapshot_rollback action
        """
        instance = self.type(name='test', data=self.node['info'])
        snapshot_epoch = 'test_epoch'

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.snapshot_rollback(snapshot_epoch)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with self.assertRaises(TypeError,
                           message="snapshot_rollback() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_rollback()

    def test_snapshot_delete_success(self):
        """
        Test successfull snapshot delete action
        """
        instance = self.type(name='test', data=self.node['info'])
        snapshot_epoch = 'test_epoch'

        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_delete(snapshot_epoch)
        instance.machine.snapshot_delete.assert_called_once_with(
            snapshot_epoch)

    def test_snapshot_delete_fail(self):
        """
        Test failing snapshot delete action
        """
        instance = self.type(name='test', data=self.node['info'])
        snapshot_epoch = 'test_epoch'

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.snapshot_delete(snapshot_epoch)

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with self.assertRaises(TypeError,
                           message="snapshot_delete() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_delete()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_add_success(self, ovc):
        """
        Test successfull add disk action
        """

        disk = self.disk

        def find_or_create(template_uid, service_name, data):
            self.assertEqual(template_uid, self.type.DISK_TEMPLATE)
            return self.set_up_proxy_mock(result=disk['info'], name=disk['service'])

        instance = self.type(name='test', data=self.node['info'])
        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            api.services.find_or_create.side_effect = find_or_create
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
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.disk_add(name='test')

        instance.state.set('actions', 'install', 'ok')

        # test call without arguments
        with self.assertRaises(TypeError):
            instance.disk_add()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_attach_success(self, ovc):
        """
        Test successfull attach disk action
        """
        instance = self.type(name='test', data=self.node['info'])
        instance.state.set('actions', 'install', 'ok')

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance._machine = MagicMock()
            instance.disk_attach(disk_service_name='test')
            instance.machine.disk_attach.assert_called_with(self.disk['info']['diskId'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_attach_fail(self, ovc):
        """
        Test failing attach disk action
        """
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.disk_attach(disk_service_name=str)

        instance.state.set('actions', 'install', 'ok')

        with self.assertRaises(ServiceNotFoundError):
            instance.disk_attach(disk_service_name='test')


    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_detach_success(self, ovc):
        """
        Test successfull detach disk action
        """
        disk = self.disk
         
        instance = self.type(name='test', data=self.node['info'])
        instance.state.set('actions', 'install', 'ok')
        instance.data['disks'] = [disk['service']]
        ovc.get.side_effect = self.ovc_mock
        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.disk_detach(disk_service_name=disk['service'])
            instance.machine.disk_detach.assert_called_with(disk['info']['diskId'])


    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_detach_fail_state_check_error(self, ovc):
        instance = self.type(name='test', data=self.node['info'])

        # fails if not installed
        with self.assertRaises(StateCheckError):
            instance.disk_detach(disk_service_name=str)        

    @mock.patch.object(j.clients, '_openvcloud')
    def test_disk_detach_fail(self, ovc):
        """
        Test failing detach disk action
        """
        instance = self.type(name='test', data=self.node['info'])
        instance.state.set('actions', 'install', 'ok')

        # fails if disk service is not found
        disk_service_name = 'test'
        instance.data['disks'] = [disk_service_name]
        with self.assertRaises(ServiceNotFoundError):
            instance.disk_detach(disk_service_name=disk_service_name)

