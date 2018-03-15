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

    @mock.patch.object(j.clients, '_openvcloud')
    def test_validate_args(self, client):
        tt = [
            {
                "data": {"description" : "dummy value"},
                "valid": True,
                "msg": "description is a valid argument",
            },
            {
                "data": {"address" : "dummy value"},
                "valid": True,
                "msg": "address is a valid argument",
            },
            {
                "data": {"port" : "dummy value"},
                "valid": True,
                "msg": "port is a valid argument",
            },
            {
                "data": {"token" : "dummy value"},
                "valid": True,
                "msg": "token is a valid argument",
            },
            {
                "data": {"location" : "dummy value"},
                "valid": True,
                "msg": "location is a valid argument",
            },
            {
                "data": {"location" : "dummy value", "port" : "dummy value"},
                "valid": True,
                "msg": "location and port are valid arguments",
            },
            {
                "data": {"foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
            {
                "data": {"addresss" : "dummy value"},
                "valid": False,
                "msg": "addresss is an invalid argument",
            },
            {
                "data": {"toke" : "dummy value"},
                "valid": False,
                "msg": "toke is an invalid argument",
            },
            {
                "data": {"location" : "dummy value", "foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
        ]

        name = 'test'
        dummy_data = {
            'address': 'some.address.com',
            'token': 'some-token',
            'location': 'abc',
        }
        instance = self.type(name, None, dummy_data)

        for tc in tt:
            result = False

            try:
                instance._validate_args(data=tc['data'])
                result = True
            except Exception as err:
                print(err)
                if not isinstance(err, ValueError):
                    self.fail(msg="received unexpected exception:\n\t%s" % (str(err)))
            
            self.assertEqual(tc['valid'], result, tc['msg'])
