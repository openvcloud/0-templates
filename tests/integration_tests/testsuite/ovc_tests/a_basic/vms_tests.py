import unittest
from framework.ovc_utils.utils import OVC_BaseTest
from collections import OrderedDict
from random import randint


class BasicTests(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(BasicTests, self).__init__(*args, **kwargs)

    def setUp(self):
        super(BasicTests, self).setUp()
        self.acc1 = self.random_string()
        self.accounts = {self.acc1: {'openvcloud': self.openvcloud}}
        self.cs1 = self.random_string()
        self.vm1 = self.random_string()
        self.cloudspaces = {self.cs1: {'account': self.acc1}}
        self.vms = dict()
        self.temp_actions = {'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']},
                             'vdc': {'actions': ['install']},
                             'node': {'actions': ['install']}}
        self.CLEANUP["accounts"].append(self.acc1)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/47')
    def test001_create_vm_with_wrong_params(self):
        """ ZRT-OVC-000
        *Test case for creating virtual machine with wrong parameters*

        **Test Scenario:**

        #. Create an vm without providing sshKey parameter, should fail.
        #. Create a vm without providing vdc parameter, should fail.
        #. Create a vm with providing non existing parameter, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create a vm without providing sshKey parameter, should fail.')
        self.vms[self.vm1] = {'vdc': self.cs1}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertEqual(res, 'sshKey is required')

        self.log('Create a vm without providing vdc parameter, should fail.')
        self.vms[self.vm1] = {'sshKey': self.key}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertEqual(res, 'vdc name should be given')

        self.log('Create a vm with providing non existing parameter, should fail.')
        self.vms[self.vm1].update({'vdc': self.cs1, self.random_string(): self.random_string()})
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertEqual(res, 'parameter provided is wrong')

        self.log('Create a vm with providing non existing user, should fail')
        self.vms[self.vm1] = {'sshKey': self.key, 'vdc': self.cs1,
                              'users': OrderedDict([('name', self.random_string()),
                                                    ('accesstype', 'CXDRAU')])}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertIn('no vdcuser found', res)

        self.log('%s ENDED' % self._testID)

    def test002_create_vms_with_correct_params(self):
        """ ZRT-OVC-000
        Test case for creating virtual machine with correct parameters*

        **Test Scenario:**

        #. Create two vms, should succeed.
        #. Check if the 1st vm's parameters are reflected correctly on OVC.
        #. Check if the 2nd vm is created, should succeed.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create two vms, should succeed')
        self.vms[self.vm1] = {'sshKey': self.key, 'vdc': self.cs1}
        self.vm2 = self.random_string()
        self.vdcuser = self.random_string()
        self.vdcusers[self.vdcuser] = {'openvcloud': self.openvcloud,
                                       'provider': 'itsyouonline',
                                       'email': '%s@test.com' % self.random_string(),
                                       'groups': ['user']}
        bds = randint(10, 20)
        dds = randint(10, 20)
        self.vms[self.vm2] = {'sshKey': self.key, 'vdc': self.cs1,
                              'bootDiskSize': bds, 'dataDiskSize': dds}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.vm1, res[self.vm1])
        self.wait_for_service_action_status(self.vm2, res[self.vm2])

        self.log("Check if the 1st vm's parameters are reflected correctly on OVC")
        self.cs1_id = self.get_cloudspace(self.cs1)['id']
        vm = self.get_vm(cloudspaceId=self.cs1_id, vmname=self.vm1)
        self.assertTrue(vm, "No vm has been found")
        self.assertEqual(self.cs1_id, vm['cloudspaceid'])

        self.log('Check if the 2nd vm is created, should succeed')
        vm2 = self.get_vm(cloudspaceId=self.cs1_id, vmname=self.vm2)
        self.assertTrue(vm2, "No vm has been found")
        self.assertEqual([disk['sizeMax'] for disk in vm2['disks'] if disk['type'] == 'B'][0], bds)
        self.assertEqual([disk['sizeMax'] for disk in vm2['disks'] if disk['type'] == 'D'][0], dds)
        self.assertEqual(vm2['memory'], 512)
        self.assertEqual(vm2['vcpus'], 1)

        self.log('%s ENDED' % self._testID)
