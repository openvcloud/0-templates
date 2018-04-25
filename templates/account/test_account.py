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

        self.ovc = {'service': 'test_ovc_service',
                    'info': {'name': 'connection_instance_name'}
                    }
        self.acc = {'service': 'test_account_service',
                    'info': {'name': 'test_account',
                             'openvcloud': self.ovc['service']}
                    }
        self.vdcuser = {'service': 'test_vdcuser_service',
                        'base_name': 'test_vdcuser',
                        'accesstype': 'R',
                        'info': {'name': 'test_vdcuser@itsyouonline',
                        'openvcloud': self.ovc['service']}
                        }                    

    def tearDown(self):
        patch.stopall()

    @staticmethod
    def set_up_proxy_mock(result=None, state='ok', name='service_name'):
        task = MagicMock(result=result, state=state)
        proxy = MagicMock(schedule_action=MagicMock(return_value=task))
        proxy.name = name
        return proxy

    def find(self, template_uid, name):
        if template_uid == self.type.OVC_TEMPLATE:
            self.assertEqual(name, self.ovc['service'])
            proxy = self.set_up_proxy_mock(result=self.ovc['info'])
        if template_uid == self.type.VDCUSER_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.vdcuser['info'])        
        return [proxy]

    def ovc_mock(self, instance):
        acc_mock = MagicMock(model={'acl': [{'userGroupId': self.vdcuser['info']['name'],
                                             'right': self.vdcuser['accesstype']}],
                                    'id': 111, 'name': self.acc['info']['name']},
                                    )
        ovc = MagicMock(account_get=MagicMock(return_value=acc_mock))
        ovc.accounts = [acc_mock]
        return ovc

    def test_validate_success(self):
        data = self.acc['info']
        name = 'test'
        instance = self.type(name, None, data)
        instance.validate()

    def test_validate_fail_missing_name(self):
        data = {}
        name = 'test'
        instance = self.type(name, None, data)
        
        with self.assertRaisesRegex(ValueError,
                                     '"name" is required'):
            instance.validate()

    def test_validate_fail_missing_ovc(self):
        data = {'name': 'account_name'}
        name = 'test'
        instance = self.type(name, None, data)
        
        with self.assertRaisesRegex(ValueError,
                                     '"openvcloud" is required'):
            instance.validate()
    
    @mock.patch.object(j.clients, '_openvcloud')
    def test_ovc_success(self, ovc):
        """ Test ovc client getter """
        data = self.acc['info']
        instance = self.type('test', None, data)
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.ovc

    @mock.patch.object(j.clients, '_openvcloud')
    def test_ovc_fail_missing_ovc_service(self, ovc):
        """ Test ovc client getter """
        data = self.acc['info']
        instance = self.type('test', None, data)
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = []
            with self.assertRaisesRegex(RuntimeError,
                                        'found 0 services with name "%s", required exactly one' %
                                        self.ovc['service']):
                instance.ovc

    @mock.patch.object(j.clients, '_openvcloud')
    def test_ovc_fail_get_info(self, ovc):
        """ Test ovc client getter """
        data = self.acc['info']
        instance = self.type('test', None, data)
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [
                self.set_up_proxy_mock(state='error', name=self.ovc['service'])
                ]
            with self.assertRaisesRegex(RuntimeError,
                                        'error occurred when executing action "get_info" on service "%s"' %
                                        self.ovc['service']):
                instance.ovc

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, ovc):
        data = self.acc['info']
        instance = self.type('test', None, data)

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.install()

        ovc.get.assert_called_once_with(self.ovc['info']['name'])

        cl = ovc.get.return_value
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
    def test_uninstall_nonexistent_account(self, ovc):
        """
        Test uninstall account
        """
        data = self.acc['info']
        instance = self.type('test', None, data)

        # if account doesn't exist on ovc do nothing
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        client.accounts = []

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.uninstall()

        account = client.account_get.return_value
        account.delete.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_success(self, ovc):
        """
        Test uninstall account
        """
        data = self.acc['info']
        instance = self.type('test', None, data)

        # if account doesn't exist on ovc do nothing
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        account.spaces = []
        
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find

            instance.uninstall()
        account.delete.assert_called_once_with()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_fail_not_empty(self, ovc):
        """
        Test uninstall account
        """
        data = self.acc['info']
        instance = self.type('test', None, data)

        # if account doesn't exist on ovc do nothing
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            with self.assertRaisesRegex(RuntimeError,
                                        'not empty account cannot be deleted'):
                instance.uninstall()
        account.delete.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_fail_read_only(self, ovc):
        """
        Test uninstall account
        """
        data = self.acc['info']
        data['create'] = False
        instance = self.type('test', None, data)

        # if account doesn't exist on ovc do nothing
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            with self.assertRaisesRegex(RuntimeError,
                                        'readonly account'):
                instance.uninstall()
        account.delete.assert_not_called()

    def test_update_statecheckerror(self):
        instance = self.type('test', None, {})
        with self.assertRaises(StateCheckError):
            # fails if account not installed
            instance.update()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_update(self, ovc):
        """
        Test updating account limits
        """
        data = self.acc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        cl = ovc.get.return_value
        account = cl.account_get.return_value
        account.model = {}

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
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
        user = {'vdcuser': 'test1', 'accesstype': 'W',
                'user_name': 'user@provider'}
        with pytest.raises(StateCheckError):
            # fails if account not installed
            instance.user_authorize(user['vdcuser'], user['accesstype'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_success(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.acc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        user = {'vdcuser': self.vdcuser['service'], 
                'accesstype': 'W',
                'user_name': self.vdcuser['info']['name']}

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        account.model = {'acl': []}
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.user_authorize(user['vdcuser'], user['accesstype'])

            instance.account.authorize_user.assert_called_once_with(
                username=user['user_name'],
                right=user['accesstype'])
            api.services.find.assert_has_calls(
                [mock.call(template_uid=self.type.VDCUSER_TEMPLATE,
                            name=user['vdcuser'])]
            )
            self.assertEqual(
                instance.data['users'],
                [
                    {'name': user['user_name'],
                        'accesstype': user['accesstype']}
                ])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_fail(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.acc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')
        # user to add
        user = {'vdcuser': self.vdcuser['service'], 
                'accesstype': 'W',
                'user_name': self.vdcuser['base_name']}

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        account.model = {'acl': []}
        account.authorize_user.return_value = False
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            with self.assertRaisesRegex(RuntimeError, 
                                        'failed to add user "%s"' %
                                        self.vdcuser['info']['name']):
                instance.user_authorize(user['vdcuser'], user['accesstype'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_update_access_right_success(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.acc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        user = {'vdcuser': self.vdcuser['service'], 
                'accesstype': 'W',
                'user_name': self.vdcuser['info']['name']}

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.user_authorize(user['vdcuser'], user['accesstype'])

            instance.account.update_access.assert_called_once_with(
                username=user['user_name'],
                right=user['accesstype'])
            api.services.find.assert_has_calls(
                [mock.call(template_uid=self.type.VDCUSER_TEMPLATE,
                            name=user['vdcuser'])]
            )
            self.assertEqual(
                instance.data['users'],
                [
                    {'name': user['user_name'],
                        'accesstype': user['accesstype']}
                ])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_update_access_right_fail(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.acc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        user = {'vdcuser': self.vdcuser['service'], 
                'accesstype': 'W',
                'user_name': self.vdcuser['info']['name']}

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        account.authorize_user.return_value = False   
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.user_authorize(user['vdcuser'], user['accesstype'])

            instance.account.update_access.assert_called_once_with(
                username=user['user_name'],
                right=user['accesstype'])
            api.services.find.assert_has_calls(
                [mock.call(template_uid=self.type.VDCUSER_TEMPLATE,
                            name=user['vdcuser'])]
            )

    def test_user_unauthorize_statecheckerror(self):
        instance = self.type('test', None)
        user = {'vdcuser': 'test1', 'accesstype': 'W',
                'user_name': 'user@provider'}
        with pytest.raises(StateCheckError):
            # fails if account not installed
            instance.user_authorize(user['vdcuser'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_unauthorize_success(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.acc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        user = {'vdcuser': self.vdcuser['service'], 
                'accesstype': 'W',
                'user_name': self.vdcuser['info']['name']}

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.user_unauthorize(user['vdcuser'])

            instance.account.unauthorize_user.assert_called_once_with(
                username=user['user_name'])
            api.services.find.assert_has_calls(
                [mock.call(template_uid=self.type.VDCUSER_TEMPLATE,
                            name=user['vdcuser'])]
            )
            self.assertEqual(
                instance.data['users'], [])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_unauthorize_fail(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.acc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        # user to add
        user = {'vdcuser': self.vdcuser['service'], 
                'accesstype': 'W',
                'user_name': self.vdcuser['info']['name']}

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        account.unauthorize_user.return_value = False   
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            with self.assertRaisesRegex(RuntimeError,
                                        'failed to remove user "%s"' % user['user_name']):
                instance.user_unauthorize(user['vdcuser'])

            instance.account.unauthorize_user.assert_called_once_with(
                username=user['user_name'])
            api.services.find.assert_has_calls(
                [mock.call(template_uid=self.type.VDCUSER_TEMPLATE,
                            name=user['vdcuser'])]
            )


    # def test_user_unauthorize_success(self):
    #     """
    #     Test deleting a user success
    #     """
    #     instance = self.type('test', None)
    #     instance.state.set('actions', 'install', 'ok')

    #     users = [{'userGroupId': 'user@provider', 'right': 'R'}]
    #     # user to delete
    #     user = {'vdcuser': 'test1', 'accesstype': 'W',
    #             'user_name': 'user@provider'}

    #     # mock finding services
    #     def find(template_uid, name):
    #         task_mock = MagicMock(result=user['user_name'])
    #         proxy = MagicMock(
    #             schedule_action=MagicMock(return_value=task_mock))
    #         return [proxy]

    #     with patch.object(instance, 'api') as api:
    #         api.services.find.side_effect = find
    #         with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:

    #             # test success
    #             ovc.return_value.account_get.return_value.unauthorize_user.return_value = True
    #             ovc.return_value.account_get.return_value.model = {
    #                 'acl': users}

    #             instance.user_unauthorize(vdcuser=user['vdcuser'])
    #             instance.account.unauthorize_user.assert_called_once_with(
    #                 username=user['user_name'])
    #             self.assertEqual(instance.data['users'], [])

    # def test_user_unauthorize_fail(self):
    #     """
    #     Test deleting a user fail
    #     """
    #     instance = self.type('test', None)
    #     instance.state.set('actions', 'install', 'ok')

    #     users = [{'userGroupId': 'user@provider', 'right': 'R'}]
    #     # user to delete
    #     user = {'vdcuser': 'test1', 'accesstype': 'W',
    #             'user_name': 'user@provider'}

    #     # mock finding services
    #     def find(template_uid, name):
    #         task_mock = MagicMock(result=user['user_name'])
    #         proxy = MagicMock(
    #             schedule_action=MagicMock(return_value=task_mock))
    #         return [proxy]

    #     with patch.object(instance, 'api') as api:
    #         api.services.find.side_effect = find
    #         with patch('js9.j.clients.openvcloud.get', return_value=self.ovc_mock) as ovc:
    #             ovc.return_value.account_get.return_value.unauthorize_user.return_value = False
    #             ovc.return_value.account_get.return_value.model = {
    #                 'acl': users}
    #             with pytest.raises(RuntimeError,
    #                                message='failed to remove user "%s"' % user['vdcuser']):
    #                 instance.user_unauthorize(vdcuser=user['vdcuser'])
