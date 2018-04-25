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

        self.ovc = {
            'service': 'test_ovc_service',
            'info': {'name': 'connection_instance_name'}
        }
        self.acc = {
            'service': 'test_account_service',
            'info': {'name': 'test_account',
                     'openvcloud': self.ovc['service']}
        }
        self.vdc = {
            'service': 'test_vdc_service',
            'info': {'name': 'test_vdc',
                     'account': self.acc['service']}
        }                    
        self.vdcuser = {
            'service': 'test_vdcuser_service',
            'base_name': 'test_vdcuser',
            'accesstype': 'R',
            'info': {'name': 'test_vdcuser@itsyouonline',
                     'openvcloud': self.ovc['service']}
        }
        self.node = {
            'service': 'test_node_service',
            'info': {'name': 'test_node_name',
                     'vdc': self.vdc['service'],
                     'id': 123}
        }
        # set up existing user
        self.user = {'service': 'test_user',
                     'info': {'name': self.vdcuser['info']['name'], 'accesstype':  'R'}
                     }
        # set up new user
        self.new_user = {'service': 'new_test_user',
                         'info': {'name': 'new_test_user@intyouonline', 'accesstype':  'W'}
                         }

    def tearDown(self):
        patch.stopall()

    @staticmethod
    def set_up_proxy_mock(result, state='ok', name='service_name'):
        task = MagicMock(result=result, state=state)
        proxy = MagicMock(schedule_action=MagicMock(return_value=task))
        proxy.name = name
        return proxy

    def find(self, template_uid, name):
        if template_uid == self.type.ACCOUNT_TEMPLATE:
            return [self.set_up_proxy_mock(result=self.acc['info'], name=self.acc['service'])]
        if template_uid == self.type.OVC_TEMPLATE:
            return [self.set_up_proxy_mock(result=self.ovc['info'], name=self.ovc['service'])]
        if template_uid == self.type.NODE_TEMPLATE:
            return [self.set_up_proxy_mock(result=self.node['info'], name=self.node['service'])]
        if template_uid == self.type.VDCUSER_TEMPLATE:
            return [self.set_up_proxy_mock(result=self.vdcuser['info'], name=self.vdcuser['service'])]


    def ovc_mock(self, instance):
        model = {'name': self.vdc['info']['name'],
                                       'acl': [{
                                            'userGroupId': self.user['info']['name'],
                                            'right': self.user['info']['accesstype']}]
                                }
        space_mock = MagicMock(model=model)
        acc_mock = MagicMock(space_get=MagicMock(return_value=space_mock))
        acc_mock.spaces = [MagicMock(model=model)]
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
        data = self.vdc['info']
        instance = self.type('test', None, data)
        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.uninstall()
            instance.space.delete.assert_called_once_with()
        with self.assertRaises(StateCheckError):
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
        data  = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        port = {'source': 22, 'destination': 22}
        machine_id = self.node['info']['id']
        space_id = 100
        ipaddr_pub = '10.00.00.00'

        space_mock = MagicMock(ipaddr_pub=ipaddr_pub, id=space_id)
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
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
        data  = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        port = {'source': '22', 'destination': '2200'}
        port_id = 111
        machine_id = self.node['info']['id']
        space_id = 100
        ipaddr_pub = '10.00.00.00'

        space_mock = MagicMock(ipaddr_pub=ipaddr_pub, id=space_id)
        list_of_ports = [{
            'publicPort': port['source'],
            'localPort': port['destination'],
            'id': port_id
        }]

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
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

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_success(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        def find(template_uid, name):
            if template_uid == self.type.OVC_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.ovc['info'])]             
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc['info'])]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.new_user['info'])]

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.user_authorize(self.new_user['service'],
                                         self.new_user['info']['accesstype'])

            instance.space.authorize_user.assert_called_once_with(
                username=self.new_user['info']['name'], right=self.new_user['info']['accesstype'])

            self.assertEqual(api.services.find.call_count, 4)

            self.assertEqual(
                instance.data['users'],
                [self.user['info'], self.new_user['info']]
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_fail_no_vdcuser_service(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        def find(template_uid, name):
            if template_uid == self.type.OVC_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.ovc['info'])]            
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc['info'])]
            return []

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'found 0 services with name "%s", required exactly one' % 
                                         self.new_user['service']):
                instance.user_authorize(
                    self.new_user['service'], self.new_user['info']['accesstype'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_authorize_fail_adding_user(self, ovc):
        """
        Test authorizing a new user
        """
        data = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        self.mock_bool_result = False

        def find(template_uid, name):
            if template_uid == self.type.OVC_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.ovc['info'])]             
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc['info'], state='ok')]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.new_user['info'], state='ok')]

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        space = account.space_get.return_value
        space.authorize_user.return_value = False

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'failed to add user "%s"' % self.new_user['info']['name']):
                instance.user_authorize(
                    self.new_user['service'], self.new_user['info']['accesstype'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_update_access_right_success(self, ovc):
        """
        Test updating access right of an authorized user
        """
        new_accesstype = 'W'
        data = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])

        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.user_authorize(self.user['service'], new_accesstype)

        instance.space.update_access.assert_called_once_with(
            username=self.user['info']['name'], right=new_accesstype)

        self.assertEqual(instance.data['users'],
                         [{'name': self.user['info']['name'], 'accesstype': 'W'}])

    def test_user_update_access_right_fail(self):
        """
        Test failing updating access when vdc service is not installed
        """
        instance = self.type('test', None)
        instance.state.set('actions', 'install', 'ok')

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_unauthorize_success(self, ovc):
        """
        Test deleting a user
        """
        data = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        user = self.user

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
            instance.user_unauthorize(user['service'])
            instance.space.unauthorize_user.assert_called_once_with(
                username=user['info']['name'])
            self.assertEqual(instance.data['users'], [])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_user_unauthorize_fail(self, ovc):
        """
        Test deleting a user
        """
        data = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')
        user = self.user

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        client = ovc.get.return_value
        account = client.account_get.return_value
        space = account.space_get.return_value
        space.unauthorize_user.return_value = False        

        self.mock_bool_result = False
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = self.find
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
        data = self.vdc['info']
        instance = self.type('test', None, data)
        instance.state.set('actions', 'install', 'ok')

        user = self.user

        def find(template_uid, name):
            if template_uid == self.type.OVC_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.ovc['info'])]            
            if template_uid == self.type.ACCOUNT_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.acc['info'])]
            if template_uid == self.type.VDCUSER_TEMPLATE:
                return [self.set_up_proxy_mock(result=self.user['info'], 
                        state='error', name=self.user['service'])]

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])
        self.mock_bool_result = False
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            with self.assertRaisesRegexp(RuntimeError,
                                         'error occurred when executing action "get_info" on service "%s"' %
                                         self.user['service']):
                instance.user_unauthorize(user['service'])
