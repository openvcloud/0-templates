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
        self.location = {'name': 'be-gen-demo', 'gid': 123}

        #self.location_gid = 123
        #self.disk_id = '1111'
        #self.account_name = 'test_account'
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
        #       
        #                   )
        self.ovc = {
            'service': 'test_ovc_service',
            'info': {'name': 'connection_instance_name'}
        }        
        self.acc = {'service': 'test_account_service',
                    'info': {'name': 'test_account_real_name',
                             'openvcloud': self.ovc['service']}
        }
        self.vdc = {'service': 'test_vdc_service',
                    'info': {'name': 'test_vdc_real_name',
                             'account': self.acc['service']}
        }
        self.disk = {'service': 'test_disk_service',
                     'info': {'name': 'disk_real_name',
                              'vdc': self.vdc['service'],
                              'diskId': '1111',
                              'diskType': 'D',},
        }

    def tearDown(self):
        patch.stopall()

    def find(self, template_uid, name):
        if template_uid == self.type.OVC_TEMPLATE:
            return [self.set_up_proxy_mock(result=self.ovc['info'], name=self.ovc['service'])]
        if template_uid == self.type.ACCOUNT_TEMPLATE:
            return [self.set_up_proxy_mock(result=self.acc['info'], name=self.acc['service'])]
        if template_uid == self.type.VDC_TEMPLATE:
            return [self.set_up_proxy_mock(result=self.vdc['info'], name=self.vdc['service'])]

    @staticmethod
    def set_up_proxy_mock(result, state='ok', name='service_name'):
        task = MagicMock(result=result, state=state)
        proxy = MagicMock(schedule_action=MagicMock(return_value=task))
        proxy.name = name
        return proxy

    def ovc_mock(self, instance):
        disks = [{'id': self.disk['info']['diskId'],
                   'name': self.disk['info']['name']}]
        account_mock = MagicMock(disks=disks,
                                 disk_create=MagicMock(return_value=self.disk['info']['diskId']),
                                 model={'name': self.acc['info']['name']})        
        space_mock = MagicMock(model={'acl': [], 'location':self.location['name']},
                               account=account_mock)
        ovc_mock = MagicMock(space_get=MagicMock(return_value=space_mock),
                                  locations=[
                                      { 
                                        'name':self.location['name'],
                                        'gid': self.location['gid'],
                                      }
                                    ],
                                )
        return ovc_mock

    def test_validate_success_create_disk(self):
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

    def test_validate_success_existent_disk(self):
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
            'name': self.disk['info']['name'],
            'description': 'some extra info',
            'size': 2,
            'type': 'D'
        }
        name = 'my-disk-service'
        instance = self.type(name=name, data=data)
        
        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
            api.services.find.side_effect = self.find
            instance.install()
            instance.account.disk_create.assert_called_once_with(
                            name=data['name'],
                            gid=[self.location['gid']],
                            description=data['description'],
                            size=data['size'],
                            type=data['type'],
            )     

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_existent_disk_success(self, ovc):
        name = 'my-disk-service'

        data = {'vdc' : self.vdc['service'], 
                'diskId' : self.disk['info']['diskId']}
        instance = self.type(name=name, data=data)

        # test success
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.install()
            instance.account.disk_create.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_existent_disk_fail(self, ovc):
        name = 'my-disk-service'

        disk_id = 2222
        data = {'vdc' : 'test_vdc', 'diskId' : disk_id}
        instance = self.type(name=name, data=data)

        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
            ovc.get.return_value.space_get.return_value.account.disks = []
            api.services.find.side_effect = self.find
            with self.assertRaisesRegex(ValueError,
                                        'Disk with id %s does not exist on account "%s"' % 
                                        (disk_id, self.acc['info']['name'] )):
                instance.install()

    def test_config_success(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.disk['info'])

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.config
            self.assertEqual(instance.config['ovc'], self.ovc['info']['name'])

    def test_config_fail_find_no_vdc(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.disk['info'])
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            # test when more than 1 vdc service is found
            with self.assertRaisesRegex(RuntimeError,
                                        'found 0 services with name "%s", required exactly one' % self.vdc['service']):
                instance.config

    def test_config_fail_find_more_than_one_vdc(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.disk['info'])
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [None,None]
            # test when more than 1 vdc service is found
            with self.assertRaisesRegex(RuntimeError,
                                        'found 2 services with name "%s", required exactly one' % self.vdc['service']):
                instance.config

    def test_config_fail_find_no_account(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.disk['info'])
        with patch.object(instance, 'api') as api:
            vdc_proxy = self.find(self.type.VDC_TEMPLATE, self.vdc['service'])
            api.services.find.side_effect = [vdc_proxy, []]
            with self.assertRaisesRegex(RuntimeError,
                                        'found 0 services with name "%s", required exactly one' % 
                                        self.acc['service']):
                instance.config

    def test_config_fail_find_no_ovc(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.disk['info'])
        with patch.object(instance, 'api') as api:
            vdc_proxy = self.find(self.type.VDC_TEMPLATE, self.vdc['service'])
            acc_proxy = self.find(self.type.ACCOUNT_TEMPLATE, self.acc['service'])
            api.services.find.side_effect = [vdc_proxy, acc_proxy, []]
            with self.assertRaisesRegex(RuntimeError,
                                        'found 0 services with name "%s", required exactly one' % 
                                        self.ovc['service']):
                instance.config

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_fail_boot_disk(self, ovc):
        data = self.disk['info']
        data['type'] = 'B'
        instance = self.type(name='test', data=data)
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find        
            with self.assertRaisesRegex(RuntimeError, "can't delete boot disk"):
                instance.uninstall()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_success(self, ovc):
        data = self.disk['info']
        instance = self.type(name='test', data=data)

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.uninstall()

        instance.account.disk_delete.assert_called_once_with(data['diskId'], detach=False)
        with self.assertRaises(StateCheckError):
            instance.state.check('actions', 'install', 'ok')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_nonexistent_disk(self, ovc):
        data = {
            'deviceName': 'TestDisk',
            'diskId': '5555'
        }

        instance = self.type(name='test', data=data)
        with patch.object(instance, 'api') as api:
            ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
            api.services.find.side_effect = self.find
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
        # field to update
        maxIops = 5

        instance = self.type(name='test', data=self.disk['info'])
        instance.state.set('actions', 'install', 'ok')

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
            instance.update(maxIops=maxIops)
        
        self.assertEqual(instance.data['maxIops'], maxIops)
