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
        self.acc_info = {'name': 'test_account',
                         'openvcloud': 'be-gen'}      
        self.acocunt_service_name = 'test_account_service'
        self.vdc_name = 'vdc_service_name'

    @staticmethod
    def set_up_proxy_mock(result, state='ok', name='service_name'):
        task = MagicMock(result=result, state=state)
        proxy = MagicMock(schedule_action=MagicMock(return_value=task))
        proxy.name = name
        return proxy

    def ovc_mock(self, instance):
        space_model = MagicMock(model={'name': self.vdc_name})
        space_mock = MagicMock(model=space_model)
        acc_mock = MagicMock(space_get=MagicMock(return_value=space_mock))
        acc_mock.spaces = [space_model]
        return MagicMock(account_get=MagicMock(return_value=acc_mock))

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
        
        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info)]

        name = 'test'
        data = {
            'account': 'account-service-name',
            'name': name
        }
        instance = self.type(name, None, data)

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

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info)]

        data = {
            'name' : self.vdc_name,
            'account': self.acocunt_service_name,
        }
        instance = self.type('test', None, data)
        ovc.get.side_effect = self.ovc_mock
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
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

    def test_update(self):
        """
        Test updating vdc limits
        """
        instance = self.type('test', None, {})
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

    @mock.patch.object(j.clients, '_openvcloud')
    def test_portforward_create_require_arguments(self, ovc):
        """ Test call without arguments """
        instance = self.type('test', None, None)
        with pytest.raises(TypeError,
                           message="portforward_create() missing 2 required positional arguments: 'node_service' and 'ports'"):
            instance.portforward_create()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_portforward_create(self, ovc):
        """
        Test creating portforward
        """
        data = {
            'account': 'test_account'
        }

        instance = self.type('test', None, None)
        port = {'source': 22, 'destination': 22}
        machine_id = 1234
        space_id = 100
        ipaddr_pub = '10.00.00.00'

        node_info = {'name': 'test_node_name', 'id': machine_id}
        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info)]
            if template_uid == self.type.NODE_TEMPLATE:
                return [self.set_up_proxy_mock(result=node_info)]

        space_mock = MagicMock(ipaddr_pub=ipaddr_pub, id=space_id)

        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find

            instance._space = space_mock
            instance.portforward_create(node_service='test_node', ports=[port])
            instance.ovc.api.cloudapi.portforwarding.create.assert_called_with(
                cloudspaceId=space_id,
                protocol='tcp',
                localPort=port['destination'],
                publicPort=port['source'],
                publicIp=ipaddr_pub,
                machineId=machine_id,
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_portforward_delete(self, ovc):
        """
        Test deleting portforward
        """
        data = {
            'account': 'test_account'
        }

        instance = self.type('test', None, None)
        instance.state.set('actions', 'install', 'ok')

        port = {'source': '22', 'destination': '2200'}
        port_id = 111
        machine_id = 1234
        space_id = 100
        ipaddr_pub = '10.00.00.00'

        node_info = {'name': 'test_node_name', 'id': machine_id}
        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info)]
            if template_uid == self.type.NODE_TEMPLATE:
                return [self.set_up_proxy_mock(result=node_info)]

        space_mock = MagicMock(ipaddr_pub=ipaddr_pub, id=space_id)
        list_of_ports = [{
            'publicPort': port['source'],
            'localPort': port['destination'],
            'id': port_id
        }]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.ovc.api.cloudapi.portforwarding.list = MagicMock(
                return_value=list_of_ports)
            instance._space = space_mock
            instance.portforward_delete(node_service='test_node', ports=[port])
            instance.ovc.api.cloudapi.portforwarding.delete.assert_called_with(
                id=port_id,
                cloudspaceId=space_id,
                protocol='tcp',
                localPort=port['destination'],
                publicPort=port['source'],
                publicIp=ipaddr_pub,
                machineId=machine_id,
            )

