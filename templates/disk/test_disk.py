from js9 import j
import os

from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
import pytest

from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError

class TestDisk(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

        self.valid_data = {'vdc' : 'test_vdc'}
        self.location = 'be-gen-demo'
        self.disk_id = '1111'
        self.location_gid = 123
        # define properties of space mock
        account_mock = MagicMock(disks=[{'id':self.disk_id}],
                                 disk_create=MagicMock(return_value=self.disk_id))
        space_mock = MagicMock(model={'acl': [], 'location':self.location},
                               account=account_mock)
        self.ovc_mock = MagicMock(space_get=MagicMock(return_value=space_mock),
                                  locations=[
                                      { 
                                        'name':self.location,
                                        'gid': self.location_gid,
                                      }
                                    ],
                                )

    def test_validate(self):
        '''
        Test validate method
        '''
        name = 'test'

        # test success
        instance = self.type(name=name, data=self.valid_data)
        instance.validate()

        # test fail when data is empty
        invalid_data = {}
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message='vdc name should be given'):
            instance.validate()

        # test fail when fault disk type
        invalid_data = {
            'vdc' : 'test_vdc',
            'type': 'A'
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="diskovc's type must be data (D) or boot (B) only"):
            instance.validate()
        
        # test fail when limits a given incorrectly
        invalid_data = {
            'vdc' : 'test_vdc',
            'maxIops': 1,
            'readIopsSec': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of iops_sec cannot be set at the same time"):
            instance.validate()
        
        invalid_data = {
            'vdc' : 'test_vdc',
            'totalIopsSec': 1,
            'writeIopsSec': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of iops_sec cannot be set at the same time"):
            instance.validate()

        invalid_data = {
            'vdc' : 'test_vdc',
            'totalBytesSec': 1,
            'readBytesSec': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of bytes_sec cannot be set at the same time"):
            instance.validate()

        invalid_data = {
            'vdc' : 'test_vdc',
            'totalBytesSec': 1,
            'writeBytesSec': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of bytes_sec cannot be set at the same time"):
            instance.validate()

        invalid_data = {
            'vdc' : 'test_vdc',
            'totalBytesSecMax': 1,
            'readBytesSecMax': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of bytes_sec_max cannot be set at the same time"):
            instance.validate()

        invalid_data = {
            'vdc' : 'test_vdc',
            'totalBytesSecMax': 1,
            'writeBytesSecMax': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of bytes_sec_max cannot be set at the same time"):
            instance.validate()

        invalid_data = {
            'vdc' : 'test_vdc',
            'totalIopsSecMax': 1,
            'readIopsSecMax': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of iops_sec_max cannot be set at the same time"):
            instance.validate()

        invalid_data = {
            'vdc' : 'test_vdc',
            'totalIopsSecMax': 1,
            'writeIopsSecMax': 1
            }
        instance = self.type(name=name, data=invalid_data)
        with pytest.raises(RuntimeError,
                          message="total and read/write of iops_sec_max cannot be set at the same time"):
            instance.validate()
        
        # test success
        instance = self.type(name=name, data=self.valid_data)

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
            'deviceName': 'TestDisk',
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

        # test success
        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock
            api.services.find.side_effect = find
            instance.install()
            instance.account.disk_create.assert_called_once_with(
                            name=data['deviceName'],
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

        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock
            ovc.get.return_value.space_get.return_value.account.disks = []
            api.services.find.side_effect = find
            with pytest.raises(ValueError,
                               message='Data Disk with Id = "%s" was not found' % self.disk_id):
                instance.install()

    def test_config_success(self):
        '''
        Test fetching config from vdc, account, and ovc services
        '''
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
        '''
        Test fetching config from vdc, account, and ovc services
        '''
        instance = self.type(name='test', data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            # test when more than 1 vdc service is found
            with pytest.raises(RuntimeError,
                               message='found 2 vdcs with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

    def test_config_fail_find_more_than_one_vdc(self):
        '''
        Test fetching config from vdc, account, and ovc services
        '''
        instance = self.type(name='test', data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [None,None]
            # test when more than 1 vdc service is found
            with pytest.raises(RuntimeError,
                               message='found 2 vdcs with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

    def test_config_fail_find_no_account(self):
        '''
        Test fetching config from vdc, account, and ovc services
        '''
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

    def test_config_fail_find_more_than_one_account(self):
        '''
        Test fetching config from vdc, account, and ovc services
        '''
        instance = self.type(name='test', data=self.valid_data)
        vdc_name = 'test_vdc'
        account_name = 'test_account'
        with patch.object(instance, 'api') as api:
            task_mock = MagicMock(result=vdc_name)
            mock_find_vdc = MagicMock(schedule_action=MagicMock(return_value=task_mock))            

            # test when more than 1 account service is found
            api.services.find.side_effect = [ [mock_find_vdc], [None, None]]
            with pytest.raises(RuntimeError,
                               message='found 2 accounts with name "%s", required exactly one' % account_name):
                instance.config