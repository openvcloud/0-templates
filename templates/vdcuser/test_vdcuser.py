from js9 import j
import os

from unittest import TestCase
from unittest import mock

from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestVdcUser(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

    def test_validate_openvcloud(self):
        data = {
            'openvcloud': 'connection',
        }
        name = 'test'
        instance = self.type(name, None, data)

        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, data['openvcloud'])

            result = mock.MagicMock()
            result.name = name
            return [result]

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.validate()

        api.services.find.assert_called_once_with(template_uid=self.type.OVC_TEMPLATE, name=data['openvcloud'])

        # Next, we test when NO connection is given
        api.reset_mock()

        data = {}
        instance = self.type(name, None, data)

        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, None)

            result = mock.MagicMock()
            result.name = name
            return [result]

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.validate()

        api.services.find.assert_called_once_with(template_uid=self.type.OVC_TEMPLATE, name=None)

        # Finally, if the search retuned more than one object
        api.reset_mock()

        data = {}
        instance = self.type(name, None, data)

        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, None)

            result = mock.MagicMock()
            result.name = name
            return [result, result]  # return 2

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaises(RuntimeError):
                instance.validate()

        api.services.find.assert_called_once_with(template_uid=self.type.OVC_TEMPLATE, name=None)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, openvcloud):
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'email': 'email@test.com',
        }

        name = 'user1'
        instance = self.type(name, None, data)
        client = openvcloud.get.return_value
        # user exists
        client.api.system.usermanager.userexists.return_value = True
        instance.install()

        client.api.system.usermanager.userexists.assert_called_once_with(name=name)

        openvcloud.reset_mock()
        client.api.system.usermanager.userexists.return_value = False

        instance.install()

        client.api.system.usermanager.create.assert_called_once_with(
            username=name,
            password=data['password'],
            groups=[],
            emails=[data['email']],
            domain='',
            provider='',
        )
        openvcloud.get.assert_called_once_with(data['openvcloud'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, openvcloud):
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'email': 'email@test.com',
        }

        name = 'user1'
        instance = self.type(name, None, data)

        with self.assertRaises(StateCheckError):
            instance.uninstall()

        client = openvcloud.get.return_value
        # user exists
        client.api.system.usermanager.userexists.return_value = True
        instance.state.set('actions', 'install', 'ok')
        instance.uninstall()

        client.api.system.usermanager.userexists.assert_called_once_with(name=name)

        client.api.system.usermanager.delete.assert_called_once_with(
            username=name,
        )
        openvcloud.get.assert_called_once_with(data['openvcloud'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_set_groups(self, openvcloud):
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'email': 'email@test.com',
        }

        name = 'user1'
        instance = self.type(name, None, data)

        with self.assertRaises(StateCheckError):
            instance.groups_set([])

        client = openvcloud.get.return_value
        # user exists
        client.api.system.usermanager.userexists.return_value = True
        instance.state.set('actions', 'install', 'ok')
        instance.groups_set([])  # not changing the groups

        client.api.system.usermanager.editUser.assert_not_called()

        openvcloud.reset_mock()

        groups = ['group1', 'group2']
        instance.groups_set(groups)

        client.api.system.usermanager.editUser.assert_called_once_with(
            username=name,
            groups=groups,
            provider='',
            emails=[data['email']]
        )
