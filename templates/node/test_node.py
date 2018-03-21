from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
import tempfile
import shutil
import os
import pytest

from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot import config, template_collection
from zerorobot.template_uid import TemplateUID
from zerorobot.template.state import StateCheckError


class TestNode(TestCase):

    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

        self.valid_data ={
            'vdc': 'vdcName', 
            'sshKey': 'keyName'
            }            

        # define machine mock properties
        machine_mock = MagicMock(id=int, 
                            sshLogin=str,
                            sshPassword=str,
                            ipPublic=str,
                            ipPrivate=str,
                            prefab=MagicMock(return_value=None))        
        space_mock = MagicMock(machine_get=MagicMock(return_value=machine_mock))
        self.ovc_mock=MagicMock(space_get=MagicMock(return_value=space_mock))

    def tearDown(self):
        patch.stopall()

    def test_validate(self):
        """
        Test validate method
        """
        name = 'test'
        instance = self.type(name=name, guid=None, data=self.valid_data)

        @mock.patch.object(instance, 'api')
        def validate(instance, api):
            api.services.find.return_value = [None]
            instance.validate()

        validate(instance)
        instance.delete()

        # test missing sshkey service name
        invalid_data ={
            'vdc': 'vdcName',
            }

        instance = self.type(name=name, guid=None, data=invalid_data)
        with pytest.raises(ValueError,
                           message='sshKey name is required'):
            instance.validate()
        instance.delete()              

        # test missing sshkey service name
        invalid_data ={
            'sshKey': 'sshkeyName',
            }
        with pytest.raises(ValueError,
                           message='vdc name is required'):
            instance.validate()
        instance.delete()

    def test_config(self):
        '''
        Test fetching config from vdc, account, and ovc services
        '''
        instance = self.type(name='test', data=self.valid_data)
        with patch.object(instance, 'api') as api:
            api.services.find.side_effect = [[], [None,None]]
            # test when no vdc service is found
            with pytest.raises(RuntimeError,
                               message='found 0 vdcs with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

            # test when more than 1 vdc service is found
            with pytest.raises(RuntimeError,
                               message='found 2 vdcs with name "%s", required exactly one' % self.valid_data['vdc']):
                instance.config

            # test when no account service is found
            account_name = 'test_account'
            task_mock = MagicMock(result=account_name)
            mock_find_ovc = MagicMock(schedule_action=MagicMock(return_value=task_mock))            
            api.services.find.side_effect = [ [mock_find_ovc], []]
            with pytest.raises(RuntimeError,
                               message='found 0 accounts with name "%s", required exactly one' % account_name):
                instance.config

            # test when more than 1 account service is found
            api.services.find.side_effect = [ [mock_find_ovc], [None, None]]
            with pytest.raises(RuntimeError,
                               message='found 2 accounts with name "%s", required exactly one' % account_name):
                instance.config

            # test success
            ovc_name = 'test_ovc'
            task_mock = MagicMock(result=ovc_name)
            mock_find_acc = MagicMock(schedule_action=MagicMock(return_value=task_mock))
            api.services.find.side_effect = [ [mock_find_ovc], [mock_find_acc]]
            instance.config

            self.assertEqual(instance.config['ovc'], ovc_name)
            self.assertEqual(instance.config['account'], account_name)

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, ovc):
        """
        Test install VM
        """
        # if installed, do nothing
        instance = self.type(name='test', data=self.valid_data)
        instance.state.set('actions', 'install', 'ok')
        instance.install()
        ovc.get.return_value.space_get.return_value.machine_create.assert_not_called()
        instance.state.delete('actions', 'install')

        # test installing vm
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            ovc.get.return_value = MagicMock(self.ovc_mock)

            # test VM already exists
            instance.install()
            ovc.get.return_value.space_get.return_value.machine_get.return_value.delete.assert_called_once_with()

            # test creation of a new VM
            instance.state.delete('actions', 'install')

            # set mock to rise error for machine_get
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            ovc.get.return_value.space_get.return_value.machine_get.side_effect = RuntimeError
            instance.install()



    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, ovc):
        """
        Test install VM
        """
        instance = self.type(name='test', data=self.valid_data)

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.uninstall()

        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]

            # test uninstall
            ovc.get.return_value = MagicMock(self.ovc_mock)
            instance.uninstall()
            ovc.get.return_value.space_get.return_value.machine_get.return_value.delete.assert_called_once_with()

    def test_start(self):
        '''
        Test start action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.start()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.start()
        instance.machine.start.assert_called_once_with()

    def test_stop(self):
        '''
        Test stop action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.stop()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.stop()
        instance.machine.stop.assert_called_once_with()

    def test_restart(self):
        '''
        Test restart action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.restart()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.restart()
        instance.machine.restart.assert_called_once_with()

    def test_pause(self):
        '''
        Test pause action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.pause()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.pause()
        instance.machine.pause.assert_called_once_with()

    def test_resume(self):
        '''
        Test resume action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.resume()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.resume()
        instance.machine.resume.assert_called_once_with()

    def test_reset(self):
        '''
        Test reset action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.reset()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.reset()
        instance.machine.reset.assert_called_once_with()

    def test_snapshot(self):
        '''
        Test snapshot action
        '''
        instance = self.type(name='test', data=self.valid_data)  

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot()
        instance.machine.snapshot_create.assert_called_once_with()  

    def test_clone(self):
        '''
        Test clone action
        '''
        instance = self.type(name='test', data=self.valid_data)  
        clone_name = 'test_clone'

        # test call without arguments
        with pytest.raises(TypeError,
                           message="clone() missing 1 required positional argument: 'clone_name'"):
            instance.clone()

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.clone(clone_name)
        instance.machine.clone.assert_called_once_with(clone_name)

    def test_snapshot_rollback(self):
        '''
        Test snapshot_rollback action
        '''
        instance = self.type(name='test', data=self.valid_data)  
        snapshot_epoch = 'test_epoch'

        # test call without arguments
        with pytest.raises(TypeError,
                           message="snapshot_rollback() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_rollback()


        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_rollback(snapshot_epoch)
        instance.machine.snapshot_rollback.assert_called_once_with(snapshot_epoch)            

    def test_snapshot_delete(self):
        '''
        Test snapshot delete action
        '''
        instance = self.type(name='test', data=self.valid_data)  
        snapshot_epoch = 'test_epoch'

        # test call without arguments
        with pytest.raises(TypeError,
                           message="snapshot_delete() missing 1 required positional argument: 'snapshot_epoch'"):
            instance.snapshot_delete()


        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.snapshot()
        
        # test success
        instance.state.set('actions', 'install', 'ok')
        instance._machine = MagicMock()
        instance.snapshot_delete(snapshot_epoch)
        instance.machine.snapshot_delete.assert_called_once_with(snapshot_epoch) 

    @mock.patch.object(j.clients, '_openvcloud')
    def test_portforward_create(self, ovc):
        '''
        Test creating portforward
        '''
        instance = self.type(name='test', data=self.valid_data)
        ports = {'source':22, 'destination':22}
        
        # test call without arguments
        with pytest.raises(TypeError,
                           message="portforward_create() missing 1 required positional argument: 'ports'"):
            instance.portforward_create()
        

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.portforward_create(ports)
        
        # success
        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            ovc.get.return_value = MagicMock(self.ovc_mock)
            test_machine_id = 1
            ovc.get.return_value.space_get.return_value.machine_get.return_value.id = test_machine_id

            instance.portforward_create(ports)
            instance.vdc.schedule_action.assert_called_with(
                'portforward_create', 
                {'machineId': test_machine_id, 
                'port_forwards': ports, 
                'protocol': 'tcp'}
            )

    @mock.patch.object(j.clients, '_openvcloud')
    def test_portforward_delete(self, ovc):
        '''
        Test deleting portforward
        '''
        instance = self.type(name='test', data=self.valid_data)
        ports = {'source':22, 'destination':22}
        
        # test call without arguments
        with pytest.raises(TypeError,
                           message="portforward_create() missing 1 required positional argument: 'ports'"):
            instance.portforward_delete()

        with pytest.raises(StateCheckError):
            # fails if not installed
            instance.portforward_delete(ports)
        
        # success
        instance.state.set('actions', 'install', 'ok')
        with patch.object(instance, 'api') as api:
            api.services.find.return_value = [MagicMock(schedule_action=MagicMock())]
            ovc.get.return_value = MagicMock(self.ovc_mock)
            test_machine_id = 1
            ovc.get.return_value.space_get.return_value.machine_get.return_value.id = test_machine_id

            instance.portforward_delete(ports)
            instance.vdc.schedule_action.assert_called_with(
                'portforward_delete', 
                {'machineId': test_machine_id, 
                'port_forwards': ports, 
                'protocol': 'tcp'}
            )