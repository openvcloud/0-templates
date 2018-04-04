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

        # define properties of space mock
        space_mock = MagicMock(model={'acl': []})
        self.ovc_mock = MagicMock(space_get=MagicMock(return_value=space_mock))

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



