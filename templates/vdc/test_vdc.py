from js9 import j
import os

from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
import pytest

from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestVDC(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )
        # define properties of space mock
        self.initial_user = {'name': 'initial_user@itsyouonline', 'accesstype': 'ACDRUX'}
        space_mock = MagicMock(model={
            'acl': [{
                'userGroupId': self.initial_user['name'], 
                'right': self.initial_user['accesstype']}
                ]}
            )
        acc_mock = MagicMock(space_get=MagicMock(return_value=space_mock))
        self.ovc_mock = MagicMock(account_get=MagicMock(return_value=acc_mock))        

    def test_validate(self):
        # test fail if name is missing        
        name = 'test'
        data = {
            'account': 'test-account',
        }
        instance = self.type(name, None, data)
        with pytest.raises(ValueError,
                           message="vdc name is required"):
            instance.validate()

        # test fail if account is missing        
        data = {
            'account': 'test-account',
        }
        instance = self.type(name, None, data)
        with pytest.raises(ValueError,
                           message="account service name is required"):
            instance.validate()

        # test success
        data = {
            'name': 'vdc_name',
            'account': 'test-account',
        }
        instance = self.type(name, None, data)
        instance.validate()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, openvcloud):
        name = 'test'
        data = {
            'account': 'account-service-name',
            'name': name
        }
        instance = self.type(name, None, data)

        account_name = 'be-gen'
        def find(template_uid, name): 
            self.assertEqual(template_uid, self.type.ACCOUNT_TEMPLATE)
            self.assertEqual(name, data['account'])
            task_mock = MagicMock(result=account_name)
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        # we will do it this way
        with mock.patch.object(instance, '_account') as account:
            space = account.space_get.return_value
            space.model = {
                'id': 'space-id',
                'acl': [],
                'status': 'DEPLOYED'
            }
            with mock.patch.object(instance, 'api') as api:
                instance.api.find.side_effect = find
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

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_success(self, ovc):
        """
        Test uninstall vdc
        """

        data = {
            'account': 'test-account',
            }        

        instance = self.type('test', None, data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            instance.uninstall()
            instance.space.delete.assert_called_once_with()
        with pytest.raises(StateCheckError):
            instance.state.check('actions', 'install', 'ok')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_fail_read_only_account(self, ovc):
        """
        Test uninstall vdc. Test error in read-only cloudspace
        """
        
        data_read_only = {
            'account': 'test-account',
            'create': False,
            }
        instance = self.type('test', None, data_read_only)
        with pytest.raises(RuntimeError,
                           message='"%s" is readonly cloudspace' % instance.name):
            instance.uninstall()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_fail_no_account(self, ovc):
        """
        Test uninstall vdc if no ovc service was found
        """

        data = {
            'account': 'test-account',
            }        

        instance = self.type('test', None, data)


        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            with pytest.raises(RuntimeError,
                               message='found 0 services with name "%s", required exactly one' % data['account']):
                instance.uninstall()      

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


    def test_user_authorize_success(self):
        """
        Test authorizing a new user
        """

        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        vdcuser, accesstype, username = 'test_user', 'R', 'user@itsyouonline'

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = [[MagicMock()], [MagicMock()],
                                              [MagicMock(schedule_action=MagicMock(
                                                         return_value=MagicMock(result=username)))]]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                
                # test success
                ovc.return_value.account_get.return_value.space_get.return_value.authorize_user.return_value=True
                instance.user_authorize(vdcuser, accesstype)
                instance.space.authorize_user.assert_called_once_with(username=username, right=accesstype)
                api.services.find.assert_has_calls(
                    [mock.call(template_uid=self.type.VDCUSER_TEMPLATE, name=vdcuser)]
                )

                self.assertEqual(
                    instance.data['users'],
                    [self.initial_user, {'name': username, 'accesstype': accesstype}]
                    )

    def test_user_authorize_fail_no_vdcuser_service(self):
        """
        Test authorizing a new user
        """

        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')
        
        # user to add
        vdcuser, accesstype, username = 'test_user', 'R', 'user@itsyouonline'
        users = [{'userGroupId': username, 'right': 'R'}]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = [[MagicMock()],[MagicMock()], []]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:

                with pytest.raises(RuntimeError,
                                   message='found 0 services with name "%s", required exactly one' % vdcuser):

                    # fails if no vdcuser service is running for this user
                    instance.user_authorize(vdcuser, accesstype)

    def test_user_authorize_fail_adding_user(self):
        """
        Test authorizing a new user
        """

        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        vdcuser, accesstype, username = 'test_user', 'R', 'user@itsyouonline'

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = [[MagicMock()], [MagicMock()], 
                                             [MagicMock(schedule_action=MagicMock(
                                                        return_value=MagicMock(result=username)))]]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                # test fail
                ovc.return_value.account_get.return_value.space_get.return_value.authorize_user.return_value=False
                vdcuser, accesstype = 'userTest2', 'R'
                with pytest.raises(RuntimeError,
                                   message='failed to add user "%s"' % username):
                    instance.user_authorize(vdcuser, accesstype)

    def test_user_update_access_right_success(self):
        """
        Test updating access right of an authorized user
        """
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        # user to update
        vdcuser = 'test_user'
        username = self.initial_user['name']
        accesstype = 'W'
        #users = [{'userGroupId': username, 'right': accesstype}]
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = [[MagicMock()], [MagicMock()], 
                                             [MagicMock(schedule_action=MagicMock(
                                                        return_value=MagicMock(result=username)))]]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:

                # test success
                ovc.return_value.account_get.return_value.space_get.return_value.update_access.return_value=True
                instance.user_authorize(vdcuser, accesstype)
                instance.space.update_access.assert_called_once_with(username=username, right=accesstype)
                self.assertEqual(instance.data['users'],
                                [{'name': username, 'accesstype': 'W'}])

    def test_user_update_access_right_fail(self):
        """
        Test updating access right of an authorized user
        """
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        # user to update
        vdcuser = 'test_user'
        username = self.initial_user['name']
        accesstype = 'W'
        #users = [{'userGroupId': username, 'right': accesstype}]
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = [[MagicMock()], [MagicMock()], 
                                             [MagicMock(schedule_action=MagicMock(
                                                        return_value=MagicMock(result=username)))]]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                ovc.return_value.account_get.return_value.space_get.return_value.update_access.return_value=False
                with pytest.raises(RuntimeError,
                                   message='failed to update accesstype of user "test1"'):
                    instance.user_authorize(vdcuser, accesstype)


    def test_user_unauthorize(self):
        """
        Test deleting a user
        """
        data = {
            'name': 'vdc_name',
            'account': 'test-account',
        }
        
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')
        
        # user to delete
        username = 'user@provider'
        vdcuser = 'service_name'
        users = [{'userGroupId': username, 'right': 'R'}]

        # mock finding services
        def find(template_uid, name):
            task_mock = MagicMock(result=username)
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                # test success
                ovc.return_value.account_get.return_value.space_get.return_value.unauthorize_user.return_value=True
                ovc.return_value.account_get.return_value.space_get.return_value.model = {'acl': users}

                instance.user_unauthorize(vdcuser)
                instance.space.unauthorize_user.assert_called_once_with(username=username)
                self.assertEqual(instance.data['users'], [])

                # test fail
                ovc.return_value.account_get.return_value.space_get.return_value.unauthorize_user.return_value=False
                with pytest.raises(RuntimeError,
                                   message='failed to remove user "%s"' % username):
                    instance.user_unauthorize(vdcuser)

    def test_update(self):
        """
        Test updating vdc limits
        """
        instance = self.type('test', None, {})

        with self.assertRaises(StateCheckError):
            instance.update()

        instance.state.set('actions', 'install', 'ok')

        with mock.patch.object(instance, '_account') as account:
            space = account.space_get.return_value
            space.model = {}
            instance.update(
                maxMemoryCapacity=1,
                maxVDiskCapacity=25,
                maxNumPublicIP=3,
                maxCPUCapacity=4
            )

            space.save.assert_called_once_with()

            self.assertEqual(space.model, {
                'maxMemoryCapacity': 1,
                'maxVDiskCapacity': 25,
                'maxNumPublicIP': 3,
                'maxCPUCapacity': 4
            })
