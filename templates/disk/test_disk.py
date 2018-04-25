from js9 import j
import os

from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError

class TestDisk(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

        self.valid_data = {'vdc' : 'test_vdc', 'name': 'test_disk'}
        self.location = 'be-gen-demo'
        self.disk_id = '1111'
        self.location_gid = 123
        self.account_name = 'test_account'
        # define properties of space mock
        # account_mock = MagicMock(disks=[{'id':self.disk_id}],
        #                          disk_create=MagicMock(return_value=self.disk_id),
        #                          model={'name': self.account_name})
        # space_mock = MagicMock(model={'acl': [], 'location':self.location},
        #                        account=account_mock)
        # self.ovc_mock = MagicMock(space_get=MagicMock(return_value=space_mock),
        #                           locations=[
        #                               { 
        #                                 'name':self.location,
        #                                 'gid': self.location_gid,
        #                               }
        #                             ],
        #                         )
        self.acc = {'service': 'test_account_service',
                    'info': {'name': 'test_account_real_name',
                             'openvcloud': 'be-gen'}
                    }
        self.vdc = {'service': 'test_vdc_service',
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

    def tearDown(self):
        patch.stopall()




    def test_validate_success_name(self):
        """
        Test validate method with valid data for creation of new disk
        """
        valid_data = {
            'name' : 'test_disk',
            'vdc' : 'test_vdc'
        }

        instance = self.type(name='test', data=valid_data)
        instance.validate()
        assert instance.data['name'] == valid_data['name']
        assert instance.data['vdc'] == valid_data['vdc']

    def test_validate_success_disk_id(self):
        """
        Test validate method with valid data for link to existent disk
        """        
        valid_data = {
            'diskId' : 1111,
            'vdc' : 'test_vdc'
        }

        instance = self.type(name='test', data=valid_data)
        instance.validate()
        assert instance.data['diskId'] == valid_data['diskId']
        assert instance.data['vdc'] == valid_data['vdc']

    def test_validate_fail_empty_data(self):
        """
        Test validate method with invalid data
        """

        invalid_data = {}
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(ValueError, 'vdc service name is required'):
            instance.validate()

    def test_validate_fail_missing_name(self):
        """
        Test validate method with invalid data
        """
        invalid_data = {
            'vdc' : 'test_vdc'
        }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(ValueError, 'provide name to create a new device'):
            instance.validate()

    def test_validate_fail_disk_type(self):
        """
        Test validate method with invalid data: fault disk type
        """
        invalid_data = {
            'name' : 'test_disk',
            'vdc' : 'test_vdc',
            'type': 'A'
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(ValueError, "disk type must be data D or boot B only"):
            instance.validate()

    def test_validate_fail_iops_limits(self):
        """
        Test validate method with invalid data: limits a given incorrectly
        """        
        invalid_data = {
            'name' : 'test_name',
            'vdc' : 'test_vdc',
            'maxIops': 1,
            'readIopsSec': 1
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(RuntimeError, 
                                    "total and read/write of iops_sec cannot be set at the same time"):
            instance.validate()

    def test_validate_fail_iops_limits(self):
        """
        Test validate method with invalid data: limits a given incorrectly
        """              
        invalid_data = {
            'name' : 'test_name',
            'vdc' : 'test_vdc',
            'totalIopsSec': 1,
            'writeIopsSec': 1
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(RuntimeError,
                                    "total and read/write of iops_sec cannot be set at the same time"):
            instance.validate()

    def test_validate_fail_limit_bytes_sec(self):
        """
        Test validate method with invalid data: limits a given incorrectly
        """ 
        invalid_data = {
            'name' : 'test_name',
            'vdc' : 'test_vdc',
            'totalBytesSec': 1,
            'readBytesSec': 1
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(RuntimeError,
                                    "total and read/write of bytes_sec cannot be set at the same time"):
            instance.validate()

    def test_validate_fail_bytes_sec_max_limits_read(self):
        """
        Test validate method with invalid data: limits a given incorrectly
        """ 
        invalid_data = {
            'name' : 'test_name',
            'vdc' : 'test_vdc',
            'totalBytesSecMax': 1,
            'readBytesSecMax': 1
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(RuntimeError,
                                    "total and read/write of bytes_sec_max cannot be set at the same time"):
            instance.validate()

    def test_validate_fail_bytes_sec_max_limits_write(self):
        """
        Test validate method with invalid data: limits a given incorrectly
        """
        invalid_data = {
            'name' : 'test_name',
            'vdc' : 'test_vdc',
            'totalBytesSecMax': 1,
            'writeBytesSecMax': 1
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(RuntimeError,
                                    "total and read/write of bytes_sec_max cannot be set at the same time"):
            instance.validate()

    def test_validate_fail_iops_sec_max_limits_read(self):
        """
        Test validate method with invalid data: limits a given incorrectly
        """ 
        invalid_data = {
            'name' : 'test_name',
            'vdc' : 'test_vdc',
            'totalIopsSecMax': 1,
            'readIopsSecMax': 1
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(RuntimeError,
                                    "total and read/write of iops_sec_max cannot be set at the same time"):
            instance.validate()

    def test_validate_fail_iops_sec_max_limits_write(self):
        """
        Test validate method with invalid data: limits a given incorrectly
        """ 
        invalid_data = {
            'name' : 'test_name',
            'vdc' : 'test_vdc',
            'totalIopsSecMax': 1,
            'writeIopsSecMax': 1
            }
        instance = self.type(name='test', data=invalid_data)
        with self.assertRaisesRegex(RuntimeError,
                                    "total and read/write of iops_sec_max cannot be set at the same time"):
            instance.validate()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_ok(self, ovc):
        """ Test install action when state install is OK """
        instance = self.type(name='my-disk-service', data=self.valid_data)
        instance.state.set('actions', 'install', 'ok')
        instance.install()
        ovc.get.return_value.account_get.return_value.disk_create.assert_not_called()        

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_create_disk_success(self, ovc):
        data = {
            'name': 'TestDisk',
            'description': 'some extra info',
            'size': 2,
            'type': 'D'
        }
        name = 'my-disk-service'
        instance = self.type(name=name, data=data)
        
        vdc_name = 'vdc_name'
        account_service = 'account_service'
        account_name = 'account_name'
        ovc_name = 'ovc_name'
        
        # mock finding services
        def find(template_uid, name):     
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [
                vdc_name, account_service, account_name, ovc_name
                ]
            task_mock = MagicMock()
            type(task_mock).result = result_mock
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock
            api.services.find.side_effect = find
            instance.install()
            instance.account.disk_create.assert_called_once_with(
                            name=data['name'],
                            gid=[self.location_gid],
                            description=data['description'],
                            size=data['size'],
                            type=data['type'],
            )     

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_existent_disk_success(self, ovc):
        name = 'my-disk-service'

        disk_id = self.disk_id
        data = {'vdc' : 'test_vdc', 'diskId' : disk_id}
        instance = self.type(name=name, data=data)

        vdc_name = 'vdc_name'
        account_service = 'account_service'
        account_name = 'account_name'
        ovc_name = 'ovc_name'

        # mock finding services
        def find(template_uid, name):     
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [
                vdc_name, account_service,
                account_name, ovc_name
                ]
            task_mock = MagicMock()
            type(task_mock).result = result_mock 
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        # test success
        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock
            api.services.find.side_effect = find
            instance.install()
            instance.account.disk_create.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_existent_disk_fail(self, ovc):
        name = 'my-disk-service'

        disk_id = 2222
        data = {'vdc' : 'test_vdc', 'diskId' : disk_id}
        instance = self.type(name=name, data=data)

        vdc_name = 'vdc_name'
        account_service = 'account_service'
        ovc_name = 'ovc_name'

        # mock finding services
        def find(template_uid, name):     
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [
                vdc_name, account_service,
                self.account_name , ovc_name
                ]
            task_mock = MagicMock()
            type(task_mock).result = result_mock 
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock
            ovc.get.return_value.space_get.return_value.account.disks = []
            api.services.find.side_effect = find
            with self.assertRaisesRegex(ValueError,
                                        'Disk with id %s does not exist on account "%s"' % 
                                        (disk_id, self.account_name )):
                instance.install()

    def test_config_success(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.valid_data)
        vdc_name = 'test_vdc'
        account_name = 'test_account'
        ovc_name = 'test_ovc'
        task_mock = MagicMock(result=vdc_name)
        mock_find_vdc = MagicMock(schedule_action=MagicMock(return_value=task_mock)) 

        with patch.object(instance, 'api') as api:
            result = mock.PropertyMock()
            result.side_effect = [account_name, ovc_name]
            task_mock = MagicMock()
            type(task_mock).result = result

            mock_find_acc = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            api.services.find.side_effect = [[mock_find_vdc],[mock_find_acc]]
            instance.config
            self.assertEqual(instance.config['ovc'], ovc_name)

    def test_config_fail_find_no_vdc(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            # test when more than 1 vdc service is found
            with self.assertRaisesRegex(RuntimeError,
                                        'found 0 services with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

    def test_config_fail_find_more_than_one_vdc(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [None,None]
            # test when more than 1 vdc service is found
            with self.assertRaisesRegex(RuntimeError,
                                        'found 2 services with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

    def test_config_fail_find_no_account(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.valid_data)
        vdc_name = 'test_vdc'
        account_name = 'test_account'
        with patch.object(instance, 'api') as api:
            # test when no account service is found
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [vdc_name, account_name]
            task_mock = MagicMock()
            type(task_mock).result = result_mock
            mock_find_vdc = MagicMock(schedule_action=MagicMock(return_value=task_mock))       
            api.services.find.side_effect = [ [mock_find_vdc], []]
            with self.assertRaisesRegex(RuntimeError,
                                        'found 0 services with name "%s", required exactly one' % account_name):
                instance.config

    def test_config_fail_find_more_than_one_account(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.valid_data)
        vdc_name = 'test_vdc'
        account_name = 'test_account'
        with patch.object(instance, 'api') as api:
            # test when no account service is found
            result_mock = mock.PropertyMock()
            result_mock.side_effect = [vdc_name, account_name]
            task_mock = MagicMock()
            type(task_mock).result = result_mock
            mock_find_vdc = MagicMock(schedule_action=MagicMock(return_value=task_mock))       
            # test when more than 1 account service is found
            api.services.find.side_effect = [ [mock_find_vdc], [None, None]]
            with self.assertRaisesRegex(RuntimeError,
                                        'found 2 services with name "%s", required exactly one' % account_name):
                instance.config

    def test_uninstall_fail_boot_disk(self):
        data = {
            'type': 'B',
        }
        instance = self.type(name='test', data=data)
        with self.assertRaisesRegex(RuntimeError, "can't delete boot disk"):
            instance.uninstall()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_success(self, ovc):
        disk_id = self.disk_id
        data = {
            'deviceName': 'TestDisk',
            'description': 'some extra info',
            'size': 2,
            'type': 'D',
            'diskId': disk_id
        }

        instance = self.type(name='test', data=data)
        def find(template_uid, name):
            result_mock = int
            task_mock = MagicMock()
            type(task_mock).result = result_mock
            proxy = MagicMock(return_value=MagicMock(schedule_action=task_mock))
            
            return [proxy]
        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock
            ovc.get.return_value.space_get.return_value.account.disks = [{'id': disk_id}]
            api.services.find.side_effect = find
            instance.uninstall()

        instance.account.disk_delete.assert_called_once_with(disk_id)
        with self.assertRaises(StateCheckError):
            instance.state.check('actions', 'install', 'ok')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_nonexistent_disk(self, ovc):
        disk_id = 5555
        existent_disks = [{'id': 1111}]
        data = {
            'deviceName': 'TestDisk',
            'description': 'some extra info',
            'size': 2,
            'type': 'D',
            'diskId': disk_id
        }

        instance = self.type(name='test', data=data)
        def find(template_uid, name):
            result_mock = int
            task_mock = MagicMock()
            type(task_mock).result = result_mock
            proxy = MagicMock(return_value=MagicMock(schedule_action=task_mock))
            
            return [proxy]
        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock
            ovc.get.return_value.space_get.return_value.account.disks = existent_disks
            api.services.find.side_effect = find
            instance.uninstall()

        instance.account.disk_delete.assert_not_called()

        with self.assertRaises(StateCheckError):
            instance.state.check('actions', 'install', 'ok')

    def test_update_fail_statecheckerror(self):
        instance = self.type(name='test', data=None)
        with self.assertRaises(StateCheckError):
            instance.update()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_update_success(self, ovc):
        data = {
            'deviceName': 'TestDisk',
            'description': 'some extra info',
            'size': 2,
            'type': 'D',
            'diskId': self.disk_id
        }
        # update arg
        maxIops = 5

        instance = self.type(name='test', data=data)
        instance.state.set('actions', 'install', 'ok')

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock()]
            ovc.get.return_value = self.ovc_mock

            instance.update(maxIops=maxIops)
