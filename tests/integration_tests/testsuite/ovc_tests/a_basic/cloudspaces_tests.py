import time
import unittest
from framework.utils.utils import OVC_BaseTest
from collections import OrderedDict
from random import randint


class BasicTests(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(BasicTests, self).__init__(*args, **kwargs)

    def setUp(self):
        super(BasicTests, self).setUp()
        self.acc1 = self.random_string()
        self.cs1 = self.random_string()
        self.cloudspaces = [{self.cs1: {'account': self.acc1}}]
        self.accounts = [{self.acc1: {'openvcloud': self.openvcloud}}]
        self.temp_actions = {'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']},
                             'vdc':{'actions':['install']}}

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/47')
    def test001_create_cloudspace_with_wrong_params(self):
        """ ZRT-OVC-001
        *Test case for creating acloudspace with wrong parameters .*

        **Test Scenario:**

        #. Create an account without providing account parameter, should fail.
        #. Create an account with providing non existing parameter, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create an cloudspace without providing account parameter, should fail')
        self.cloudspaces = [{self.cs1: {}}]
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                       cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res, 'account is required')

        self.log('Create an cloudspace with providing non existing parameter, should fail')
        self.cloudspaces = [{self.cs1: {'account': self.acc1, self.random_string(): self.random_string()}}]
        res = self.create_cs(openvcloud=self.openvcloud,accounts=self.accounts, vdcusers=self.vdcusers,
                              cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.assertEqual(res,'parameter provided is wrong' )

        self.log('%s ENDED' % self._testID)

    def test002_create_cloudspace(self):
        """ ZRT-OVC-002
        *Test case for ...*

        **Test Scenario:**

        #. Create 2 cloudspaces, should succeed.
        #. Check that the cloudspaces have been created.
        
        """
        self.log('%s STARTED' % self._testID)
        self.cs2 = self.random_string()
        self.cloudspaces.extend([{self.cs2: {'account': self.acc1}}])
        self.log('Create 2 cloudspaces, should succeed.')
        res = self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                       cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(self.cs1, res[self.cs1])

        self.log('Check that the cloudspaces have been created.')
        self.assertTrue(self.get_cloudspace(self.cs1))
        self.assertTrue(self.get_cloudspace(self.cs2))

        self.log('%s ENDED' % self._testID)
