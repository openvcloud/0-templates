import unittest
from framework.ovc_utils.utils import OVC_BaseTest
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
        self.CLEANUP["accounts"].append(self.acc1)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/47')
    def test001_create_account_with_wrong_params(self):
        """ ZRT-OVC-001
        *Test case for creating account with different or missing parameters*

        **Test Scenario:**

        #. Create an account without providing openvcloud parameter, should fail.
        #. Create an account with providing non existing openvcloud value, should fail.
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

        self.log('Create an account with providing non existing parameter, should fail')
        self.accounts[self.acc1] = {self.random_string(): self.random_string()}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(res, 'parameter provided is wrong')

        self.log('%s ENDED' % self._testID)

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
                                    'maxCPUCapacity': CU_C, 'maxVDiskCapacity': CU_D,
                                    'maxNumPublicIP': CU_I }
        self.acc2 = self.random_string()
        self.accounts[self.acc2] = {'openvcloud': self.openvcloud}
        self.CLEANUP["accounts"].append(self.acc2)

        self.log('Create two accounts, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['install'])
        self.wait_for_service_action_status(self.acc2, res[self.acc2]['install'])

        self.log('Check if the 1st account parameters are reflected correctly on OVC')
        account = self.get_account(self.acc1)
        self.assertEqual(account['status'], 'CONFIRMED')
        self.assertEqual(account['resourceLimits']['CU_D'], CU_D)
        self.assertEqual(account['resourceLimits']['CU_C'], CU_C)
        self.assertEqual(account['resourceLimits']['CU_I'], CU_I)
        self.assertEqual(account['resourceLimits']['CU_M'], CU_M)

        self.log('Check if the 2nd accound was created, should succeed.')
        account = self.get_account(self.acc2)
        self.assertEqual(account['status'], 'CONFIRMED')

        self.log('%s ENDED' % self._testID)

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
                                    'maxCPUCapacity': CU_C, 'maxVDiskCapacity': CU_D,
                                    'maxNumPublicIP': CU_I}

        self.log('Create an account, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['install'])

        self.log('Check if the account parameters are reflected correctly on OVC')
        account = self.get_account(self.acc1)
        self.assertEqual(account['status'], 'CONFIRMED')

        self.log('Update some parameters and make sure it is updated')
        self.temp_actions['account'] = {'actions': ['update'],
                                        'args': {"maxMemoryCapacity": CU_M - 1, "maxCPUCapacity": CU_C - 1,
                                                 "maxVDiskCapacity": CU_D - 1, "maxNumPublicIP": CU_I - 1}}
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))

        self.wait_for_service_action_status(self.acc1, res[self.acc1]['update'])
        account = self.get_account(self.acc1)
        self.assertEqual(account['resourceLimits']['CU_D'], CU_D - 1)
        self.assertEqual(account['resourceLimits']['CU_C'], CU_C - 1)
        self.assertEqual(account['resourceLimits']['CU_I'], CU_I - 1)
        self.assertEqual(account['resourceLimits']['CU_M'], CU_M - 1)

        self.log('%s ENDED' % self._testID)

    def test004_account_add_delete_user(self):
        """ ZRT-OVC-004
        *Test case for updating account with fake user*

        **Test Scenario:**

        #. Create an account (A1).
        #. Add an existing user to A1, should succeed.
        #. Delete an existing user from A1, should succeed.
        """
        self.log('%s STARTED' % self._testID)

        self.accounts[self.acc1] = {'openvcloud': self.openvcloud}
        self.log('Create an account, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['install'])

        self.log('Add an existing user to A1, should succeed.')
        self.temp_actions['account']['args'] = {'user': {'name': '%s@itsyouonline' % self.vdcuser, 'accesstype': 'R'}}
        self.temp_actions['account']['actions'] = ['user_add']
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['user_add'])

        account = self.get_account(self.acc1)
        self.assertIn('%s@itsyouonline' % self.vdcuser,
                      [user['userGroupId'] for user in account['acl']])

        self.log('Delete an existing user from A1, should succeed.')
        self.temp_actions['account']['actions'] = ['user_delete']
        self.temp_actions['account']['args'] = {'username': '%s@itsyouonline' % self.vdcuser}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['user_delete'])
        account = self.get_account(self.acc1)
        self.assertNotIn('%s@itsyouonline' % self.vdcuser,
                         [user['userGroupId'] for user in account['acl']])
                         
    @unittest.skip('https://github.com/openvcloud/0-templates/issues/95')
    def test005_account_add_delete_non_existing_user(self):
        """ ZRT-OVC-021
        *Test case for adding and deleting  non-existing user from account. *

        **Test Scenario:**

        #. Create an account (A1).
        #. Add a non-existing user to A1, should fail.
        #. Delete a non-existing user from A1, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.accounts[self.acc1] = {'openvcloud': self.openvcloud}
        self.log('Create an account, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['install'])

        self.log('Add non-existing user to A1, should fail.')
        fake_user = self.random_string()
        self.temp_actions['account']['args'] = {'user': {'name': '%s@itsyouonline'%fake_user, 'accesstype': 'R'}}
        self.temp_actions['account']['actions'] = ['user_add']
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        result = self.wait_for_service_action_status(self.acc1, res[self.acc1]['user_add'])
        self.assertTrue(result)
        self.assertIn('no vdcuser service found with name "%s"'%fake_user, result)

        self.log('Delete non-existing user from A1, should fail.')
        fake_user = self.random_string()
        self.temp_actions['account']['actions'] = ['user_delete']
        self.temp_actions['account']['args'] = {'username': '%s@itsyouonline' % fake_user}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        result = self.wait_for_service_action_status(self.acc1, res[self.acc1]['user_delete'])
        self.assertTrue(result)
        self.assertIn('no vdcuser service found with name "%s"'%fake_user, result)
