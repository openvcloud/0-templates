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
            'token': 'some-token',
            'location': 'abc',
        }
        name = 'test'
        self.type(name, None, data)

        client.get.assert_called_once_with(name, {
            'address': data['address'],
            'jwt_': data['token'],
            'port': data.get('port', 443),
            'location': 'abc',
        }, create=True)

        client.get.return_value.config.save.assert_called_once_with()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_create_missing_data(self, client):
        data = {
            'address': 'some.address.com',
            # missing token
        }
        name = 'test'
        with self.assertRaises(ValueError):
            self.type(name, None, data)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_update(self, client):
        data = {
            'address': 'some.address.com',
            'token': 'some-token',
            'location': 'abc',
        }
        name = 'test'
        instance = self.type(name, None, data)
        client.reset_mock()

        instance.update(address='new.address.com')
        client.get.assert_called_once_with(name, {
            'address': 'new.address.com',
            'jwt_': data['token'],
            'port': data.get('port', 443),
            'location': 'abc',
        }, create=True)

        client.get.return_value.config.save.assert_called_once_with()
