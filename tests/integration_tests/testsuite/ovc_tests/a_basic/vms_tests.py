import unittest
from framework.ovc_utils.utils import OVC_BaseTest
from collections import OrderedDict
from random import randint
import unittest
import time


class BasicTests(OVC_BaseTest):
    def __init__(self, *args, **kwargs):
        super(BasicTests, self).__init__(*args, **kwargs)

    def setUp(self):
        super(BasicTests, self).setUp()
        self.vdcuser = self.random_string()
        self.vdcuser_name = self.random_string()
        self.vdcusers[self.vdcuser] = {'name': self.vdcuser_name,
                                      'openvcloud': self.openvcloud,
                                      'provider': 'itsyouonline',
                                      'email': '%s@test.com' % self.random_string(),
                                      'groups': ['user']}
        self.acc1 = self.random_string()
        self.acc1_name = self.random_string()
        self.accounts = {self.acc1: {'name': self.acc1_name, 'openvcloud': self.openvcloud}}
        self.cs1 = self.random_string()
        self.cs1_name = self.random_string()
        self.vm1 = self.random_string()
        self.vm1_name = self.random_string()
        self.cloudspaces = {self.cs1: {'name': self.cs1_name, 'account': self.acc1}}
        self.vms = dict()
        self.temp_actions = {'sshkey': {'actions': ['install'], 'service': self.key},
                             'openvcloud': {'actions': ['install'], 'service': self.openvcloud},
                             'account': {'actions': ['install'], 'service': self.acc1},
                             'vdcuser': {'actions': ['install'], 'service': self.vdcuser},
                             'vdc': {'actions': ['install'], 'service': self.cs1},
                             'node': {'actions': ['install']}}
        self.CLEANUP["accounts"].append(self.acc1)

    def tearDown(self):
        temp_actions = {'node': {'actions': ['uninstall']}}
        if self.check_if_service_exist(self.cs1):
            res = self.create_vm(vms=self.vms, accounts=self.accounts,
                                 cloudspaces=self.cloudspaces, temp_actions=temp_actions)
            self.wait_for_service_action_status(self.vm1, res[self.vm1]['uninstall'])

        temp_actions = {'vdc': {'actions': ['uninstall'], 'service': self.cs1}}
        if self.check_if_service_exist(self.cs1):
            res = self.create_cs(accounts=self.accounts, cloudspaces=self.cloudspaces,
                                 temp_actions=temp_actions)
            self.wait_for_service_action_status(self.cs1, res[self.cs1]['uninstall'])
        super(BasicTests, self).tearDown()

    @unittest.skip('https://github.com/openvcloud/0-templates/issues/47')
    def test001_create_vm_with_wrong_params(self):
        """ ZRT-OVC-012
        *Test case for creating virtual machine with wrong parameters*

        **Test Scenario:**

        #. Create an vm without providing sshKey parameter, should fail.
        #. Create a vm without providing vdc parameter, should fail.
        #. Create a vm with providing non existing parameter, should fail.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create a vm without providing sshKey parameter, should fail.')
        self.vms[self.vm1] = {'name': self.vm1_name, 'vdc': self.cs1}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertEqual(res, 'sshKey is required')

        self.log('Create a vm without providing vdc parameter, should fail.')
        self.vms[self.vm1] = {'name': self.vm1_name, 'sshKey': self.key}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertEqual(res, 'vdc name should be given')

        self.log('Create a vm with providing non existing parameter, should fail.')
        self.vms[self.vm1].update({'name': self.vm1_name, 'vdc': self.cs1, self.random_string(): self.random_string()})
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertEqual(res, 'parameter provided is wrong')

        self.log('Create a vm with providing non existing user, should fail')
        self.vms[self.vm1] = {'name': self.vm1_name, 'sshKey': self.key, 'vdc': self.cs1,
                              'users': OrderedDict([('name', self.random_string()),
                                                    ('accesstype', 'CXDRAU')])}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertIn('no vdcuser found', res)

        self.log('%s ENDED' % self._testID)

    def test002_create_vms_with_correct_params(self):
        """ ZRT-OVC-013
        Test case for creating virtual machine with correct parameters*

        **Test Scenario:**

        #. Create two vms, should succeed.
        #. Check if the 1st vm's parameters are reflected correctly on OVC.
        #. Check if the 2nd vm is created, should succeed.
        """
        self.log('%s STARTED' % self._testID)

        self.log('Create two vms, should succeed')
        self.vms[self.vm1] = {'name': self.vm1_name, 'sshKey': self.key, 'vdc': self.cs1}
        self.vm2 = self.random_string()
        self.vm2_name = self.random_string()
        self.vdcuser = self.random_string()
        self.vdcuser_name = self.random_string()
        self.vdcusers[self.vdcuser] = {'name': self.vdcuser_name,
                                       'openvcloud': self.openvcloud,
                                       'provider': 'itsyouonline',
                                       'email': '%s@test.com' % self.random_string(),
                                       'groups': ['user']}
        bds = randint(10, 20)
        dds = randint(10, 20)
        self.vms[self.vm2] = {'name': self.vm2_name, 'sshKey': self.key, 'vdc': self.cs1,
                              'bootDiskSize': bds, 'dataDiskSize': dds}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=self.temp_actions)
        self.assertEqual(type(res), type(dict()))
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['install'])
        self.wait_for_service_action_status(self.vm2, res[self.vm2]['install'])

        self.log("Check if the 1st vm's parameters are reflected correctly on OVC")
        self.cs1_id = self.get_cloudspace(self.cs1_name)['id']
        vm = self.get_vm(cloudspaceId=self.cs1_id, vmname=self.vm1_name)
        self.assertTrue(vm, "No vm has been found")
        self.assertEqual(self.cs1_id, vm['cloudspaceid'])

        self.log('Check if the 2nd vm is created, should succeed')
        vm2 = self.get_vm(cloudspaceId=self.cs1_id, vmname=self.vm2_name)
        self.assertTrue(vm2, "No vm has been found")
        self.assertEqual([disk['sizeMax'] for disk in vm2['disks'] if disk['type'] == 'B'][0], bds)
        self.assertEqual([disk['sizeMax'] for disk in vm2['disks'] if disk['type'] == 'D'][0], dds)
        self.assertEqual(vm2['memory'], 512)
        self.assertEqual(vm2['vcpus'], 1)

        self.log('%s ENDED' % self._testID)

    #@unittest.skip('https://github.com/openvcloud/0-templates/issues/125')
    def test003_get_vm_info(self):
        """ ZRT-OVC-025
        *Test case for getting vm info*

        **Test Scenario:**

        #. Create an account (A1).
        #. Create Cloudspace (C1).
        #. Create Cloudspace (VM1).
        #. Get VM1 and check its info.
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
            data={'name': vdc_name, 'account': account_ser_name}
        )
        vdc.schedule_action('install')
        vdc.schedule_action('install').wait(die=True, timeout=120)

        self.log('Create Cloudspace (VM1)')
        sshkey_ser_name = self.random_string()
        sshkey_name = self.random_string()
        sshkey = self.robot.services.create(
            template_uid="{}/sshkey/{}".format(self.repo, self.version),
            service_name=sshkey_ser_name,
            data={'name': sshkey_name,
                  'dir': '/root/.ssh/',
                  'passphrase': self.random_string()}
        )
        sshkey.schedule_action('install')

        vm_ser_name = self.random_string()
        vm_name = self.random_string()
        node = self.robot.services.create(template_uid="{}/node/{}".format(self.repo, self.version),
            service_name=vm_ser_name,
            data={'name': vm_name,
                  'sshKey': sshkey_ser_name,
                  'vdc': vdc_ser_name}
        )
        node.schedule_action('install')
        node.schedule_action('install').wait(die=True, timeout=200)

        self.log('Get VM1 and check its info')
        node_info = node.schedule_action('get_info').wait(die=True, timeout=30).result
        self.assertEqual(vm_name, node_info['name'])
        self.assertEqual(vdc_ser_name, node_info['vdc'])
        self.assertEqual(2, len(node_info['disk_services']))
        ovc.schedule_action('uninstall')
        node.schedule_action('uninstall')
        time.sleep(10)
        vdc.schedule_action('uninstall')
        time.sleep(10)
        account.schedule_action('uninstall')
        node.delete()
        vdc.delete()
        account.delete()
        ovc.delete()
        sshkey.delete()

        self.log('%s ENDED' % self._testID)


