import unittest
from framework.ovc_utils.utils import OVC_BaseTest
from random import randint
from JumpScale9Lib.clients.portal.PortalClient import ApiError
import time

class accounts(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(accounts, self).__init__(*args, **kwargs)

    def setUp(self):
        super(accounts, self).setUp()
        self.acc1 = self.random_string()
        self.acc1_name = self.random_string()
        self.vdcuser = self.random_string()
        self.vdcuser_name = self.random_string()
        self.vdcusers[self.vdcuser] = {'name': self.vdcuser_name,
                                       'openvcloud': self.openvcloud,
                                       'provider': 'itsyouonline',
                                       'email': '%s@test.com' % self.random_string(),
                                       'groups': ['user']}
        self.accounts = dict()
        self.temp_actions = {'openvcloud': {'actions': ['install']},
                             'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']}}
        self.CLEANUP["accounts"].append(self.acc1)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/117')
    def test001_create_account_with_wrong_params(self):
        """ ZRT-OVC-001
        *Test case for creating account with different or missing parameters*

        **Test Scenario:**

        #. Create an account without providing an account name parameter, should fail.
        #. Create an account without providing openvcloud parameter, should fail.
        #. Create an account with providing non existing openvcloud value, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create an account without providing an account name parameter, should fail.')
        self.accounts[self.acc1] = {}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(res, '"name" is required')

        self.log('Create an account without providing openvcloud parameter, should fail')
        self.accounts[self.acc1] = {'name': self.random_string()}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(res, '"openvcloud" is required')

        self.log('Create an account with providing wrong openvcloud value, should fail.')
        self.accounts[self.acc1] = {'name': self.random_string(),
                                    'openvcloud': self.random_string()}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(res, 'found 0 openvcloud connections, requires exactly 1')

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
        self.accounts[self.acc1] = {'openvcloud': self.openvcloud,
                                    'name': self.acc1_name,
                                    'maxMemoryCapacity': CU_M,
                                    'maxCPUCapacity': CU_C, 'maxVDiskCapacity': CU_D,
                                    'maxNumPublicIP': CU_I
                                    }

        self.acc2 = self.random_string()
        account2_name = self.random_string()
        self.accounts[self.acc2] = {'openvcloud': self.openvcloud, 'name': account2_name }
        self.CLEANUP["accounts"].append(self.acc2)

        self.log('Create two accounts, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['install'])
        self.wait_for_service_action_status(self.acc2, res[self.acc2]['install'])

        self.log('Check if the 1st account parameters are reflected correctly on OVC')
        account = self.get_account(self.acc1_name)
        self.assertEqual(account['status'], 'CONFIRMED')
        self.assertEqual(account['resourceLimits']['CU_D'], CU_D)
        self.assertEqual(account['resourceLimits']['CU_C'], CU_C)
        self.assertEqual(account['resourceLimits']['CU_I'], CU_I)
        self.assertEqual(account['resourceLimits']['CU_M'], CU_M)

        self.log('Check if the 2nd accound was created, should succeed.')
        account = self.get_account(account2_name)
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
        self.accounts[self.acc1] = {'name': self.acc1_name, 'openvcloud': self.openvcloud,
                                    'maxMemoryCapacity': CU_M, 'maxCPUCapacity': CU_C,
                                    'maxVDiskCapacity': CU_D, 'maxNumPublicIP': CU_I}

        self.log('Create an account, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['install'])

        self.log('Check if the account parameters are reflected correctly on OVC')
        account = self.get_account(self.acc1_name)
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
        account = self.get_account(self.acc1_name)
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

        self.accounts[self.acc1] = {'name': self.acc1_name, 'openvcloud': self.openvcloud}
        self.log('Create an account, should succeed')
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertTrue(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['install'])

        self.log('Add an existing user to A1, should succeed.')
        self.temp_actions['account']['args'] = {'vdcuser': self.vdcuser, 'accesstype': 'R'}
        self.temp_actions['account']['actions'] = ['user_authorize']
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['user_authorize'])
        account = self.get_account(self.acc1_name)
        self.assertIn('%s@itsyouonline' % self.vdcuser_name,
                      [user['userGroupId'] for user in account['acl']])

        self.log('Delete an existing user from A1, should succeed.')
        self.temp_actions['account']['actions'] = ['user_unauthorize']
        self.temp_actions['account']['args'] = {'vdcuser': self.vdcuser}
        res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                  accounts=self.accounts, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.acc1, res[self.acc1]['user_unauthorize'])
        account = self.get_account(self.acc1_name)
        self.assertNotIn('%s@itsyouonline' % self.vdcuser_name,
                         [user['userGroupId'] for user in account['acl']])

        self.log('%s ENDED' % self._testID)

    def test005_get_account_info(self):
        """ ZRT-OVC-000
        *Test case for getting account info*

        **Test Scenario:**

        #. Create an account (A1).
        #. Get A1 and check its info.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create an account (A1)')
        openvcloud_ser_name = self.random_string()
        ovc = self.robot.services.create(
            template_uid="{}/openvcloud/{}".format(self.repo, self.version),
            service_name=openvcloud_ser_name,
            data={'name': self.random_string(),
                  'location': self.location,
                  'address': self.env,
                  'token': self.iyo_jwt()}
        )
        ovc.schedule_action('install')

        account_ser_name = self.random_string()
        account_name = self.random_string()
        account = self.robot.services.create(
            template_uid="{}/account/{}".format(self.repo, self.version),
            service_name=account_ser_name,
            data={'name': account_name, 'openvcloud': openvcloud_ser_name}
        )
        account.schedule_action('install')

        self.log('Get A1 and check its info')
        acc_info = account.schedule_action('get_info').wait(die=True).result
        self.assertEqual(account_name, acc_info['name'])
        self.assertEqual(openvcloud_ser_name, acc_info['openvcloud'])
        self.assertEqual('CXDRAU', acc_info['users'][0]['accesstype'])
        ovc.schedule_action('uninstall')
        account.schedule_action('uninstall')

        self.log('%s ENDED' % self._testID)

    def test006_set_vdcuser_groups(self):
        """ ZRT-OVC-000
        *Test case for setting vdcuser groups*

        **Test Scenario:**

        #. Create vdc user, should succeed.
        #. Set user groups and check if it was set.
        """
        self.log('%s STARTED' % self._testID)

        self.log(' vdc user, should succeed')
        openvcloud_ser_name = self.random_string()
        ovc = self.robot.services.create(
            template_uid="{}/openvcloud/{}".format(self.repo, self.version),
            service_name=openvcloud_ser_name,
            data={'name': self.random_string(),
                  'location': self.location,
                  'address': self.env,
                  'token': self.iyo_jwt()}
        )
        ovc.schedule_action('install')

        vdcuser_ser_name = self.random_string()
        vdcuser_name = self.random_string()
        vdcuser = self.robot.services.create(
            template_uid="github.com/openvcloud/0-templates/vdcuser/0.0.1",
            service_name=vdcuser_ser_name,
            data={'name': vdcuser_name,
                  'openvcloud': openvcloud_ser_name,
                  'email': '{}@test.com'.format(self.random_string())}
        )
        vdcuser.schedule_action('install')

        self.log('Set user groups and check if it was set')
        vdcuser.schedule_action('groups_set', {'groups': ['level1', 'level2']})
        time.sleep(12)
        user = self.ovc_client.api.system.usermanager.userget(name='{}@itsyouonline'.format(vdcuser_name))
        self.assertIn('level1', user['groups'])
        self.assertIn('level2', user['groups'])

        self.log('Delete vdcuser, should succeed ')
        vdcuser.schedule_action('uninstall')
        try:
            self.ovc_client.api.system.usermanager.userget(name='{}@itsyouonline'.format(vdcuser_name))
        except ApiError as e:
            self.assertEqual(e.response.status_code, 404)
        self.log('%s ENDED' % self._testID)
