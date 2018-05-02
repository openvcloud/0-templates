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

        # def find(template_uid, name):
        #     self.assertEqual(template_uid, self.type.ACCOUNT_TEMPLATE)
        #     self.assertEqual(name, data['account'])

        #     result = mock.MagicMock()
        #     result.name = name
        #     return [result]

        # with mock.patch.object(instance, 'api') as api:
        #     api.services.find.side_effect = find
        #     instance.validate()

        # api.services.find.assert_called_once_with(template_uid=self.type.ACCOUNT_TEMPLATE, name=data['account'])

        # # Next, we test when NO connection is given
        # api.reset_mock()

        # data = {}
        # instance = self.type(name, None, data)

        # def find(template_uid, name):
        #     self.assertEqual(template_uid, self.type.ACCOUNT_TEMPLATE)
        #     self.assertEqual(name, None)

        #     result = mock.MagicMock()
        #     result.name = name
        #     return [result]

        # with patch.object(instance, 'api') as api:
        #     api.services.find.side_effect = find
        #     with self.assertRaises(ValueError):
        #         instance.validate()

        # api.services.find.assert_not_called()

        # # Finally, if the search retuned more than one object
        # api.reset_mock()

        # data = {
        #     'account': 'test-account'
        # }
        # instance = self.type(name, None, data)

        # def find(template_uid, name):
        #     self.assertEqual(template_uid, self.type.ACCOUNT_TEMPLATE)
        #     self.assertEqual(name, data['account'])

        #     result = mock.MagicMock()
        #     result.name = name
        #     return [result, result]  # return 2

        # with patch.object(instance, 'api') as api:
        #     api.services.find.side_effect = find
        #     with self.assertRaises(RuntimeError):
        #         instance.validate()

    #     # api.services.find.assert_called_once_with(template_uid=self.type.ACCOUNT_TEMPLATE, name=data['account'])

    # def test_validate(self):
    #     data = {
    #         'name' : 'vdcName',
    #         'account': 'test-account',
    #     }
    #     name = 'test'
    #     instance = self.type(name, None, data)

    #     def find(template_uid, name):
    #         if template_uid == self.type.ACCOUNT_TEMPLATE:
    #             # handle the connection search (tested in another test method)
    #             result = mock.MagicMock()
    #             result.name = 'test-account'
    #             return [result]

    #         result = mock.MagicMock()
    #         result.name = name
    #         return [result]

    #     with mock.patch.object(instance, 'api') as api:
    #         api.services.find.side_effect = find
    #         instance.validate()
    #     api.services.find.assert_has_calls(
    #         [
    #             mock.call(template_uid=self.type.ACCOUNT_TEMPLATE, name=data['account']),
    #         ]
    #     )

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

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, ovc):
        '''
        Test uninstall vdc
        '''
        # test error in read-only cloudspace
        data_read_only = {
            'account': 'test-account',
            'create': False,
            }
        instance = self.type('test', None, data_read_only)
        with pytest.raises(RuntimeError,
                           message='"%s" is readonly cloudspace' % instance.name):
            instance.uninstall()

        # test success
        data = {
            'account': 'test-account',
            }        

        instance = self.type('test', None, data)
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            instance.uninstall()
            instance.space.delete.assert_called_once_with()

        # test error if no ovc service was found
        instance = self.type('test', None, data)
        #instance.space.delete.reset_mock()
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            with pytest.raises(ValueError,
                               message='found 0 accounts with name "%s", required exactly one' % data['account']):
                instance.uninstall()      

    def test_user_authorize(self):
        '''
        Test authorizing a new user
        '''
        instance = self.type('test', None)

        # user to add
        vdcuser, accesstype, username = 'userTest', 'R', 'user@itsyouonline'
        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.user_authorize(vdcuser, accesstype)

        instance.state.set('actions', 'install', 'ok')
        with pytest.raises(ValueError,
                           message='no vdcuser service found with name "%s"' % vdcuser):
            # fails if no vdcuser service is running for this user
            instance.user_authorize(vdcuser, accesstype)

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock(
                return_value=MagicMock(result=username)))]
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

                # test fail
                ovc.return_value.account_get.return_value.space_get.return_value.authorize_user.return_value=False
                vdcuser, accesstype = 'userTest2', 'R'
                with pytest.raises(RuntimeError,
                                   message='failed to add user "%s"' % username):
                    instance.user_authorize(vdcuser, accesstype)

    def test_user_update_access_right(self):
        '''
        Test updating access right of an authorized user
        '''
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                # new accesstype update
                vdcuser = 'userTest'
                accesstype = 'RCX'

                # test success
                ovc.return_value.account_get.return_value.space_get.return_value.update_access.return_value=True
                instance.user_authorize(vdcuser, accesstype)
                instance.space.update_access.assert_called_once_with(username=self.initial_user['name'], right=accesstype)
                self.assertEqual(instance.data['users'],
                                [{'name': 'test1', 'accesstype': 'RCX'}])

                # test fail
                ovc.return_value.account_get.return_value.space_get.return_value.update_access.return_value=False
                with pytest.raises(RuntimeError,
                                   message='failed to update accesstype of user "test1"'):
                    instance.user_add(user)

    def test_user_delete(self):
        '''
        Test deleting a user
        '''
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')
        
        users = [{'userGroupId': 'test1', 'right': 'R'}]

        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
                # user to delete
                username = 'test1'

                # test success
                ovc.return_value.account_get.return_value.space_get.return_value.unauthorize_user.return_value=True
                ovc.return_value.account_get.return_value.space_get.return_value.model = {'acl': users}
                instance.user_delete(username)
                instance.space.unauthorize_user.assert_called_once_with(username=username)
                self.assertEqual(instance.data['users'], [])

                # test fail
                ovc.return_value.account_get.return_value.space_get.return_value.unauthorize_user.return_value=False
                with pytest.raises(RuntimeError,
                                   message='failed to update accesstype of user "test1"'):
                    instance.user_delete(username)

    def test_update(self):
        '''
        Test updating vdc limits
        '''
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
