from js9 import j
import os

from unittest import TestCase
from unittest import mock

from zerorobot import config, template_collection


class TestSshKey(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

        # mock ssh client
        self.ssh_patch = mock.patch.object(j.clients, '_ssh')
        self.ssh = self.ssh_patch.start()

    def tearDown(self):
        self.ssh_patch.stop()

    def test_create(self):
        path = '/path/to/key/file'
        self.type("test", None, {'path': path})
        self.ssh.load_ssh_key.assert_called_with(path)

    def test_update_data_no_change(self):
        path = '/path/to/key/file'
        instance = self.type("test", None, {'path': path})

        self.ssh.load_ssh_key.assert_called_once_with(path)

        self.ssh.reset_mock()
        instance.update_data({'path': path})

        self.ssh.ssh_key_unload.assert_not_called()
        self.ssh.load_ssh_key.assert_not_called()

    def test_update_data_change(self):
        path1 = '/path/to/key/file'
        instance = self.type("test", None, {'path': path1})

        self.ssh.load_ssh_key.assert_called_once_with(path1)

        self.ssh.reset_mock()
        path2 = '/path/to/new/key/file'
        instance.update_data({'path': path2})

        self.ssh.ssh_key_unload.assert_called_once_with(path1)
        self.ssh.load_ssh_key.assert_called_once_with(path2)
