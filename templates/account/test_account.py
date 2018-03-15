from js9 import j
import os

from unittest import TestCase
from unittest import mock

from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestAccount(TestCase):
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
            with self.assertRaises(ValueError):
                instance.validate()

        api.services.find.assert_not_called()

        # Finally, if the search retuned more than one object
        api.reset_mock()

        data = {
            'openvcloud': 'connection'
        }
        instance = self.type(name, None, data)

        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, data['openvcloud'])

            result = mock.MagicMock()
            result.name = name
            return [result, result]  # return 2

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaises(RuntimeError):
                instance.validate()

        api.services.find.assert_called_once_with(template_uid=self.type.OVC_TEMPLATE, name=data['openvcloud'])

    def test_validate_users(self):
        data = {
            'openvcloud': 'connection',
            'users': [
                {'name': 'test-user'},
            ]
        }
        name = 'test'
        instance = self.type(name, None, data)

        def find(template_uid, name):
            if template_uid == self.type.OVC_TEMPLATE:
                # handle the connection search (tested in another test method)
                result = mock.MagicMock()
                result.name = 'connection'
                return [result]

            self.assertEqual(template_uid, self.type.VDCUSER_TEMPLATE)
            self.assertEqual(name, data['users'][0]['name'])

            result = mock.MagicMock()
            result.name = name
            return [result]

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.validate()

        api.services.find.assert_has_calls(
            [
                mock.call(template_uid=self.type.OVC_TEMPLATE, name=data['openvcloud']),
                mock.call(template_uid=self.type.VDCUSER_TEMPLATE, name=data['users'][0]['name'])
            ]
        )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, openvcloud):
        data = {
            'openvcloud': 'connection',
            # 'users': [
            #     {'name': 'test-user'},
            # ]
        }
        name = 'test'
        instance = self.type(name, None, data)
        instance.install()

        openvcloud.get.assert_called_once_with(data['openvcloud'])

        cl = openvcloud.get.return_value
        cl.account_get.assert_called_once_with(
            name=name,
            create=True,
            # default values
            maxMemoryCapacity=-1,
            maxVDiskCapacity=-1,
            maxCPUCapacity=-1,
            maxNumPublicIP=-1,
        )

        account = cl.account_get.return_value
        account.save.assert_called_once_with()

    def test_authorize_users(self):
        data = {
            'users': [
                {'name': 'test1'},
                {'name': 'test2', 'accesstype': 'R'}
            ]
        }

        instance = self.type('test', None, data)

        def find(template_uid, name):
            self.assertRegex(template_uid, self.type.VDCUSER_TEMPLATE)
            for user in data['users']:
                if name == user['name']:
                    u = mock.MagicMock()
                    u.schedule_action.return_value.result = name
                    return [u]
            raise ValueError('user not found')

        account = mock.MagicMock()

        # we set the account ACL to match the
        # configured data. this should has no
        # effect
        account.model = {
            'acl': [
                {'userGroupId': 'test1', 'right': 'ACDRUX'},
                {'userGroupId': 'test2', 'right': 'R'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(account)

        account.update_access.assert_not_called()
        account.authorize_user.assert_not_called()
        account.unauthorize_user.assert_not_called()

        account.reset_mock()
        # change the account model to force a change
        # account model is missing a user, we expect a call to authorize_user
        account.model = {
            'acl': [
                {'userGroupId': 'test2', 'right': 'R'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(account)

        account.update_access.assert_not_called()
        account.authorize_user.assert_called_once_with(username='test1', right='ACDRUX')
        account.unauthorize_user.assert_not_called()

        account.reset_mock()
        # change the account model to force a change
        # account model has an extra user, we expect a call to unauthorize_user
        account.model = {
            'acl': [
                {'userGroupId': 'test1', 'right': 'ACDRUX'},
                {'userGroupId': 'test2', 'right': 'R'},
                {'userGroupId': 'test3', 'right': 'R'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(account)

        account.update_access.assert_not_called()
        account.authorize_user.assert_not_called()
        account.unauthorize_user.assert_not_called()

        account.reset_mock()
        # change the account model to force a change
        # account model has a missmatching user, we expect a call to update_access
        account.model = {
            'acl': [
                {'userGroupId': 'test1', 'right': 'ACDRUX'},
                {'userGroupId': 'test2', 'right': 'ACDRUX'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(account)

        account.update_access.assert_called_once_with(username='test2', right='R')
        account.authorize_user.assert_not_called()
        account.unauthorize_user.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_add(self, openvcloud):
        data = {
            'users': [
                {'name': 'test1', 'accesstype': 'R'},
            ]
        }

        instance = self.type('test', None, data.copy())

        with self.assertRaises(StateCheckError):
            # fails if not installed
            instance.user_add({'name': 'test1', 'accesstype': 'R'})

        instance.state.set('actions', 'install', 'ok')
        with mock.patch.object(instance, '_authorize_users') as authorize:
            with mock.patch.object(instance, 'api') as api:
                api.services.find.return_value = [None]
                instance.user_add({'name': 'test1', 'accesstype': 'R'})

            authorize.assert_not_called()
            self.assertEqual(
                instance.data['users'],
                [
                    {'name': 'test1', 'accesstype': 'R'},
                ]
            )

        cl = openvcloud.get.return_value
        account = cl.account_get.return_value

        # Add a user that does not exist
        with mock.patch.object(instance, '_authorize_users') as authorize:
            with mock.patch.object(instance, 'api') as api:
                api.services.find.return_value = [None]
                instance.user_add({'name': 'test2'})

            authorize.assert_called_once_with(account)
            self.assertEqual(
                instance.data['users'], [
                    {'name': 'test1', 'accesstype': 'R'},
                    {'name': 'test2', 'accesstype': 'ACDRUX'},
                ])

        # Add a user that exists but with different accesstype
        with mock.patch.object(instance, '_authorize_users') as authorize:
            with mock.patch.object(instance, 'api') as api:
                api.services.find.return_value = [None]
                instance.user_add({'name': 'test2', 'accesstype': 'R'})

            authorize.assert_called_once_with(account)
            self.assertEqual(
                instance.data['users'], [
                    {'name': 'test1', 'accesstype': 'R'},
                    {'name': 'test2', 'accesstype': 'R'},
                ])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_delete(self, openvcloud):
        data = {
            'users': [
                {'name': 'test1', 'accesstype': 'R'},
            ]
        }

        instance = self.type('test', None, data)

        with self.assertRaises(StateCheckError):
            # fails if not installed
            instance.user_delete({'name': 'test1', 'accesstype': 'R'})

        # delete a user that does not exist
        instance.state.set('actions', 'install', 'ok')
        with mock.patch.object(instance, '_authorize_users') as authorize:
            instance.user_delete('test2')

            authorize.assert_not_called()
            self.assertEqual(
                instance.data['users'],
                [
                    {'name': 'test1', 'accesstype': 'R'},
                ]
            )

        cl = openvcloud.get.return_value
        account = cl.account_get.return_value

        # delete a user that exists
        with mock.patch.object(instance, '_authorize_users') as authorize:
            instance.user_delete('test1')

            account.unauthorize_user.assert_called_once_with(username='test1')
            self.assertEqual(
                instance.data['users'], [])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_update(self, openvcloud):
        cl = openvcloud.get.return_value
        account = cl.account_get.return_value
        account.model = {}

        instance = self.type('test', None, {})

        with self.assertRaises(StateCheckError):
            instance.update()

        instance.state.set('actions', 'install', 'ok')

        instance.update(
            maxMemoryCapacity=1,
            maxDiskCapacity=2,
            maxNumPublicIP=3
        )

        account.save.assert_called_once_with()

        self.assertEqual(account.model, {
            'maxMemoryCapacity': 1,
            'maxDiskCapacity': 2,
            'maxNumPublicIP': 3
        })