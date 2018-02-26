from js9 import j
import os

from unittest import TestCase
from unittest import mock

from zerorobot import config, template_collection


class TestOpenvcloud(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_create_success(self, client):
        data = {
            'address': 'some.address.com',
            'login': 'some-login',
            'token': 'some-token'
        }
        name = 'test'
        self.type(name, None, data)

        client.get.assert_called_once_with(name, {
            'address': data['address'],
            'login': data['login'],
            'appkey_': data['token'],
            'port': data.get('port', 443)
        }, create=True)

        client.get.return_value.config.save.assert_called_once_with()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_create_missing_data(self, client):
        data = {
            'address': 'some.address.com',
            'login': 'some-login',
            # missing token
        }
        name = 'test'
        with self.assertRaises(ValueError):
            self.type(name, None, data)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_update(self, client):
        data = {
            'address': 'some.address.com',
            'login': 'some-login',
            'token': 'some-token'
        }
        name = 'test'
        instance = self.type(name, None, data)
        client.reset_mock()

        instance.update(address='new.address.com')
        client.get.assert_called_once_with(name, {
            'address': 'new.address.com',
            'login': data['login'],
            'appkey_': data['token'],
            'port': data.get('port', 443)
        }, create=True)

        client.get.return_value.config.save.assert_called_once_with()
