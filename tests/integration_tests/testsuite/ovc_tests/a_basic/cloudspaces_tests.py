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
        self.acc1_name = self.random_string()
        self.vdcuser = self.random_string()
        self.vdcuser_name = self.random_string()
        self.cs1 = self.random_string()
        self.cs1_name = self.random_string()
        self.vdcusers[self.vdcuser] = {'name': self.vdcuser_name,
                                       'openvcloud': self.openvcloud,
                                       'provider': 'itsyouonline',
                                       'email': '%s@test.com' % self.random_string(),
                                       'groups': ['user']}
        self.accounts = {self.acc1: {'name': self.acc1_name, 'openvcloud': self.openvcloud}}
        self.cloudspaces = dict()
        self.temp_actions = {'openvcloud': {'actions': ['install']},
                             'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']},
                             'vdc': {'actions': ['install']}
                             }
        self.CLEANUP["accounts"].append(self.acc1)

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/117')
    def test001_create_cloudspace_with_wrong_params(self):
        """ ZRT-OVC-005
        *Test case for creating a cloudspace with wrong parameters .*

        **Test Scenario:**
        #. Create a cloudspace without providing name parameter, should fail.
        #. Create a cloudspace without providing account parameter, should fail.
        #. Create a cloudspace with non-existing account , should fail.

        """
        self.log('%s STARTED' % self._testID)

        self.log('Create a cloudspace without providing name parameter, should fail')
        self.cloudspaces[self.cs1] = {}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res, 'vdc name is required')

        self.log('Create a cloudspace without providing account parameter, should fail.')
        self.cloudspaces[self.cs1] = {'name': self.cs1_name}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res, 'account service name is required')

        self.log('Create a cloudspace with non-existing account , should fail')
        self.cloudspaces[self.cs1] = {'name': self.cs1_name, 'account': self.random_string}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res, "account doesn't exist")

        self.log('%s ENDED' % self._testID)

    @unittest.skip("Need to be tested on different environment other than be-g8-3")
    def test002_create_cloudspaces(self):
        """ ZRT-OVC-006
        * Test case for testing multiple cloud spaces creation. *

        **Test Scenario:**

        #. Create 2 cloudspaces  with right parametrs , should succeed.
        #. Check that the cloudspaces have been created.
        #. Uninstall the cloudspaces, should succeed.
        #. Check that the cloudspaces have been uninstalled successfully , should succeed.
        """
        self.log('%s STARTED' % self._testID)
        cs2 = self.random_string()
        cs2_name = self.random_string()
        self.cloudspaces[self.cs1] = {'name': self.cs1_name, 'account': self.acc1}
        self.cloudspaces[cs2] = {'name': cs2_name, 'account': self.acc1}

        self.log('Create two cloudspaces, should succeed.')
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['install'])

        self.log('Check that the cloudspaces have been created.')
        cloudspace1 = self.get_cloudspace(self.cs1_name)
        self.assertEqual(cloudspace1['status'], 'DEPLOYED')
        cloudspace2 = self.get_cloudspace(cs2_name)
        self.assertEqual(cloudspace2['status'], 'DEPLOYED')

        self.log(' Uninstall the cloudspaces, should succeed.')
        temp_actions = {'vdc': {'actions': ['uninstall']}}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['uninstall'])

        self.log("Check that cloudspace [CS1] has been uninstalled successfully , should succeed.")
        self.assertTrue(self.wait_for_cloudspace_status(self.cs1_name, "DESTROYED"))

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
        self.cloudspaces[self.cs1] = {'name': self.cs1_name, 'account': self.acc1, 'maxMemoryCapacity': CU_M,
                                      'maxCPUCapacity': CU_C, 'maxVDiskCapacity': CU_D,
                                      'maxNumPublicIP': CU_I, 'maxNetworkPeerTransfer': CU_NP
                                      }
        self.log("Create cloudspace with %s limitations , should %s."%(type, "succeed" if factor == 1 else "fail"))
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['install'])
        time.sleep(2)
        cloudspace = self.get_cloudspace(self.cs1_name)
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

    def test004_get_cloudspace_info(self):
        """ ZRT-OVC-024
        *Test case for getting cloudspace indfo*

        **Test Scenario:**

        #. Create an account (A1).
        #. Create Cloudspace (C1).
        #. Get C1 and check its info.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create an account (A1)')
        openvcloud_ser_name = self.random_string()
        # create services
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

        self.log('Create Cloudspace (C1)')
        vdc_ser_name = self.random_string()
        vdc_name = self.random_string()
        vdc = self.robot.services.create(
            template_uid="{}/vdc/{}".format(self.repo, self.version),
            service_name=vdc_ser_name,
            data={'name': vdc_name , 'account': account_ser_name}
        )
        vdc.schedule_action('install')

        self.log('Get C1 and check its info')
        vdc_info = vdc.schedule_action('get_info').wait(die=True).result
        self.assertEqual(vdc_name, vdc_info['name'])
        self.assertEqual(account_ser_name, vdc_info['account'])
        self.assertEqual('ACDRUX', vdc_info['users'][0]['accesstype'])
        ovc.schedule_action('uninstall')
        vdc.schedule_action('uninstall')
        account.schedule_action('uninstall')

        self.log('%s ENDED' % self._testID)


class CloudspaceActions(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(CloudspaceActions, self).__init__(*args, **kwargs)

    def setUp(self):
        super(CloudspaceActions, self).setUp()

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        self = cls()
        super(CloudspaceActions, self).setUp()
        cls.acc1 = self.random_string()
        cls.acc1_name = self.random_string()
        cls.cs1 = self.random_string()
        cls.cs1_name = self.random_string()
        cls.vdcuser = self.random_string()
        cls.vdcuser_name = self.random_string()
        cls.vdcusers = self.vdcusers
        cls.openvcloud = self.openvcloud
        self.vdcusers[cls.vdcuser] = {'name': cls.vdcuser_name,
                                      'openvcloud': self.openvcloud,
                                      'provider': 'itsyouonline',
                                      'email': '%s@test.com' % self.random_string(),
                                      'groups': ['user']}

        cls.accounts = {cls.acc1: {'name': cls.acc1_name, 'openvcloud': self.openvcloud}}
        cls.cloudspaces = {cls.cs1: {'name': cls.cs1_name, 'account': cls.acc1}}

        cls.temp_actions = {'openvcloud': {'actions': ['install']},
                            'account': {'actions': ['install']},
                            'vdcuser': {'actions': ['install']},
                            'vdc': {'actions': ['install']}
                            }
        cls.cloudspaces[cls.cs1] = {'name': cls.cs1_name, 'account': cls.acc1, 'maxMemoryCapacity': randint(10, 1000),
                                    'maxCPUCapacity': randint(10, 1000), 'maxVDiskCapacity': randint(10, 1000),
                                    'maxNumPublicIP': randint(10, 1000), 'maxNetworkPeerTransfer': randint(10, 1000)
                                    }
        self.log("Create cloudspace , should succeed")
        res = self.create_cs(accounts=cls.accounts, cloudspaces=cls.cloudspaces, temp_actions=cls.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['install'])

        self.CLEANUP["accounts"].append(cls.acc1)

    def test001_update_cloudspace_params(self):
        """ ZRT-OVC-008
        *Test case for updating account's parameters*

        **Test Scenario:**

        #. Create a cloudspace[CS1], should succeed.
        #. Update cloudspace parameters, should succeed.
        """

        self.log('%s STARTED' % self._testID)

        cloudspace = self.get_cloudspace(self.cs1_name)
        CU_D = cloudspace['resourceLimits']["CU_D"]
        CU_C = cloudspace['resourceLimits']["CU_C"]
        CU_I = cloudspace['resourceLimits']["CU_I"]
        CU_M = cloudspace['resourceLimits']["CU_M"]
        CU_NP = cloudspace['resourceLimits']["CU_NP"]

        self.log("Update cloudspace parameters, should succeed.")
        temp_actions = {'vdc': {'actions': ['update'], 'args': {"maxMemoryCapacity": CU_M+1, "maxCPUCapacity": CU_C-1,
                                                                "maxVDiskCapacity": CU_D+1, "maxNumPublicIP": CU_I-1,
                                                                "maxNetworkPeerTransfer": CU_NP+1}, 'service': self.cs1}}

        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['update'])
        cloudspace = self.get_cloudspace(self.cs1_name)
        self.assertEqual(cloudspace['status'], 'DEPLOYED')
        self.assertEqual(cloudspace['resourceLimits']['CU_M'], CU_M+1)
        self.assertEqual(cloudspace['resourceLimits']['CU_C'], CU_C-1)
        self.assertEqual(cloudspace['resourceLimits']['CU_D'], CU_D+1)
        self.assertEqual(cloudspace['resourceLimits']['CU_I'], CU_I-1)
        self.assertEqual(cloudspace['resourceLimits']['CU_NP'], CU_NP+1)

        self.log('%s ENDED' % self._testID)

    def test002_Disable_and_Enable_cloudspace(self):
        """ ZRT-OVC-009
        *Test case for testing disable and enable cloudspace. *

        **Test Scenario:**

        #. Create a cloudspace[CS1], should succeed.
        #. Disable a cloudspace [CS1], should succeed.
        #. Check that cloudspace [CS1] Disabled successfully , should succeed.
        #. Enable a cloudspace[CS1], should succeed.
        #. Check that cloudspace [CS1] Enabled successfully , should succeed.
        """
        self.log('%s STARTED' % self._testID)
        self.log('Disable a cloudspace [CS1], should succeed.')
        temp_actions = {'vdc': {'actions': ['disable'], 'service': self.cs1}}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['disable'])

        self.log("Check that cloudspace [CS1] uninstall successfully , should succeed.")
        self.assertTrue(self.wait_for_cloudspace_status(self.cs1_name, "DISABLED"))

        self.log("Enable a cloudspace[CS1], should succeed.")
        temp_actions = {'vdc': {'actions': ['enable'], 'service': self.cs1}}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['enable'])

        self.log("Check that cloudspace [CS1] Enabled successfully , should succeed.")
        self.assertTrue(self.wait_for_cloudspace_status(self.cs1_name))

        self.log('%s ENDED' % self._testID)

    def test003_add_and_delete_user_to_cloudspace(self):
        """ ZRT-OVC-010
        *Test case for adding and deleting user to cloudspace *

        **Test Scenario:**

        #. Create a cloudspace[CS1], should succeed.
        #. Add User[U1] to cloudspace[CS1] , should succeed.
        #. Check that user[U1] added to cloudspace [CS1] successfully , should succeed.
        #. Delete User [U1] from cloudspace[CS1], should succeed.
        #. Check that user[U1] deleted from cloudspace [CS1] successfully , should succeed.
        """

        self.log('%s STARTED' % self._testID)

        self.log('Add User[U1] to cloudspace[CS1] , should succeed.')
        temp_actions = {'vdc': {'actions': ['user_authorize'], 'service': self.cs1,
                                'args': {'vdcuser': self.vdcuser, 'accesstype': 'R'}}}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['user_authorize'])

        self.log("Check that user[U1] added to cloudspace [CS1] successfully, should succeed.")
        cloudspace = self.get_cloudspace(self.cs1_name)
        self.assertIn('%s@itsyouonline' % self.vdcuser_name,
                      [user['userGroupId'] for user in cloudspace['acl']])

        self.log("Delete User [U1] from cloudspace, should succeed.")
        temp_actions = {'vdc': {'actions': ['user_unauthorize'], 'service': self.cs1,
                                'args': {'vdcuser': self.vdcuser}}}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['user_unauthorize'])

        self.log("Check that user[U1] added to cloudspace [CS1] successfully, should succeed.")
        cloudspace = self.get_cloudspace(self.cs1_name)
        self.assertNotIn('%s@itsyouonline' % self.vdcuser_name,
                         [user['userGroupId'] for user in cloudspace['acl']])

        self.log('%s ENDED' % self._testID)

    @unittest.skip("https://github.com/openvcloud/0-templates/issues/120")
    def test004_add_and_delete_portforward(self):
        """ ZRT-OVC-011
        *Test case for adding and deleting portforward on cloudspaces. *

        **Test Scenario:**

        #. Create a cloudspace[CS1], should succeed.
        #. Create a vm on [CS1], should succeed.
        #. Create portforward for created cloudspace, should succeed.
        #. Check that portforwad  has been added to cloudspace [CS1] successfully , should succeed.
        #. Delete the portforward from [CS1], should succeed.
        #. Check that the portforward  has been deleted from cloudspace [CS1] successfully , should succeed.
        """

        self.log('%s STARTED' % self._testID)
        self.log("Create a vm on [CS1], should succeed.")
        self.temp_actions["node"] = {'actions': ['install']}
        vm = self.random_string()
        vm_name = self.random_string()
        vms = {vm: {'name': vm_name, 'sshKey': self.key, 'vdc': self.cs1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=vms, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(vm, res[vm]['install'])
        cs1_id = self.get_cloudspace(self.cs1_name)['id']
        vmId = self.get_vm(cloudspaceId=cs1_id, vmname=vm_name)['id']
        self.log('Create portforward for created cloudspace, should succeed.')
        public_port = randint(1000, 60000)
        local_port = 22
        temp_actions = {'vdc': {'actions': ['portforward_create'], 'service': self.cs1,
                                'args': {'machineId': vmId,
                                         'port_forwards': OrderedDict([('destination', local_port),('source', public_port)])}}}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['portforward_create'])

        self.log("Check that user[U1] added to cloudspace [CS1] successfully, should succeed.")
        time.sleep(4)
        pf_list = self.get_portforward_list(self.cs1_name, vm_name)
        self.assertIn(public_port, [int(x["publicPort"]) for x in pf_list])

        self.log('Delete the portforward from [CS1], should succeed.')
        temp_actions = {'vdc': {'actions': ['portforward_delete'], 'service': self.cs1,
                                'args': {'machineId': vmId,
                                         'port_forwards': OrderedDict([('destination', local_port),('source', public_port)])}}}
        res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1]['portforward_delete'])

        self.log('Check that the portforward  deleted from cloudspace [CS1] successfully , should succeed.')
        time.sleep(4)
        pf_list = self.get_portforward_list(self.cs1_name, vm_name)
        self.assertNotIn(public_port, [int(x["publicPort"]) for x in pf_list])

    @classmethod
    def tearDownClass(cls):
        self = cls()
        temp_actions = {'vdc': {'actions': ['uninstall']}}
        if self.check_if_service_exist(self.cs1):
            res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                      accounts=self.accounts, temp_actions=temp_actions)
            self.wait_for_service_action_status(self.cs1, res[self.cs1]['uninstall'])

        temp_actions = {'account': {'actions': ['uninstall']}}
        if self.check_if_service_exist(self.acc1):
            res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                      accounts=self.accounts, temp_actions=temp_actions)
            self.wait_for_service_action_status(self.acc1, res[self.acc1]['uninstall'])

        self.delete_services()
