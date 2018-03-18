import unittest
from framework.utils.utils import OVC_BaseTest
from collections import OrderedDict
from random import randint


class vms(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(vms, self).__init__(*args, **kwargs)

    def setUp(self):
        super(vms, self).setUp()
        self.acc1 = self.random_string()
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud}
        self.cs1 = self.random_string()
        self.cs1_id = self.get_cloudspace(self.cs1)['id']
        self.vm1 = self.random_string()
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud}
        self.cloudspaces[self.cs1] = {'account': self.acc1}
        self.vms[self.vm1] = {}
        self.temp_actions = {'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']},
                             'vdc': {'actions': ['install']},
                             'node': {'actions': ['install']}}

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
        res = self.create_vm(vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, vms=self.vms,
                             temp_actions=self.temp_actions)
        self.assertEqual(res, 'sshKey is required')

        self.log('Create a vm without providing vdc parameter, should fail.')
        self.vms[self.vm1] = {'sshKey': self.key}
        res = self.create_vm(ovdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, vms=self.vms,
                             temp_actions=self.temp_actions)
        self.assertEqual(res, 'vdc name should be given')

        self.log('Create a vm with providing non existing parameter, should fail.')
        self.vms[self.vm1].update({'vdc': self.cs1, self.random_string(): self.random_string()})
        res = self.create_vm(vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, vms=self.vms,
                             temp_actions=self.temp_actions)
        self.assertEqual(res, 'parameter provided is wrong')

        self.log('Create a vm with providing non existing user, should fail')
        self.vms[self.vm1] = {'sshKey': self.key, 'vdc': self.cs1,
                              'users': OrderedDict([('name', self.random_string()),
                                                    ('accesstype', 'CXDRAU')])}
        res = self.create_vm(vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, vms=self.vms,
                             temp_actions=self.temp_actions)
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

        self.lg('Create two vms, should succeed')
        self.vms[self.vm1] = {'sshKey': self.key, 'vdc': self.cs1}
        res = self.create_vm(vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, vms=self.vms,
                             temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.vm1, res[self.vm1])

        self.log("Check if the 1st vm's parameters are reflected correctly on OVC")
        vm = self.get_vm(cloudspaceId=self.cs1_id, vmname=self.vm1)
        self.assertEqual(self.cs1_id, vm['cloudspaceid'])

        self.log('%s ENDED' % self._testID)

    def tearDown(self):
        for accountname in self.accounts.keys():
            if self.check_if_service_exist(accountname):
                self.temp_actions = {'account': {'actions': ['uninstall']}}
                self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                    accounts=self.accounts, temp_actions=self.temp_actions)
        self.delete_services()
