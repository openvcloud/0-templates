from js9 import j
import os

from unittest import TestCase

from zerorobot import config, template_collection

class TestNode(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )

    def test_validate_args(self):
        tt = [
            {
                "data": {"description" : "dummy value"},
                "valid": True,
                "msg": "description is a valid argument",
            },
            {
                "data": {"vdc" : "dummy value"},
                "valid": True,
                "msg": "vdc is a valid argument",
            },
            {
                "data": {"osImage" : "dummy value"},
                "valid": True,
                "msg": "osImage is a valid argument",
            },
            {
                "data": {"sizeId" : "dummy value"},
                "valid": True,
                "msg": "sizeId is a valid argument",
            },
            {
                "data": {"vCpus" : "dummy value"},
                "valid": True,
                "msg": "vCpus is a valid argument",
            },
            {
                "data": {"memSize" : "dummy value"},
                "valid": True,
                "msg": "memSize is a valid argument",
            },
            {
                "data": {"ports" : "dummy value"},
                "valid": True,
                "msg": "ports is a valid argument",
            },
            {
                "data": {"machineId" : "dummy value"},
                "valid": True,
                "msg": "machineId is a valid argument",
            },
            {
                "data": {"ipPublic" : "dummy value"},
                "valid": True,
                "msg": "ipPublic is a valid argument",
            },
            {
                "data": {"ipPrivate" : "dummy value"},
                "valid": True,
                "msg": "ipPrivate is a valid argument",
            },
            {
                "data": {"sshLogin" : "dummy value"},
                "valid": True,
                "msg": "sshLogin is a valid argument",
            },
            {
                "data": {"sshPassword" : "dummy value"},
                "valid": True,
                "msg": "sshPassword is a valid argument",
            },
            {
                "data": {"disks" : "dummy value"},
                "valid": True,
                "msg": "disks is a valid argument",
            },
            {
                "data": {"bootDiskSize" : "dummy value"},
                "valid": True,
                "msg": "bootDiskSize is a valid argument",
            },
            {
                "data": {"dataDiskSize" : "dummy value"},
                "valid": True,
                "msg": "dataDiskSize is a valid argument",
            },
            {
                "data": {"dataDiskFilesystem" : "dummy value"},
                "valid": True,
                "msg": "dataDiskFilesystem is a valid argument",
            },
            {
                "data": {"dataDiskMountpoint" : "dummy value"},
                "valid": True,
                "msg": "dataDiskMountpoint is a valid argument",
            },
            {
                "data": {"uservdc" : "dummy value"},
                "valid": True,
                "msg": "uservdc is a valid argument",
            },
            {
                "data": {"sshKey" : "dummy value"},
                "valid": True,
                "msg": "sshKey is a valid argument",
            },
            {
                "data": {"managedPrivate" : "dummy value"},
                "valid": True,
                "msg": "managedPrivate is a valid argument",
            },
            {
                "data": {"managedPrivate" : "dummy value", "bootDiskSize" : "dummy value"},
                "valid": True,
                "msg": "managedPrivate and bootDiskSize are valid arguments",
            },
            {
                "data": {"foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
            {
                "data": {"dataDiskFilesystemx" : "dummy value"},
                "valid": False,
                "msg": "dataDiskFilesystemx is an invalid argument",
            },
            {
                "data": {"ipPrivat" : "dummy value"},
                "valid": False,
                "msg": "ipPrivat is an invalid argument",
            },
            {
                "data": {"vdc" : "dummy value", "foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
        ]
        
        name = 'test'
        instance = self.type(name)

        for tc in tt:
            result = False

            try:
                instance._validate_args(data=tc['data'])
                result = True
            except Exception as err:
                print(err)
                if not isinstance(err, ValueError):
                    self.fail(msg="received unexpected exception:\n\t%s" % (str(err)))
            
            self.assertEqual(tc['valid'], result, tc['msg'])
