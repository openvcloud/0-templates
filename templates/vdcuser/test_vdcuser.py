import os
import pytest
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

    def test_validate(self):
        # test fails:
        # missing username
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'email': 'email@test.com',          
        }
        instance = self.type('vdcuser', None, data)
        with pytest.raises(ValueError,
                           message='name is required'):
            instance.validate()

        # missing email
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'name': 'username',          
        }
        instance = self.type('vdcuser', None, data)
        with pytest.raises(ValueError,
                           message='email is required'):
            instance.validate()          

        # missing openvcloud
        data = {
            'password': 'passwd',
            'name': 'username',
            'email': 'email@test.com',     
        }
        instance = self.type('vdcuser', None, data)
        with pytest.raises(ValueError,
                           message='openvcloud is required'):
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
    def test_install(self, openvcloud):
        name = 'user1'
        data = {
            'openvcloud': 'connection',
            'password': 'password',
            'email': 'email@test.com',
            'name': name,
        }
        connection_name = 'be-gen'
        def find(template_uid, name): 
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, data['openvcloud'])    
            task_mock = MagicMock(result=connection_name)
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        instance = self.type('vdcuser1', None, data)
        client = openvcloud.get.return_value
        # user exists
        client.api.system.usermanager.userexists.return_value = True
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find        
            instance.install()

        client.api.system.usermanager.userexists.assert_called_once_with(name=name+'@itsyouonline')

        openvcloud.reset_mock()
        client.api.system.usermanager.userexists.return_value = False
        instance.state.delete('actions', 'install')
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find        
            instance.install()

        client.api.system.usermanager.create.assert_called_once_with(
            username=name,
            groups=[],
            emails=[data['email']],
            domain='',
            password=data['password'],
            provider='itsyouonline',
        )
        openvcloud.get.assert_called_once_with(connection_name)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, openvcloud):
        name = 'user1'
        data = {
            'openvcloud': 'connection',
            'email': 'email@test.com',
            'name': name,
        }
        connection_name = 'be-gen'
        def find(template_uid, name): 
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, data['openvcloud'])    
            task_mock = MagicMock(result=connection_name)
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        client = openvcloud.get.return_value
        instance = self.type('vdcuser1', None, data)
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find
            instance.install()
        openvcloud.reset_mock()

        # user exists
        client.api.system.usermanager.userexists.return_value = True
        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find 
            instance.uninstall()

        client.api.system.usermanager.userexists.assert_called_once_with(name=name+'@itsyouonline')

        client.api.system.usermanager.delete.assert_called_once_with(
            username=name+'@itsyouonline',
        )
        openvcloud.get.assert_called_once_with(connection_name)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_set_groups(self, openvcloud):
        name = 'user1'
        data = {
            'openvcloud': 'connection',
            'password': 'passwd',
            'email': 'email@test.com',
            'name': name,
        }
        instance = self.type('vdcuser1', None, data)
        with self.assertRaises(StateCheckError):
            instance.groups_set([])

        connection_name = 'be-gen'
        def find(template_uid, name):
            self.assertEqual(template_uid, self.type.OVC_TEMPLATE)
            self.assertEqual(name, data['openvcloud'])    
            task_mock = MagicMock(result=connection_name)
            proxy = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            return [proxy]

        client = openvcloud.get.return_value
        client.api.system.usermanager.userexists.return_value = True
        instance.state.set('actions', 'install', 'ok')

        with mock.patch.object(instance, 'api') as api:
            api.services.find.side_effect = find


            # user exists
            instance.groups_set([])  # not changing the groups

        client.api.system.usermanager.editUser.assert_not_called()

        openvcloud.reset_mock()

        groups = ['group1', 'group2']
        instance.groups_set(groups)

        client.api.system.usermanager.editUser.assert_called_once_with(
            username=name+'@itsyouonline',
            groups=groups,
            provider='itsyouonline',
            emails=[data['email']]
        )
