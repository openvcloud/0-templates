import time
import unittest
from framework.ovc_utils.utils import OVC_BaseTest
from collections import OrderedDict
from random import randint
from nose_parameterized import parameterized


class BasicTests(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(BasicTests, self).__init__(*args, **kwargs)

    def setUp(self):
        super(BasicTests, self).setUp()
        self.acc1 = self.random_string()
        self.cs1 = self.random_string()
        self.vdcuser = self.random_string()
        self.vdcusers[self.vdcuser] = {'openvcloud': self.openvcloud,
                                       'provider': 'itsyouonline',
                                       'email': '%s@test.com' % self.random_string(),
                                       'groups': ['user']}
        self.accounts = {self.acc1: {'openvcloud': self.openvcloud}}
        self.cloudspaces = dict()

        self.temp_actions = {'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']},
                             'vdc': {'actions': ['install']}
                             }
        self.CLEANUP["accounts"].append(self.acc1)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/47')
    def test001_create_cloudspace_with_wrong_params(self):
        """ ZRT-OVC-005
        *Test case for creating acloudspace with wrong parameters .*

        **Test Scenario:**
        #. Create an cloudspace with providing non existing parameter, should fail.
        #. Create an cloudspace with non-existing account , should fail.
        #. Create an cloudspace without providing account parameter, should fail.
        #. Create an cloudspace with providing non existing user, should fail
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create an cloudspace with providing non existing parameter, should fail')
        self.cloudspaces[self.cs1] = {'account': self.acc1, self.random_string(): self.random_string()}
        res = self.create_cs(openvcloud=self.openvcloud, accounts=self.accounts, vdcusers=self.vdcusers,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res, 'parameter provided is wrong')

        self.log('Create an cloudspace with non-exist account , should fail')
        self.cloudspaces[self.cs1] = {'account': self.random_string}
        res = self.create_cs(openvcloud=self.openvcloud, accounts=self.accounts, vdcusers=self.vdcusers,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res, "account doesn't exist")

        self.log('Create an cloudspace with providing non existing user, should fail')
        self.cloudspaces[self.cs1] = {'account': self.acc1,
                                      'users': OrderedDict([('name', self.random_string()),
                                                            ('accesstype', 'CXDRAU')])}
        res = self.create_cs(openvcloud=self.openvcloud, accounts=self.accounts, vdcusers=self.vdcusers,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertIn('no vdcuser found', res)

        self.log('Create an cloudspace without providing account parameter, should fail')
        self.cloudspaces[self.cs1] = {}
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res, 'account is required')

        self.log('%s ENDED' % self._testID)

    @unittest.skip("https://github.com/openvcloud/0-templates/issues/49")
    def test002_create_cloudspaces(self):
        """ ZRT-OVC-006
        *Test case for testing create more than cloudspace.*

        **Test Scenario:**

        #. Create 2 cloudspaces  with right parametrs , should succeed.
        #. Check that the cloudspaces have been created.
        """
        self.log('%s STARTED' % self._testID)
        cs2 = self.random_string()
        self.cloudspaces[self.cs1] = {'account': self.acc1}
        self.cloudspaces[cs2] = {'account': self.acc1}

        self.log('Create two cloudspaces, should succeed.')
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log('Check that the cloudspaces have been created.')
        cloudspace1 = self.get_cloudspace(self.cs1)
        self.assertEqual(cloudspace1['status'], 'DEPLOYED')
        cloudspace2 = self.get_cloudspace(cs2)
        self.assertEqual(cloudspace2['status'], 'DEPLOYED')

        self.log('%s ENDED' % self._testID)

    @parameterized.expand([("Negative values", -1),
                           ("Positive values", 1)])
    def test003_create_cloudspace_with_different_limitaions(self, type, factor):
        """ ZRT-OVC-007
        *Test case for creating cloudspaces with different limitaions*

        **Test Scenario:**

        #. Create cloudspace with different limitations , should succeed.
        #. Check that the cloudspaces have been created with right limitaions.
        #. Create cloudspace with negative values on limitations, should fail.
        """
        self.log('%s STARTED' % self._testID)

        CU_D = randint(2, 1000) * factor
        CU_C = randint(2, 1000) * factor
        CU_I = randint(2, 1000) * factor
        CU_M = randint(2, 1000) * factor
        CU_NP = randint(2, 1000) * factor
        self.cloudspaces[self.cs1] = {'account': self.acc1, 'maxMemoryCapacity': CU_M,
                                      'maxCPUCapacity': CU_C, 'maxDiskCapacity': CU_D,
                                      'maxNumPublicIP': CU_I, 'maxNetworkPeerTransfer': CU_NP
                                    }

        self.log("Create cloudspace with %s limitations , should %s."%(type, "succeed" if factor == 1 else "fail"))
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])
        cloudspace = self.get_cloudspace(self.cs1)
        if type == "Negative values":
            self.assertFalse(cloudspace)
        else:
            self.assertTrue(cloudspace)

            self.log('Check that the cloudspaces have been created with right limitaions')
            self.assertEqual(cloudspace['status'], 'DEPLOYED')
            self.assertEqual(cloudspace['resourceLimits']['CU_D'], CU_D)
            self.assertEqual(cloudspace['resourceLimits']['CU_C'], CU_C)
            self.assertEqual(cloudspace['resourceLimits']['CU_I'], CU_I)
            self.assertEqual(cloudspace['resourceLimits']['CU_M'], CU_M)
            self.assertEqual(cloudspace['resourceLimits']['CU_NP'], CU_NP)
            self.assertIn('gig_qa_1@itsyouonline', [user['userGroupId'] for user in cloudspace['acl']])

        self.log('%s ENDED' % self._testID)

    def test004_update_cloudspace__params(self):
        """ ZRT-OVC-008
        *Test case for updating account's parameters*

        **Test Scenario:**

        #. Create an cloudspace[CS1], should succeed.
        #. Update cloudspace parameters, should succeed.

        """

        self.log('%s STARTED' % self._testID)

        CU_D = randint(10, 1000)
        CU_C = randint(10, 1000)
        CU_I = randint(10, 1000)
        CU_M = randint(10, 1000)
        CU_NP = randint(10, 1000)
        self.cloudspaces[self.cs1] = {'account': self.acc1, 'maxMemoryCapacity': CU_M,
                                      'maxCPUCapacity': CU_C, 'maxDiskCapacity': CU_D,
                                      'maxNumPublicIP': CU_I, 'maxNetworkPeerTransfer': CU_NP
                                      }

        self.log("Create an cloudspace[CS1], should succeed. ")
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])
        cloudspace = self.get_cloudspace(self.cs1)

        self.log("Update cloudspace parameters, should succeed.")
        temp_actions = {'vdc': {'actions': ['update'], 'args': {"maxMemoryCapacity": CU_M+1, "maxCPUCapacity": CU_C-1,
                                                                "maxDiskCapacity": CU_D+1, "maxNumPublicIP": CU_I-1,
                                                                "maxNetworkPeerTransfer": CU_NP+1}, 'service': self.cs1}}

        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])
        cloudspace = self.get_cloudspace(self.cs1)
        self.assertEqual(cloudspace['status'], 'DEPLOYED')
        self.assertEqual(cloudspace['resourceLimits']['CU_M'], CU_M+1)
        self.assertEqual(cloudspace['resourceLimits']['CU_C'], CU_C-1)
        #self.assertEqual(cloudspace['resourceLimits']['CU_D'], CU_D+1)
        self.assertEqual(cloudspace['resourceLimits']['CU_I'], CU_I-1)
        self.assertEqual(cloudspace['resourceLimits']['CU_NP'], CU_NP+1)

        self.log('%s ENDED' % self._testID)

    @unittest.skip("https://github.com/openvcloud/0-templates/issues/74")
    def test005_update_non_exist_cloudspace(self):
        """ ZRT-OVC-009
        *Test case for updating non_exist cloudspace *

        **Test Scenario:**

        #. Update non-exist cloudspace parameters, should succeed.

        """

        self.log('%s STARTED' % self._testID)
        fake_cloudspace = self.random_string()
        CU_M = randint(10, 1000)
        self.cloudspaces[self.cs1] = {'account': self.acc1, 'maxMemoryCapacity': CU_M
                                      }

        self.log("Create an cloudspace[CS1], should succeed. ")
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log("Update cloudspace parameters, should succeed.")
        temp_actions = {'vdc': {'actions': ['update'], 'args': {"maxMemoryCapacity": CU_M+1}, 'service': fake_cloudspace}}

        self.cloudspaces = {fake_cloudspace: {'account': self.acc1, 'maxMemoryCapacity': CU_M}}
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.assertEqual(res, "cloudspace doesn't exist")

        self.log('%s ENDED' % self._testID)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/55')
    def test006_update_cloudspace_with_fake_user(self):
        """ ZRT-OVC-010
        *Test case for updating cloudspace with fake user*

        **Test Scenario:**

        #. Create an cloudspace with an existing user, should succeed.
        #. Update the cloudspace with fake user, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.accounts[self.acc1] = {'openvcloud': self.openvcloud,
                                    'users': OrderedDict([('name', self.vdcuser),
                                                          ('accesstype', 'CXDRAU')])}

        CU_M = randint(10, 1000)
        self.cloudspaces[self.cs1] = {'account': self.acc1, 'maxMemoryCapacity': CU_M
                                      }
        self.log("Create an cloudspace[CS1], should succeed. ")
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log('Update the account with fake user, should fail')
        temp_actions = {'vdc': {'actions': ['update'], 'args': {"maxMemoryCapacity": CU_M+1}, 'service': self.cs1}}
        self.cloudspaces[self.cs1].update({'users': {'name': self.random_string()}})
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.assertIn('no vdcuser found', res)

        self.log('%s ENDED' % self._testID)

    def test007_uninstall_cloudspace(self):
        """ ZRT-OVC-011
        *Test case for unistall cloudspace *

        **Test Scenario:**

        #. Create an cloudspace[CS1], should succeed. 
        #. Uninstall an cloudspace [CS1], should succeed.
        #. Check that cloudspace [CS1] uninstall sucessfuly , should succeed.
        """
        self.log('%s STARTED' % self._testID)
        self.cloudspaces[self.cs1] = {'account': self.acc1}

        self.log("Create an cloudspace[CS1], should succeed. ")
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log(' Uninstall an cloudspace [CS1], should succeed.')
        temp_actions = {'vdc': {'actions': ['uninstall']}}

        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])
    
        self.log("Check that cloudspace [CS1] uninstall sucessfuly , should succeed.")
        self.assertTrue(self.wait_for_cloudspace_status(self.cs1, "DESTROYED"))

        self.log('%s ENDED' % self._testID)

    def test008_Disable_and_Enable_cloudspace(self):
        """ ZRT-OVC-012
        *Test case for testing disable and enable cloudspace. *

        **Test Scenario:**

        #. Create an cloudspace[CS1], should succeed. 
        #. Disable an cloudspace [CS1], should succeed.
        #. Check that cloudspace [CS1] Disabled sucessfuly , should succeed.
        #. Enable an cloudspace[CS1], should succeed.
        #. Check that cloudspace [CS1] Enabled sucessfuly , should succeed.
        """
        self.log('%s STARTED' % self._testID)
        self.cloudspaces[self.cs1] = {'account': self.acc1}

        self.log("Create an cloudspace[CS1], should succeed. ")
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log('Disable an cloudspace [CS1], should succeed.')
        temp_actions = {'vdc': {'actions': ['disable'], 'service': self.cs1}}
        
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])
        self.log("Check that cloudspace [CS1] uninstall sucessfuly , should succeed.")
        self.assertTrue(self.wait_for_cloudspace_status(self.cs1, "DISABLED"))

        self.log("Enable an cloudspace[CS1], should succeed.")
        temp_actions = {'vdc': {'actions': ['enable'], 'service': self.cs1}}
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]) 

        self.log("Check that cloudspace [CS1] Enabled sucessfuly , should succeed.")
        self.assertTrue(self.wait_for_cloudspace_status(self.cs1))

        self.log('%s ENDED' % self._testID)

    def test009_add_and_delete_user_to_cloudspace(self):
        """ ZRT-OVC-013
        *Test case for adding and deleting user to cloudspace *

        **Test Scenario:**

        #. Create an cloudspace[CS1], should succeed. 
        #. Create new user[U1], should succeed.
        #. Add User[U1] to cloudspace[CS1] , should succeed.
        #. Check that user[U1] added to cloudspace [CS1] sucessfuly , should succeed.
        #. Delete User [U1] from cloudspace[CS1], should succeed.
        #. Check that user[U1] deleted from cloudspace [CS1] sucessfuly , should succeed.
        """

        self.log('%s STARTED' % self._testID)
        self.cloudspaces[self.cs1] = {'account': self.acc1}

        self.log("Create an cloudspace[CS1], should succeed. ")
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])
        
        self.log("Create user [U1] ,should succeed.")
        user = self.random_string()
        vdcuser = {user: {'openvcloud': self.openvcloud,
                          'provider': 'itsyouonline',
                          'email': '%s@test.com' % self.random_string(),
                          'groups': ['user']}}
        
        temp_actions = {'vdcuser': {'actions': ['install']}}
        res = self.create_user(openvcloud=self.openvcloud, vdcusers=vdcuser, temp_actions=temp_actions)

        self.log('Add User[U1] to cloudspace[CS1] , should succeed.')
        temp_actions = {'vdc': {'actions': ['user_delete'], 'service': self.cs1, 
                                'args': {'user': {'name': user,'accesstype': 'R'}}}}
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log("Check that user[U1] added to cloudspace [CS1] sucessfuly , should succeed.")
        cloudspace = self.get_cloudspace(self.cs1)
        self.assertIn('%s@itsyouonline' % user,
                      [user['userGroupId'] for user in cloudspace['acl']])

        self.log("Delete User [U1] from cloudspace[CS1], should succeed.")
        temp_actions = {'vdc': {'actions': ['user_add'], 'service': self.cs1, 
                                'args': {'username': user}}}
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                             cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log("Check that user[U1] added to cloudspace [CS1] sucessfuly , should succeed.")
        cloudspace = self.get_cloudspace(self.cs1)
        self.assertNotIn('%s@itsyouonline' % user,
                      [user['userGroupId'] for user in cloudspace['acl']])

        self.log('%s ENDED' % self._testID)
