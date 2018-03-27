from js9 import j
import os

from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
import pytest

from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestAccount(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

        # define properties of account mock
        acc_mock =  MagicMock(model={'acl': []})
        self.ovc_mock = MagicMock(account_get=MagicMock(return_value=acc_mock))        

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

        # Finally, if the search returned more than one object
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

    def test_validate(self):
        '''
        Test validate method
        '''
        data = {
            'openvcloud': 'connection',
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

            result = mock.MagicMock()
            result.name = name
            return [result]

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.validate()

        api.services.find.assert_has_calls(
            [mock.call(template_uid=self.type.OVC_TEMPLATE, name=data['openvcloud'])]
        )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, openvcloud):
        data = {
            'openvcloud': 'connection',
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

    def test_user_add(self):
        '''
        Test authorizing a new user
        '''
        instance = self.type('test', None)

        # user to add
        user = {'name': 'test1', 'accesstype': 'R'}
        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.user_add(user)

        instance.state.set('actions', 'install', 'ok')
        with pytest.raises(ValueError,
                           message='no account service found with name "%s"' % user['name']):
            # fails if no account service is running for this user
            instance.user_add(user)

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:               
                # test success
                ovc.return_value.account_get.return_value.authorize_user.return_value=True
                instance.user_add(user)
                instance.account.authorize_user.assert_called_once_with(username=user['name'], right=user['accesstype'])
                api.services.find.assert_has_calls(
                    [mock.call(template_uid=self.type.VDCUSER_TEMPLATE, name=user['name'])]
                )

                self.assertEqual(instance.data['users'], [user])

                # test fail
                ovc.return_value.account_get.return_value.authorize_user.return_value=False
                user = {'name': 'test2', 'accesstype': 'R'}
                with pytest.raises(RuntimeError,
                                   message='failed to add user "%s"' % user['name']):
                    instance.user_add(user)

    def test_user_update_access_right(self):
        '''
        Test updating access right of an authorized user
        '''
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                users = [{'userGroupId': 'test1', 'right': 'R'}]
                # user to update
                user = {'name': 'test1', 'accesstype': 'W'}

                # test success
                ovc.return_value.account_get.return_value.update_access.return_value=True
                ovc.return_value.account_get.return_value.model = {'acl': users}
                instance.user_add(user)
                instance.account.update_access.assert_called_once_with(username=user['name'], right=user['accesstype'])
                self.assertEqual(instance.data['users'],
                                [{'name': 'test1', 'accesstype': 'W'}])

                # test fail
                ovc.return_value.account_get.return_value.update_access.return_value=False
                with pytest.raises(RuntimeError,
                                   message='failed to update accesstype of user "test1"'):
                    instance.user_add(user)


    def test_user_delete(self):
        '''
        Test deleting a user
        '''        
        instance = self.type('test', None)

        users = [{'userGroupId': 'test1', 'right': 'R'}]
        
        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                # user to delete
                username = 'test1'

                # test success
                ovc.return_value.account_get.return_value.unauthorize_user.return_value=True
                ovc.return_value.account_get.return_value.model = {'acl': users}
                instance.user_delete(username)
                instance.account.unauthorize_user.assert_called_once_with(username=username)
                self.assertEqual(instance.data['users'], [])

                # test fail
                ovc.return_value.account_get.return_value.unauthorize_user.return_value=False
                with pytest.raises(RuntimeError,
                                   message='failed to remove user "%s"' % username):
                    instance.user_delete(username)
                
                # test deliting nonexistent user
                instance.account.unauthorize_user.reset_mock()
                nonexistent_username = 'nonexistent_username'
                with pytest.raises(RuntimeError,
                                   message='user "%s" is not found' % nonexistent_username):
                    instance.user_delete(nonexistent_username)

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

    def test_validate_args(self):
        tt = [
            {
                "data": {"description" : "dummy value"},
                "valid": True,
                "msg": "description is a valid argument",
            },
            {
                "data": {"openvcloud" : "dummy value"},
                "valid": True,
                "msg": "openvcloud is a valid argument",
            },
            {
                "data": {"users" : "dummy value"},
                "valid": True,
                "msg": "users is a valid argument",
            },
            {
                "data": {"accountID" : "dummy value"},
                "valid": True,
                "msg": "accountID is a valid argument",
            },
            {
                "data": {"maxMemoryCapacity" : "dummy value"},
                "valid": True,
                "msg": "maxMemoryCapacity is a valid argument",
            },
            {
                "data": {"maxCPUCapacity" : "dummy value"},
                "valid": True,
                "msg": "maxCPUCapacity is a valid argument",
            },
            {
                "data": {"maxNumPublicIP" : "dummy value"},
                "valid": True,
                "msg": "maxNumPublicIP is a valid argument",
            },
            {
                "data": {"maxDiskCapacity" : "dummy value"},
                "valid": True,
                "msg": "maxDiskCapacity is a valid argument",
            },
            {
                "data": {"consumptionFrom" : "dummy value"},
                "valid": True,
                "msg": "consumptionFrom is a valid argument",
            },
            {
                "data": {"consumptionTo" : "dummy value"},
                "valid": True,
                "msg": "consumptionTo is a valid argument",
            },
            {
                "data": {"consumptionData" : "dummy value"},
                "valid": True,
                "msg": "consumptionData is a valid argument",
            },
            {
                "data": {"create" : "dummy value"},
                "valid": True,
                "msg": "create is a valid argument",
            },
            {
                "data": {"consumptionData" : "dummy value", "description" : "dummy value"},
                "valid": True,
                "msg": "consumptionData and description are valid arguments",
            },
            {
                "data": {"foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
            {
                "data": {"openwcloud" : "dummy value"},
                "valid": False,
                "msg": "openwcloud is an invalid argument",
            },
            {
                "data": {"maxDiskCapacit" : "dummy value"},
                "valid": False,
                "msg": "maxDiskCapacit is an invalid argument",
            },
            {
                "data": {"openvcloud" : "dummy value", "foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
        ]

        name = 'test'
        instance = self.type(name)

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
