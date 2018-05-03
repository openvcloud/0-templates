import os
from mock import MagicMock


from unittest import TestCase
from unittest import mock
from js9 import j

from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestVdcUser(TestCase):
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
        self.vdcuser = {
            'service': 'test_vdcuser_service',
            'full_name': 'test_vdcuser@itsyouonline',
            'accesstype': 'R',
            'info': {
                'password': 'password',
                'email': 'email@test.com',
                'name': 'test_vdcuser',              
                'openvcloud': self.ovc['service'],
            }
        }                       

    def get_service(self, template_uid, name):
        self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
        self.assertEqual(name, self.ovc['service'])

        proxy = MagicMock(schedule_action=MagicMock())
        proxy.schedule_action().wait = MagicMock()
        proxy.schedule_action().wait(die=True).result = self.ovc['info']

        return proxy

    def test_validate(self):
        # test fails:
        # missing username
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'email': 'email@test.com',
        }
        instance = self.type('vdcuser', None, data)
        with self.assertRaisesRegex(ValueError, 'name is required'):
            instance.validate()

        # missing email
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'name': 'username',
        }
        instance = self.type('vdcuser', None, data)
        with self.assertRaisesRegex(ValueError, 'email is required'):
            instance.validate()

        # missing openvcloud
        data = {
            'password': 'passwd',
            'name': 'username',
            'email': 'email@test.com',
        }
        instance = self.type('vdcuser', None, data)
        with self.assertRaisesRegex(ValueError, 'openvcloud is required'):
            instance.validate()

        # test success
        data = {
            'name': 'username',
            'openvcloud': 'connection',
            'password': 'passwd',
            'email': 'email@test.com',
        }
        instance = self.type('vdcuser', None, data)
        instance.validate()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_nonexistent_user(self, ovc):
        data = self.vdcuser['info']
        instance = self.type(self.vdcuser['service'], None, data)

        # mock ovc client
        client = ovc.get.return_value
        client.api.system.usermanager.userexists.return_value = False
        
        with mock.patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.install()

        client.api.system.usermanager.create.assert_called_once_with(
            username=self.vdcuser['info']['name'],
            groups=[],
            emails=[data['email']],
            domain='',
            password=data['password'],
            provider='itsyouonline',
        )
        ovc.get.assert_called_once_with(self.ovc['info']['name'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_existent_user(self, ovc):
        data = self.vdcuser['info']
        instance = self.type(self.vdcuser['service'], None, data)

        # mock ovc client        
        client = ovc.get.return_value
        client.api.system.usermanager.userexists.return_value = True

        with mock.patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.install()

        client.api.system.usermanager.userexists.assert_called_once_with(
            name=self.vdcuser['full_name'])
        client.api.system.usermanager.create.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_nonexistent_user(self, ovc):
        data = self.vdcuser['info']
        instance = self.type(self.vdcuser['service'], None, data)

        # mock ovc client        
        client = ovc.get.return_value
        client.api.system.usermanager.userexists.return_value = False
        with mock.patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.uninstall()

        ovc.get.assert_called_once_with(self.ovc['info']['name'])
        client.api.system.usermanager.userexists.assert_called_once_with(
            name=self.vdcuser['full_name'])

        client.api.system.usermanager.delete.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall_existent_user(self, ovc):
        data = self.vdcuser['info']
        instance = self.type(self.vdcuser['service'], None, data)

        # mock ovc client        
        client = ovc.get.return_value
        client.api.system.usermanager.userexists.return_value = True
        with mock.patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.uninstall()
            
        client.api.system.usermanager.userexists.assert_called_once_with(
            name=self.vdcuser['full_name'])

        client.api.system.usermanager.delete.assert_called_once_with(
            username=self.vdcuser['full_name'])


    @mock.patch.object(j.clients, '_openvcloud')
    def test_set_groups_state_check_error(self, ovc):
        data = self.vdcuser['info']
        instance = self.type(self.vdcuser['service'], None, data) 
        with self.assertRaises(StateCheckError):
            instance.groups_set([])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_set_groups_no_change(self, ovc):
        data = self.vdcuser['info']
        instance = self.type(self.vdcuser['service'], None, data)        
        instance.state.set('actions', 'install', 'ok')

        # mock ovc client        
        client = ovc.get.return_value
        client.api.system.usermanager.userexists.return_value = True

        with mock.patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.groups_set([])  # not changing the groups

        client.api.system.usermanager.editUser.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_set_groups(self, ovc):
        data = self.vdcuser['info']
        instance = self.type(self.vdcuser['service'], None, data)        
        instance.state.set('actions', 'install', 'ok')

        # mock ovc client        
        client = ovc.get.return_value
        client.api.system.usermanager.userexists.return_value = True

        # change groups
        groups = ['group1', 'group2']
        with mock.patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.groups_set(groups)

        client.api.system.usermanager.editUser.assert_called_once_with(
            username=self.vdcuser['full_name'],
            groups=groups,
            provider='itsyouonline',
            emails=[data['email']]
        )