class vmactions(OVC_BaseTest):
    key = None
    def __init__(self, *args, **kwargs):
        super(vmactions, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        self = cls()
        super(vmactions, self).setUp()
        vmactions.key = self.key
        cls.acc1 = self.random_string()
        cls.acc1_name = self.random_string()
        cls.cs1 = self.random_string()
        cls.cs1_name = self.random_string()
        cls.vm1 = self.random_string()
        cls.vm1_name = self.random_string()
        cls.vdcuser = self.random_string()
        cls.vdcuser_name = self.random_string()
        cls.openvcloud = self.openvcloud
        cls.accounts = {cls.acc1: {'name': self.acc1_name, 'openvcloud': cls.openvcloud}}
        cls.cloudspaces = {cls.cs1: {'name': self.cs1_name, 'account': cls.acc1}}
        cls.vms = {cls.vm1: {'name': self.vm1_name, 'sshKey': vmactions.key, 'vdc': self.cs1}}
        self.vdcusers[cls.vdcuser] = {'name': cls.vdcuser_name,
                                      'openvcloud': cls.openvcloud,
                                      'provider': 'itsyouonline',
                                      'email': '%s@test.com' % self.random_string(),
                                      'groups': ['user']}
        cls.vdcusers = self.vdcusers
        cls.temp_actions = {'openvcloud': {'actions': ['install'], 'service': cls.openvcloud},
                            'account': {'actions': ['install'], 'service': cls.acc1},
                            'vdcuser': {'actions': ['install'], 'service': cls.vdcuser},
                            'vdc': {'actions': ['install'], 'service': cls.cs1},
                            'node': {'actions': ['install']},
                            'sshkey': {'actions':['install'], 'service': vmactions.key}}
        self.log('Create vm, should succeed')
        res = self.create_vm(accounts=cls.accounts, cloudspaces=cls.cloudspaces,
                             vms=cls.vms, temp_actions=cls.temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['install'])
        self.CLEANUP["accounts"].append(cls.acc1)

    def tearDown(self):
        pass

    #@unittest.skip('https://github.com/openvcloud/0-templates/issues/126')
    def test002_start_stop_vm(self):
        """ ZRT-OVC-015
        *Test case for testing start and stop vm .*

        **Test Scenario:**

        #. Create a vm[vm1], should succeed.
        #. Stop [VM1], should succceed.
        #. Check that [VM1] is halted.
        #. Strat [VM1], should succeed.
        #. Check that [VM1] is running.
        """
        self.log('%s STARTED' % self._testID)

        self.log("Stop [VM1], should succceed.")
        temp_actions = {'node': {'actions': ['stop'], 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['stop'])

        self.log(" Check that [VM1] is halted.")
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        self.assertTrue(self.wait_for_vm_status(cloudspaceId, self.vm1_name, status='HALTED'))

        self.log("Start [VM1], should succceed.")
        temp_actions = {'node': {'actions': ['start'], 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['start'])

        self.log(" Check that [VM1] is running.")
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        self.assertTrue(self.wait_for_vm_status(cloudspaceId, self.vm1_name))

    #@unittest.skip('https://github.com/openvcloud/0-templates/issues/126')
    def test003_pause_and_resume(self):
        """ ZRT-OVC-016
        *Test case for testing pause and resume vm .*

        **Test Scenario:**

        #. Create a vm[vm1], should succeed.
        #. Pause [VM1], should succceed.
        #. Check that [VM1] is PAUSED.
        #. Resume [VM1], should succeed.
        #. Check that [VM1] is running.
        """
        self.log('%s STARTED' % self._testID)

        self.log("Pause [VM1], should succceed..")
        temp_actions = {'node': {'actions': ['pause'], 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['pause'])

        self.log("Check that [VM1] is PAUSED.")
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        self.assertTrue(self.wait_for_vm_status(cloudspaceId, self.vm1_name, status='PAUSED'))

        self.log("Resume [VM1], should succeed.")
        temp_actions = {'node': {'actions': ['resume'], 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['resume'])

        self.log("Check that [VM1] is running.")
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        self.assertTrue(self.wait_for_vm_status(cloudspaceId, self.vm1_name))

    def test004_clone_vm(self):
        """ ZRT-OVC-017
        *Test case for testing clone vm .*

        **Test Scenario:**

        #. Create a vm[vm1], should succeed.
        #. Stop [VM1], should succeed.
        #. Clone VM1 as [VM2_C], should succeed.
        #. Check that the cloned vm[VM2_C] has been created and got ip address.
        #. Check that the cloned vm[VM2_C] has same [VM1] memory ,Vcpu number and disksize .
        """
        self.log('%s STARTED' % self._testID)

        self.log("Stop [VM1], should succeed.")
        temp_actions = {'node': {'actions': ['stop'], 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['stop'])
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        self.assertTrue(self.wait_for_vm_status(cloudspaceId, self.vm1_name, status='HALTED'))

        self.log(" Clone VM1 as [VM2_C], should succeed.")
        vm2_c_name = self.random_string()
        temp_actions = {'node': {'actions': ['clone'], 'service': self.vm1,
                        'args': {'clone_name': vm2_c_name}}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['clone'])

        self.log("Check that the cloned vm[VM2_C] has been created and got ip address.")
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        vm1 = self.get_vm(cloudspaceId, self.vm1_name)
        vm2_c = self.get_vm(cloudspaceId, vm2_c_name)
        self.assertTrue(vm2_c)
        self.assertTrue(vm2_c["interfaces"][0]['ipAddress'])

        self.log("Check that [VM2_C] has same [VM1] memory ,Vcpu number and disksize.")
        self.assertEqual(vm2_c["status"], "RUNNING")
        self.assertEqual(vm2_c["memory"], vm1["memory"])
        self.assertEqual(vm2_c["vcpus"], vm1["vcpus"])
        self.assertEqual(vm2_c["sizeid"], vm1["sizeid"])

    @unittest.skip("https://github.com/openvcloud/0-templates/issues/122")
    def test005_snapshot_of_machine(self):
        """ ZRT-OVC-018
        *Test case for testing create and delete snapshot of machine .*

        **Test Scenario:**

        #. Create a vm[vm1], should succeed.
        #. Create a snapshot[sn] of [vm1], should succeed.
        #. Check that the snapshot[sn] has been created.
        #. Delete the snapshot[sn], should succeed.
        #. Check that the snapshot[sn] has been deleted.
        """
        self.log('%s STARTED' % self._testID)

        self.log("Create snapshot[sn] of [vm1], should succeed.")
        temp_actions = {'node': {'actions': ['snapshot'], 'service': self.vm1}}

        res = self.create_vm(keys=vmactions.key, accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['snapshot'])

        self.log("Check that the snapshot[sn] has been created.")
        time.sleep(2)
        snapshots = self.get_snapshots_list(self.cs1_name, self.vm1_name)
        self.assertTrue(snapshots)

        self.log("Delete the snapshot[sn], should succeed.")
        sn_epoch = snapshots[0]["epoch"]
        temp_actions = {'node': {'actions': ['snapshot_delete'], 'service': self.vm1, 'args': {'snapshot_epoch': sn_epoch}}}
        res = self.create_vm(keys=vmactions.key, accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['snapshot_delete'])

        self.log("Check that the snapshot[sn] has been deleted.")
        time.sleep(2)
        self.assertFalse(self.get_snapshots_list(self.cs1_name, self.vm1_name))

    @unittest.skip("https://github.com/openvcloud/0-templates/issues/122")
    def test006_rollback_of_machine(self):
        """ ZRT-OVC-019
        *Test case for testing snapshot rollback of machine .*

        **Test Scenario:**

        #. Create a vm[vm1], should succeed.
        #. Create snapshots[sn1],[sn2] and [sn3] of [vm1], should succeed.
        #. Stop [vm1], should succeed.
        #. Rollback to [sn2], should succeed.
        #. Check that [sn3] has been deleted.
        """
        self.log('%s STARTED' % self._testID)

        self.log("Create snapshots[sn1],[sn2] and [sn3] of [vm1], should succeed.")
        temp_actions = {'node': {'actions': ['snapshot'], 'service': self.vm1}}
        for _ in range(3):
            res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                                 vms=self.vms, temp_actions=temp_actions)
            self.wait_for_service_action_status(self.vm1, res[self.vm1]['snapshot'])
            time.sleep(2)
        snapshots_before_rollback = self.get_snapshots_list(self.cs1_name, self.vm1_name)

        self.log("Stop [VM1], should succeed.")
        temp_actions = {'node': {'actions': ['stop'], 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['stop'])

        self.log("Rollback to [sn2], should succeed.")
        temp_actions = {'node': {'actions': ['snapshot_rollback'], 'service': self.vm1,
                                 'args': {'snapshot_epoch': snapshots_before_rollback[1]["epoch"]}}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)

        self.log("Check that [sn3] has been deleted.")
        snapshots_after_rollback = self.get_snapshots_list(self.cs1_name, self.vm1_name)
        self.assertNotIn(snapshots_before_rollback[2]["name"], [sn["name"] for sn in snapshots_after_rollback])
        self.assertEqual(len(snapshots_after_rollback), 2)

    def test007_add_and_delete_disk_from_vm(self):
        """ ZRT-OVC-020
        *Test case for testing add and delete disk from vm. *

        **Test Scenario:**

        #. Create vm1, should succeed.
        #. Add disk to vm1, should succeed.
        #. Check that disk has been added to vm successfully.
        #. Delete disk from vm1, should succeed.
        #. Check that disk has been deleted successfully.
        """

        self.log('%s STARTED' % self._testID)

        self.log("Add disk to vm1, should succeed.")
        disk_name = self.random_string()
        disk_size = randint(10, 50)
        temp_actions = {'node': {'actions': ['disk_add'], 'args': {"name": disk_name, "size": disk_size}, 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['disk_add'])

        self.log("Check that disk has been added to vm successfully.")
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        self.assertTrue(self.wait_for_disk(cloudspaceId, self.vm1_name, disk_name))
        diskid = next(disk for disk in self.get_vm(cloudspaceId, self.vm1_name)['disks'] if disk["name"] == disk_name)['id']

        temp_actions = {'node': {'actions': ['disk_delete'], 'args': {"disk_service_name": "Disk{}".format(diskid)}, 'service': self.vm1}}
        res = self.create_vm(accounts=self.accounts, cloudspaces=self.cloudspaces,
                             vms=self.vms, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['disk_delete'])

        self.log("Check that disk has been deleted successfully.")
        self.assertTrue(self.wait_for_disk(cloudspaceId, self.vm1_name,disk_name, "non-exist"))

    def test008_create_and_delete_disk(self):
        """ ZRT-OVC-021
        *Test case for testing create and delete disk. *

        **Test Scenario:**

        #. Create a disk[D1], should succeed.
        #. Check that disk[D1] has been created.
        #. Delete the disk [D1], should succeed.
        #. Check that the disk [D1] has been deleted.
        """
        self.log('%s STARTED' % self._testID)

        self.log("Create a disk[D1], should succeed.")

        disk = self.random_string()
        disk_name = self.random_string()
        disks = {disk: {"name": disk_name, "vdc": self.cs1}}
        self.temp_actions = {'disk': {'actions': ['install'], 'service': disk}}
        res = self.create_disk(accounts=self.accounts, cloudspaces=self.cloudspaces, disks=disks, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(disk, res[disk]['install'])
        self.log("Check that disk[D1] has been created.")
        disk_list = self.get_disks_list(self.acc1_name)
        self.assertIn(disk_name, [disk["name"] for disk in disk_list])

        self.log("Delete the disk [D1], should succeed.")
        self.temp_actions["disk"] = {"actions": ["uninstall"], "service": disk}
        res = self.create_disk(accounts=self.accounts, cloudspaces=self.cloudspaces, disks=disks, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(disk, res[disk]['uninstall'])

        self.log("Check that the disk [D1] has been deleted.")
        disk_list = self.get_disks_list(self.acc1_name)
        self.assertNotIn(disk_name, [disk["name"] for disk in disk_list])

    def test009_update_disk(self):
        """ ZRT-OVC-022
        *Test case for updating disk. *

        **Test Scenario:**

        #. Create a disk[D1], should succeed.
        #. Update disk[D1], should succceed.
        #. Check that the disk [D1] has been updated successfully.
        """
        self.log('%s STARTED' % self._testID)
        self.log("Create a disk[D1], should succeed.")
        disk = self.random_string()
        disk_name = self.random_string()
        disks = {disk: {"name": disk_name, "vdc": self.cs1}}
        self.temp_actions = {'disk': {'actions': ['install'], 'service': disk}}
        res = self.create_disk(accounts=self.accounts, cloudspaces=self.cloudspaces, disks=disks, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(disk, res[disk]['install'])

        self.log("Update disk[D1], should succceed.")
        disktype = "B"
        self.temp_actions["disk"] = {"actions": ["update"], "args": {"writeBytesSec": disktype}, "service": disk}
        res = self.create_disk(accounts=self.accounts, cloudspaces=self.cloudspaces, disks=disks, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(disk, res[disk]['update'])
        self.assertEqual(self.get_disks_list(self.acc1_name)[0]['type'], disktype)

    def test009_attach_dettach_disk(self):
        """ ZRT-OVC-023
        *Test case for attaching and dettaching disk. *

        **Test Scenario:**

        #. Create a disk[D1], should succeed.
        #. Attach disk [D1] to vm, should succeed.
        #. Check that the disk [D1] has been attached successfully.
        #. Deattach disk[D1] from vm, should succeed.
        """
        self.log('%s STARTED' % self._testID)
        self.log("Create a disk[D1], should succeed.")
        disk = self.random_string()
        disk_name = self.random_string()
        disks = {disk: {"name": disk_name, "vdc": self.cs1}}
        self.temp_actions = {'disk': {'actions': ['install'], 'service': disk}}
        res = self.create_disk(key=vmactions.key, accounts=self.accounts, cloudspaces=self.cloudspaces, disks=disks, temp_actions=self.temp_actions)
        self.wait_for_service_action_status(disk, res[disk]['install'])
        diskid = next(disk for disk in self.get_disks_list(self.acc1_name) if disk["name"] == disk_name)['id']

        self.log("Attach disk [D1] to vm, should succeed.")
        temp_actions = {'node': {'actions': ['disk_attach'],'args': {"disk_service_name": disk}, 'service': self.vm1}}
        res = self.create_disk(key=vmactions.key, accounts=self.accounts, cloudspaces=self.cloudspaces,
                               vms=self.vms, disks=disks, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['disk_attach'])

        self.log("Check that disk has been added to vm successfully.")
        time.sleep(5)
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        vm = self.get_vm(cloudspaceId, self.vm1_name)
        self.assertIn(disk_name, [disk['name'] for disk in vm['disks']])

        self.log("Deattach disk[D1] from vm, should succeed")
        temp_actions = {'node': {'actions': ['disk_detach'],'args': {"disk_service_name": disk}, 'service': self.vm1}}
        res = self.create_disk(key=vmactions.key, accounts=self.accounts, cloudspaces=self.cloudspaces,
                               vms=self.vms, disks=disks, temp_actions=temp_actions)
        self.wait_for_service_action_status(self.vm1, res[self.vm1]['disk_detach'])

        self.log("Check that disk has been deattached to vm successfully.")
        time.sleep(5)
        cloudspaceId = self.get_cloudspace(self.cs1_name)['id']
        vm = self.get_vm(cloudspaceId, self.vm1_name)
        self.assertNotIn(disk_name, [disk['name'] for disk in vm['disks']])

    @classmethod
    def tearDownClass(cls):
        self = cls()
        temp_actions = {'node': {'actions': ['uninstall']}}
        if self.check_if_service_exist(cls.vm1):
            res = self.create_account(keys=vmactions.key, openvcloud=cls.openvcloud, vdcusers=self.vdcusers,
                                      accounts=self.accounts, temp_actions=temp_actions)
            self.wait_for_service_action_status(self.vm1, res[self.vm1]['uninstall'])

        temp_actions = {'vdc': {'actions': ['uninstall'], 'service': cls.cs1}}
        if self.check_if_service_exist(cls.cs1):
            res = self.create_account(openvcloud=cls.openvcloud, vdcusers=self.vdcusers,
                                      accounts=self.accounts, temp_actions=temp_actions)
            self.wait_for_service_action_status(self.cs1, res[self.cs1]['uninstall'])

        temp_actions = {'account': {'actions': ['uninstall'], 'service': cls.acc1}}
        if self.check_if_service_exist(cls.acc1):
            res = self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                      accounts=self.accounts, temp_actions=temp_actions)
            self.wait_for_service_action_status(self.acc1, res[self.acc1]['uninstall'], timeout=20)
        self.delete_services()
