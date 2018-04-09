import os
import pytest
from unittest import mock
from unittest import TestCase
from js9 import j


from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestOpenvcloud(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

    def test_validate(self):
        # test fail if name is not given
        name = 'test'
        data = {
            'address': 'some.address.com',
            'token': 'some-token',
            'location': 'abc',
        }
        instance = self.type(name, None, data)
        with pytest.raises(ValueError,
                           message='name is required'):
            instance.validate()
        # test fail if address is not given
        data = {
            'name' : 'be-gen-demo', 
            'token': 'some-token',
            'location': 'abc',
        }
        instance = self.type(name, None, data)
        with pytest.raises(ValueError,
                           message='name is required'):
            instance.validate()

        # test fail if token is not given
        data = {
            'name' : 'be-gen-demo', 
            'address': 'some.address.com',
            'location': 'abc',
        }
        instance = self.type(name, None, data)
        with pytest.raises(ValueError,
                           message='token is required'):
            instance.validate()

        # test fail if location is not given
        data = {
            'name' : 'be-gen-demo', 
            'address': 'some.address.com',
            'token': 'some-token',
        }
        instance = self.type(name, None, data)
        with pytest.raises(ValueError,
                           message='location is required'):
            instance.validate()
        # test success
        data = {
            'name' : 'be-gen-demo', 
            'address': 'some.address.com',
            'token': 'some-token',
            'location': 'abc',
        }
        instance = self.type(name, None, data)
        instance.validate()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, client):
        data = {
            'name' : 'be-gen-demo', 
            'address': 'some.address.com',
            'token': 'some-token',
            'location': 'abc',
        }
        name = 'test'
        instance = self.type(name, None, data)

        instance.install()
        client.get.assert_called_once_with(instance.data['name'], {
            'address': data['address'],
            'jwt_': data['token'],
            'port': data.get('port', 443),
            'location': 'abc',
        }, create=True)

        client.get.return_value.config.save.assert_called_once_with()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_update(self, client):
        data = {
            'name' : 'be-gen-demo',
            'address': 'some.address.com',
            'token': 'some-token',
            'location': 'abc',
        }
        instance = self.type('test', None, data)
        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.update()

        instance.state.set('actions', 'install', 'ok')

        client.reset_mock()

        new_address = 'new.address.com'
        instance.update(address=new_address)
        client.get.assert_called_once_with(data['name'], {
            'address': new_address,
            'jwt_': data['token'],
            'port': data.get('port', 443),
            'location': 'abc',
        }, create=True)

        client.get.return_value.config.save.assert_called_once_with()

    @mock.patch.object(j.tools, '_configmanager')
    def test_uninstall(self, conf_manager):
        data = {'name' : 'be-gen-demo'}

        instance = self.type('test', None, data)
        instance.uninstall()
        conf_manager.delete.assert_called_once_with(
            location="j.clients.openvcloud",
            instance=instance.data['name']
        )

        with pytest.raises(StateCheckError):
            instance.state.check('actions', 'install', 'ok')