class AuthorizeUserTestCase(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )
        # set up existing user
        self.user = {'service': 'test_user',
                     'info': {'name': 'test_user@intyouonline', 'accesstype':  'R'}
                     }
        # set up new user
        self.new_user = {'service': 'new_test_user',
                         'info': {'name': 'new_test_user@intyouonline', 'accesstype':  'W'}
                         }

        # set up instance
        self.instance = self.type('test', None)
        self.instance.state.set('actions', 'install', 'ok')
        self.acc_info = {'name': 'test_account',
                         'openvcloud': 'be-gen'}
        self.mock_bool_result = True

    @staticmethod
    def set_up_proxy_mock(result, state='ok', name='service_name'):
        task = MagicMock(result=result, state=state)
        proxy = MagicMock(schedule_action=MagicMock(return_value=task))
        proxy.name = name
        return proxy

    def ovc_mock(self, instance):
        space_mock = MagicMock(model={
            'acl': [{
                'userGroupId': self.user['info']['name'],
                'right': self.user['info']['accesstype']}
            ]},
            authorize_user=MagicMock(return_value=self.mock_bool_result),
            update_access=MagicMock(return_value=self.mock_bool_result),
            unauthorize_user=MagicMock(return_value=self.mock_bool_result)
        )
        acc_mock = MagicMock(space_get=MagicMock(return_value=space_mock))
        return MagicMock(account_get=MagicMock(return_value=acc_mock))

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_success(self, ovc):
        """
        Test authorizing a new user
        """
        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info)]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.new_user['info'])]

        ovc.get.side_effect = self.ovc_mock
        with patch.object(self.instance, 'api') as api:
            api.services.find.side_effect = find
            self.instance.user_authorize(self.new_user['service'],
                                         self.new_user['info']['accesstype'])

            self.instance.space.authorize_user.assert_called_once_with(
                username=self.new_user['info']['name'], right=self.new_user['info']['accesstype'])

            self.assertEqual(api.services.find.call_count, 3)

            self.assertEqual(
                self.instance.data['users'],
                [self.user['info'], self.new_user['info']]
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_fail_no_vdcuser_service(self, ovc):
        """
        Test authorizing a new user
        """
        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info, state='ok')]
            return []

        ovc.get.side_effect = self.ovc_mock
        with patch.object(self.instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'found 0 services with name "%s", required exactly one' % self.new_user['service']):
                self.instance.user_authorize(
                    self.new_user['service'], self.new_user['info']['accesstype'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_fail_adding_user(self, ovc):
        """
        Test authorizing a new user
        """
        self.mock_bool_result = False
        ovc.get.side_effect = self.ovc_mock

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info, state='ok')]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.new_user['info'], state='ok')]

        with patch.object(self.instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'failed to add user "%s"' % self.new_user['info']['name']):
                self.instance.user_authorize(
                    self.new_user['service'], self.new_user['info']['accesstype'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_update_access_right_success(self, ovc):
        """
        Test updating access right of an authorized user
        """
        new_accesstype = 'W'

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info, state='ok')]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.user['info'], state='ok')]

        ovc.get.side_effect = self.ovc_mock
        with patch.object(self.instance, 'api') as api:
            api.services.find.side_effect = find
            self.instance.user_authorize(self.user['service'], new_accesstype)

        self.instance.space.update_access.assert_called_once_with(
            username=self.user['info']['name'], right=new_accesstype)

        self.assertEqual(self.instance.data['users'],
                         [{'name': self.user['info']['name'], 'accesstype': 'W'}])

    def test_user_update_access_right_fail(self):
        """
        Test failing updating access when vdc service is not installed
        """
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_update_access_right_fail(self, ovc):
        """
        Test updating access right of an authorized user
        """

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_update_access_right_fail(self, ovc):
        """
        Test updating access right of an authorized user
        """
        new_accesstype = 'W'

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info, state='ok')]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.user['info'], state='ok')]

        self.mock_bool_result = False
        ovc.get.side_effect = self.ovc_mock
        with patch.object(self.instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'failed to update accesstype of user "%s"' %
                                         self.user['info']['name']):
                self.instance.user_authorize(
                    self.user['service'], new_accesstype)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_unauthorize_success(self, ovc):
        """
        Test deleting a user
        """
        instance = self.instance
        user = self.user

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info, state='ok')]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.user['info'], state='ok')]

        ovc.get.side_effect = self.ovc_mock
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.user_unauthorize(user['service'])
            instance.space.unauthorize_user.assert_called_once_with(
                username=user['info']['name'])
            self.assertEqual(instance.data['users'], [])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_unauthorize_fail(self, ovc):
        """
        Test deleting a user
        """
        instance = self.instance
        user = self.user

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info, state='ok')]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.user['info'], state='ok')]

        ovc.get.side_effect = self.ovc_mock
        self.mock_bool_result = False
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'failed to remove user "%s"' % user['info']['name']):
                instance.user_unauthorize(user['service'])

        instance.space.unauthorize_user.assert_called_once_with(
            username=user['info']['name'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_unauthorize_task_fail(self, ovc):
        """
        Test deleting a user
        """
        instance = self.instance
        user = self.user

        def find(template_uid, name):
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc_info)]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.user['info'], state='error', name=self.user['service'])]

        ovc.get.side_effect = self.ovc_mock
        self.mock_bool_result = False
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'error occurred when executing action "get_info" on service "%s"' %
                                         self.user['service']):
                instance.user_unauthorize(user['service'])
