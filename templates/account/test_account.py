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

    def test_state_check(self):
        """
        Test state check
        """
        instance = self.type('test', None)
        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.state.check('actions', 'install', 'ok')
        
        # success
        instance.state.set('actions', 'install', 'ok')
        instance.state.check('actions', 'install', 'ok')

    def test_validate_openvcloud(self):
        data = {
            'openvcloud': 'connection',
            'name': 'test_account',
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
            'openvcloud': 'connection',
            'name': 'test_account',
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
        """
        Test validate method
        """
        data = {
            'openvcloud': 'connection',
            'name': 'test_account',
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
            'name': 'test_account',
        }
        connection_name = 'be-gen'
        name = 'test'
        instance = self.type(name, None, data)

        # mock finding services
        def find(template_uid, name): 
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, data['openvcloud'])    
            task_mock = MagicMock(result=connection_name)
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.install()

        openvcloud.get.assert_called_once_with(connection_name)

        cl = openvcloud.get.return_value
        cl.account_get.assert_called_once_with(
            name=data['name'],
            create=True,
            # default values
            maxMemoryCapacity=-1,
            maxVDiskCapacity=-1,
            maxCPUCapacity=-1,
            maxNumPublicIP=-1,
        )

        account = cl.account_get.return_value
        account.save.assert_called_once_with()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_success(self, ovc):
        """
        Test uninstall account
        """

        data = {
            'openvcloud': 'connection',
            'name': 'test_account',
            }

        account = ovc.get.return_value.account_get.return_value
        instance = self.type('test', None, data)
        with mock.patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock()]        
            instance.uninstall()
        account.delete.assert_called_once_with()     

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_fail(self, ovc):
        """
        Test uninstall account
        """
        # test error in read-only cloudspace
        data_read_only = {
            'openvcloud': 'connection',
            'name': 'test_account',
            'create': False,
            }
        instance = self.type('test', None, data_read_only)

        with pytest.raises(RuntimeError,
                           message='"%s" is readonly cloudspace' % instance.name):
            instance.uninstall()
   

    def test_update_statecheckerror(self):
        instance = self.type('test', None, {})
        with self.assertRaises(StateCheckError):
            # fails if account not installed
            instance.update()
        

    @mock.patch.object(j.clients, '_openvcloud')
    def test_update(self, openvcloud):
        """
        Test updating account limits
        """
        instance = self.type('test', None, {})
        instance.state.set('actions', 'install', 'ok')
        cl = openvcloud.get.return_value
        account = cl.account_get.return_value
        account.model = {}

        with mock.patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock()]
            instance.update(
                maxMemoryCapacity=1,
                maxVDiskCapacity=2,
                maxNumPublicIP=3
            )

        account.save.assert_called_once_with()
        self.assertEqual(account.model, {
            'maxMemoryCapacity': 1,
            'maxVDiskCapacity': 2,
            'maxNumPublicIP': 3
        })

    def test_user_authorize_statecheckerror(self):
        instance = self.type('test', None)
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}
        with pytest.raises(StateCheckError):
            # fails if account not installed
            instance.user_authorize(user['vdcuser'], user['accesstype'])

    def test_user_authorize_success(self):
        """
        Test authorizing a new user
        """
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}

        with pytest.raises(ValueError,
                           message='no vdcuser service found with name "%s"' % user['vdcuser']):
            # fails if no vdcuser service is running for this user
            instance.user_authorize(user['vdcuser'], user['accesstype'])

        # mock finding services
        def find(template_uid, name):     
            task_mock = MagicMock(result=user['user_name'])
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:           
                # test success
                ovc.return_value.account_get.return_value.authorize_user.return_value=True
                instance.user_authorize(user['vdcuser'], user['accesstype'])

                instance.account.authorize_user.assert_called_once_with(
                    username=user['user_name'],
                    right=user['accesstype'])
                api.services.find.assert_has_calls(
                    [mock.call(template_uid=self.type.VDCUSER_TEMPLATE, name=user['vdcuser'])]
                )
                self.assertEqual(
                    instance.data['users'],
                    [
                        {'name': user['user_name'],
                        'accesstype': user['accesstype']}
                    ])
                ovc.return_value.account_get.return_value.authorize_user.return_value=False
                # user = {'vdcuser': 'test2', 'accesstype': 'R'}
                with pytest.raises(RuntimeError,
                                message='failed to add user "%s"' % user['user_name']):
                    instance.user_authorize(user['vdcuser'], user['accesstype'])

    def test_user_authorize_fail(self):
        """
        Test authorizing a new user
        """
        instance = self.type('test', None)

        # user to add
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}

        instance.state.set('actions', 'install', 'ok')
        with pytest.raises(ValueError,
                           message='no vdcuser service found with name "%s"' % user['vdcuser']):
            # fails if no vdcuser service is running for this user
            instance.user_authorize(user['vdcuser'], user['accesstype'])

        # mock finding services
        def find(template_uid, name):     
            task_mock = MagicMock(result=user['user_name'])
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:           
                # test success
                ovc.return_value.account_get.return_value.authorize_user.return_value=False
                with pytest.raises(RuntimeError,
                                message='failed to add user "%s"' % user['user_name']):
                    instance.user_authorize(user['vdcuser'], user['accesstype'])

    def test_user_update_access_right_success(self):
        """
        Test updating access right of an authorized user
        """
        instance = self.type('test', None)
        # user to update
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}
        users = [{'userGroupId': user['user_name'], 'right': 'R'}]

        with pytest.raises(StateCheckError):
            # fails if account not installed
            instance.user_authorize(user['vdcuser'], user['accesstype'])

        instance.state.set('actions', 'install', 'ok')

        # mock finding services
        def find(template_uid, name):     
            task_mock = MagicMock(result=user['user_name'])
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find #[MagicMock(schedule_action=MagicMock())]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                # test success
                ovc.return_value.account_get.return_value.update_access.return_value=True
                ovc.return_value.account_get.return_value.model = {'acl': users}
                instance.user_authorize(user['vdcuser'], user['accesstype'])
                instance.account.update_access.assert_called_once_with(username=user['user_name'], right=user['accesstype'])

    def test_user_update_access_right_fail(self):
        """
        Test updating access right of an authorized user
        """
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')
        # user to update
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}
        users = [{'userGroupId': user['user_name'], 'right': 'R'}]

        # mock finding services
        def find(template_uid, name):     
            task_mock = MagicMock(result=user['user_name'])
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find #[MagicMock(schedule_action=MagicMock())]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                ovc.return_value.account_get.return_value.update_access.return_value=False
                ovc.return_value.account_get.return_value.model = {'acl': users}
                with pytest.raises(RuntimeError,
                                message='failed to update accesstype of user "test1"'):
                    instance.user_authorize(user['vdcuser'], user['accesstype'])

    def test_user_unauthorize_statecheckerror(self):
        instance = self.type('test', None)
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}       
        with pytest.raises(StateCheckError):
            # fails if account not installed
            instance.user_authorize(user['vdcuser'])

    def test_user_unauthorize_success(self):
        """
        Test deleting a user success
        """        
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        users = [{'userGroupId': 'user@provider', 'right': 'R'}]
        # user to delete
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}

        # mock finding services
        def find(template_uid, name):     
            task_mock = MagicMock(result=user['user_name'])
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:

                # test success
                ovc.return_value.account_get.return_value.unauthorize_user.return_value=True
                ovc.return_value.account_get.return_value.model = {'acl': users}

                instance.user_unauthorize(vdcuser=user['vdcuser'])
                instance.account.unauthorize_user.assert_called_once_with(username=user['user_name'])
                self.assertEqual(instance.data['users'], [])

    def test_user_unauthorize_fail(self):
        """
        Test deleting a user fail
        """        
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        users = [{'userGroupId': 'user@provider', 'right': 'R'}]
        # user to delete
        user = {'vdcuser': 'test1', 'accesstype': 'W', 'user_name': 'user@provider'}

        # mock finding services
        def find(template_uid, name):     
            task_mock = MagicMock(result=user['user_name'])
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                ovc.return_value.account_get.return_value.unauthorize_user.return_value=False
                ovc.return_value.account_get.return_value.model = {'acl': users}
                with pytest.raises(RuntimeError,
                                   message='failed to remove user "%s"' % user['vdcuser']):
                    instance.user_unauthorize(vdcuser=user['vdcuser'])
