from js9 import j
import os

from unittest import TestCase
from unittest import mock

from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestVDC(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

    def test_validate_account(self):
        data = {
            'account': 'test-account',
        }
        name = 'test'
        instance = self.type(name, None, data)

        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.ACCOUNT_TEMPLATE)
            self.assertEqual(name, data['account'])

            result = mock.MagicMock()
            result.name = name
            return [result]

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.validate()

        api.services.find.assert_called_once_with(template_uid=self.type.ACCOUNT_TEMPLATE, name=data['account'])

        # Next, we test when NO connection is given
        api.reset_mock()

        data = {}
        instance = self.type(name, None, data)

        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.ACCOUNT_TEMPLATE)
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
            'account': 'test-account'
        }
        instance = self.type(name, None, data)

        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.ACCOUNT_TEMPLATE)
            self.assertEqual(name, data['account'])

            result = mock.MagicMock()
            result.name = name
            return [result, result]  # return 2

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaises(RuntimeError):
                instance.validate()

        api.services.find.assert_called_once_with(template_uid=self.type.ACCOUNT_TEMPLATE, name=data['account'])

    def test_validate_users(self):
        data = {
            'account': 'test-account',
            'users': [
                {'name': 'test-user'},
            ]
        }
        name = 'test'
        instance = self.type(name, None, data)

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                # handle the connection search (tested in another test method)
                result = mock.MagicMock()
                result.name = 'test-account'
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
                mock.call(template_uid=self.type.ACCOUNT_TEMPLATE, name=data['account']),
                mock.call(template_uid=self.type.VDCUSER_TEMPLATE, name=data['users'][0]['name'])
            ]
        )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, openvcloud):
        data = {
            'account': 'test-account',
        }
        name = 'test'
        instance = self.type(name, None, data)

        # we will do it this way
        with mock.patch.object(instance, '_account') as account:
            space = account.space_get.return_value
            space.model = {
                'id': 'space-id',
                'acl': [],
                'status': 'DEPLOYED'
            }

            instance.install()
            account.space_get.assert_called_once_with(
                name=name,
                create=True,
                maxMemoryCapacity=-1,
                maxVDiskCapacity=-1,
                maxCPUCapacity=-1,
                maxNumPublicIP=-1,
                maxNetworkPeerTransfer=-1,
                externalnetworkId=None
            )
            self.assertEqual(space.model, {
                'id': 'space-id',
                'acl': [],
                'maxMemoryCapacity': -1,
                'maxVDiskCapacity': -1,
                'maxNumPublicIP': -1,
                'maxCPUCapacity': -1,
                'maxNetworkPeerTransfer': -1,
                'status': 'DEPLOYED'
            })

            space.save.assert_called_once_with()

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

        space = mock.MagicMock()

        # we set the account ACL to match the
        # configured data. this should has no
        # effect
        space.model = {
            'acl': [
                {'userGroupId': 'test1', 'right': 'ACDRUX'},
                {'userGroupId': 'test2', 'right': 'R'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(space)

        space.update_access.assert_not_called()
        space.authorize_user.assert_not_called()
        space.unauthorize_user.assert_not_called()

        space.reset_mock()
        # change the account model to force a change
        # account model is missing a user, we expect a call to authorize_user
        space.model = {
            'acl': [
                {'userGroupId': 'test2', 'right': 'R'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(space)

        space.update_access.assert_not_called()
        space.authorize_user.assert_called_once_with(username='test1', right='ACDRUX')
        space.unauthorize_user.assert_not_called()

        space.reset_mock()
        # change the account model to force a change
        # account model has an extra user, we expect a call to unauthorize_user
        space.model = {
            'acl': [
                {'userGroupId': 'test1', 'right': 'ACDRUX'},
                {'userGroupId': 'test2', 'right': 'R'},
                {'userGroupId': 'test3', 'right': 'R'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(space)

        space.update_access.assert_not_called()
        space.authorize_user.assert_not_called()
        space.unauthorize_user.assert_called_once_with(username='test3')

        space.reset_mock()
        # change the account model to force a change
        # account model has a missmatching user, we expect a call to update_access
        space.model = {
            'acl': [
                {'userGroupId': 'test1', 'right': 'ACDRUX'},
                {'userGroupId': 'test2', 'right': 'ACDRUX'},
            ]
        }

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance._authorize_users(space)

        space.update_access.assert_called_once_with(username='test2', right='R')
        space.authorize_user.assert_not_called()
        space.unauthorize_user.assert_not_called()

    def test_user_add(self):
        data = {
            'users': [
                {'name': 'test1', 'accesstype': 'R'},
            ]
        }

        instance = self.type('test', None, data)

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

        # Add a user that does not exist
        with mock.patch.object(instance, '_authorize_users') as authorize:
            with mock.patch.object(instance, 'api') as api:
                api.services.find.return_value = [None]
                with mock.patch.object(instance, '_account') as account:
                    space = account.space_get.return_value
                    instance.user_add({'name': 'test2'})
                    authorize.assert_called_once_with(space)

            self.assertEqual(
                instance.data['users'], [
                    {'name': 'test1', 'accesstype': 'R'},
                    {'name': 'test2', 'accesstype': 'ACDRUX'},
                ])

        # Add a user that exists but with different accesstype
        with mock.patch.object(instance, '_authorize_users') as authorize:
            with mock.patch.object(instance, 'api') as api:
                api.services.find.return_value = [None]
                with mock.patch.object(instance, '_account') as account:
                    space = account.space_get.return_value
                    instance.user_add({'name': 'test2', 'accesstype': 'R'})

            authorize.assert_called_once_with(space)
            self.assertEqual(
                instance.data['users'], [
                    {'name': 'test1', 'accesstype': 'R'},
                    {'name': 'test2', 'accesstype': 'R'},
                ])

    def test_user_delete(self):
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

        # delete a user that exists
        with mock.patch.object(instance, '_authorize_users') as authorize:
            with mock.patch.object(instance, '_account') as account:
                space = account.space_get.return_value
                instance.user_delete('test1')

                authorize.assert_called_once_with(space)
            self.assertEqual(
                instance.data['users'], [])

    def test_update(self):
        instance = self.type('test', None, {})

        with self.assertRaises(StateCheckError):
            instance.update()

        instance.state.set('actions', 'install', 'ok')

        with mock.patch.object(instance, '_account') as account:
            space = account.space_get.return_value
            space.model = {}
            instance.update(
                maxMemoryCapacity=1,
                maxDiskCapacity=2,
                maxNumPublicIP=3,
                maxCPUCapacity=4
            )

            space.save.assert_called_once_with()

            self.assertEqual(space.model, {
                'maxMemoryCapacity': 1,
                'maxDiskCapacity': 2,
                'maxNumPublicIP': 3,
                'maxCPUCapacity': 4
            })
