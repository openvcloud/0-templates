import unittest
from framework.utils.utils import OVC_BaseTest
from collections import OrderedDict
from random import randint


class accounts(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(accounts, self).__init__(*args, **kwargs)

    def setUp(self):
        super(accounts, self).setUp()
        self.acc1 = self.random_string()
        self.vdcuser = self.random_string()
        self.vdcusers[self.vdcuser] = {'openvcloud': self.openvcloud,
                                       'provider': 'itsyouonline',
                                       'email': '%s@test.com' % self.random_string(),
                                       'groups': ['user']}
        self.accounts = dict()
        self.temp_actions = {'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']}}

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/47')
    def test001_create_account_with_wrong_params(self):
        """ ZRT-OVC-001
        *Test case for creating account with different or missing parameters*

        **Test Scenario:**

        #. Create an account without providing openvcloud parameter, should fail.
        #. Create an account with providing non existing openvcloud value, should fail.
        #. Create an account with providing non existing user, should fail
        #. Create an account with providing non existing parameter, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create an account without providing openvcloud parameter, should fail')
        self.accounts[self.acc1] = {}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(res, 'openvcloud is mandatory')

        self.log('Create an account with providing wrong openvcloud value, should fail.')
        self.accounts[self.acc1] = {'openvcloud': self.random_string()}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(res, 'found 0 openvcloud connections, requires exactly 1')

        self.log('Create an account with providing non existing user, should fail')
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud,
                                    'users': OrderedDict([('name', self.random_string()),
                                                          ('accesstype', 'CXDRAU')])}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertIn('no vdcuser found', res)

        self.log('Create an account with providing non existing parameter, should fail')
        self.accounts[self.acc1] = {self.random_string(): self.random_string()}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(res, 'parameter provided is wrong')

        self.log('%s ENDED' % self._testID)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/54')
    def test002_create_account_with_correct_params(self):
        """ ZRT-OVC-002
        *Test case for creating account with correct parameters*

        **Test Scenario:**

        #. Create two accounts, should succeed.
        #. Check if the 1st account parameters are reflected correctly on OVC.
        #. Check if the 2nd accound was created, should succeed.
        """
        self.log('%s STARTED' % self._testID)

        CU_D = randint(15, 30)
        CU_C = randint(15, 30)
        CU_I = randint(15, 30)
        CU_M = randint(15, 30)
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud, 'maxMemoryCapacity': CU_M,
                                    'maxCPUCapacity': CU_C, 'maxDiskCapacity': CU_D,
                                    'maxNumPublicIP': CU_I,
                                    'users': OrderedDict([('name', self.vdcuser),
                                                          ('accesstype', 'CXDRAU')])}
        self.accounts[self.acc2] = {'openvcloud': self.openvcloud}

        self.log('Create two accounts, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1])
        self.wait_for_service_action_status(self.acc2, res[self.acc2])

        self.log('Check if the 1st account parameters are reflected correctly on OVC')
        account = self.get_account(self.acc1)
        self.assertEqual(account['status'], 'CONFIRMED')
        self.assertEqual(account['resourceLimits']['CU_D'], CU_D)
        self.assertEqual(account['resourceLimits']['CU_C'], CU_C)
        self.assertEqual(account['resourceLimits']['CU_I'], CU_I)
        self.assertEqual(account['resourceLimits']['CU_M'], CU_M)
        self.assertIn('%s@itsyouonline' % self.vdcuser,
                      [user['userGroupId'] for user in account['acl']])

        self.log('Check if the 2nd accound was created, should succeed.')
        account = self.get_account(self.acc2)
        self.assertEqual(account['status'], 'CONFIRMED')

        self.log('%s ENDED' % self._testID)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/50')
    def test003_update_account__params(self):
        """ ZRT-OVC-003
        *Test case for updating account's parameters*

        **Test Scenario:**

        #. Create an account, should succeed
        #. Check if the account parameters are reflected correctly on OVC.
        #. Update some parameters and make sure it is updated.
        """
        self.log('%s STARTED' % self._testID)

        CU_D = randint(15, 30)
        CU_C = randint(15, 30)
        CU_I = randint(15, 30)
        CU_M = randint(15, 30)
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud, 'maxMemoryCapacity': CU_M,
                                    'maxCPUCapacity': CU_C, 'maxDiskCapacity': CU_D,
                                    'maxNumPublicIP': CU_I}

        self.log('Create an account, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1])

        self.log('Check if the account parameters are reflected correctly on OVC')
        account = self.get_account(self.acc1)
        self.assertEqual(account['status'], 'CONFIRMED')

        self.log('Update some parameters and make sure it is updated')
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud, 'maxMemoryCapacity': CU_M - 1,
                                    'maxCPUCapacity': CU_C - 1, 'maxDiskCapacity': CU_D - 1,
                                    'maxNumPublicIP': CU_I - 1}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1])
        account = self.get_account(self.acc1)
        self.assertEqual(account['resourceLimits']['CU_D'], CU_D - 1)
        self.assertEqual(account['resourceLimits']['CU_C'], CU_C - 1)
        self.assertEqual(account['resourceLimits']['CU_I'], CU_I - 1)
        self.assertEqual(account['resourceLimits']['CU_M'], CU_M - 1)

        self.log('%s ENDED' % self._testID)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/55')
    def test004_update_account_with_fake_user(self):
        """ ZRT-OVC-004
        *Test case for updating account with fake user*

        **Test Scenario:**

        #. Create an account with an existing user, should succeed.
        #. Update the account with fake user, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.accounts[self.acc1] = {'openvcloud': self.openvcloud,
                                    'users': OrderedDict([('name', self.vdcuser),
                                                          ('accesstype', 'CXDRAU')])}

        self.log('Create an account, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1])
        account = self.get_account(self.acc1)
        self.assertEqual(account['status'], 'CONFIRMED')

        self.log('Update the account with fake user, should fail')
        self.accounts[self.acc1]['users']['name'] = self.random_string()
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertIn('no vdcuser found', res)

        self.log('%s ENDED' % self._testID)

    def tearDown(self):
        for accountname in self.accounts.keys():
            if self.check_if_service_exist(accountname):
                self.temp_actions = {'account': {'actions': ['uninstall']}}
                self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                    accounts=self.accounts, temp_actions=self.temp_actions)
        self.delete_services()
