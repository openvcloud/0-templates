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

    @mock.patch.object(j.clients, '_sshkey')
    def test_create(self, ssh):
        dir = '/tmp'
        passphrase = '123456'

        name = 'test'
        self.type(name, None, {'dir': dir, 'passphrase': passphrase})

        dir = '%s/%s' % (dir, name)
        ssh.key_generate.assert_called_once_with(
            dir,
            passphrase=passphrase,
            overwrite=True,
            returnObj=False
        )

        ssh.get.assert_called_once_with(
            name,
            create=True,
            data={
                'path': dir,
                'passphrase_': passphrase,
            }
        )

    @mock.patch.object(j.clients, '_sshkey')
    def test_create_default_dir(self, ssh):
        dir = '/root/.ssh'
        passphrase = '123456'

        name = 'test'
        self.type(name, None, {'passphrase': passphrase})

        dir = '%s/%s' % (dir, name)
        ssh.key_generate.assert_called_once_with(
            dir,
            passphrase=passphrase,
            overwrite=True,
            returnObj=False
        )

        ssh.get.assert_called_once_with(
            name,
            create=True,
            data={
                'path': dir,
                'passphrase_': passphrase,
            }
        )

    @mock.patch.object(j.clients, '_sshkey')
    def test_create_bad_pass(self, ssh):
        dir = '/root/.ssh'
        passphrase = '123'

        name = 'test'
        with self.assertRaises(ValueError):
            self.type(name, None, {'passphrase': passphrase})

        ssh.key_generate.assert_not_called()

        ssh.get.assert_not_called()
