import time
from zerorobot.dsl.ZeroRobotAPI import ZeroRobotAPI
from framework.utils.utils import OVC_BaseTest
from collections import OrderedDict


class BasicTests(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(BasicTests, self).__init__(*args, **kwargs)

    def setUp(self):
        super(BasicTests, self).setUp()
        self.openvcloud = self.random_string()
        self.vdcusers = [{'kheirj': {'openvcloud': self.openvcloud,
                                     'provider': 'itsyouonline',
                                     'email': 'kheirj@greenitglobe.com'}}]
        self.acc1 = self.random_string()
        self.cs1 = self.random_string()
        self.accounts = [{self.acc1: {'openvcloud': self.openvcloud}}]
        self.cloudspaces = [{self.cs1: {'account': self.acc1}}]

    def test001_trial(self):
        """ ZRT-OVC-001
        *Test case for ...*

        **Test Scenario:**

        #. Create an account and 2 cloudspaces, should succeed.
        #. check that the cloudspaces have been created.
        """
        self.log('%s STARTED' % self._testID)

        self.cs2 = self.random_string()
        self.vdcuser = self.random_string()
        self.vdcusers.extend([{self.vdcuser: {'openvcloud': self.openvcloud,
                                              'provider': 'itsyouonline',
                                              'email': 'abdelmab@greenitglobe.com'}}])
        self.cloudspaces.extend([{self.cs2: {'account': self.acc1,
                                             'users': OrderedDict([('name', self.vdcuser),
                                                                   ('accesstype', 'CXDRAU')])}}])
        self.temp_actions = {'account': {'actions': ['install']},
                             'vdcuser': {'actions': ['install']}, 'vdc': ['install']}

        self.log('Create 1 account and 2 cloudspaces, should succeed')
        self.create_cs(openvcloud=self.openvcloud, vdcusers=self.vdcusers, accounts=self.accounts,
                       cloudspaces=self.cloudspaces, temp_actions=self.temp_actions)

        # wait till blueprint is executed
        self.wait_for_service_action_status(self.cs2)

        self.log('check that the cloudspaces have been created')
        self.assertTrue(self.get_cloudspace(self.cs1))
        self.assertTrue(self.get_cloudspace(self.cs2))

        #check on the cloudspaces params

        self.log('%s ENDED' % self._testID)

    def tearDown(self):
        self.temp_actions = {'account': {'actions': ['uninstall']}}
        self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                            accounts=self.accounts, temp_actions=self.temp_actions)
        self.delete_services()
