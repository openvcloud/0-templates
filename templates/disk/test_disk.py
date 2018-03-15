import os

from unittest import TestCase

from zerorobot import config, template_collection

class TestDisk(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
            os.path.dirname(__file__)
        )
    
    def test_validate_args(self):
        tt = [
            {
                "data": {"size" : "dummy value"},
                "valid": True,
                "msg": "size is a valid argument",
            },
            {
                "data": {"type" : "dummy value"},
                "valid": True,
                "msg": "type is a valid argument",
            },
            {
                "data": {"description" : "dummy value"},
                "valid": True,
                "msg": "description is a valid argument",
            },
            {
                "data": {"deviceName" : "dummy value"},
                "valid": True,
                "msg": "deviceName is a valid argument",
            },
            {
                "data": {"diskId" : "dummy value"},
                "valid": True,
                "msg": "diskId is a valid argument",
            },
            {
                "data": {"vdc" : "dummy value"},
                "valid": True,
                "msg": "vdc is a valid argument",
            },
            {
                "data": {"location" : "dummy value"},
                "valid": True,
                "msg": "location is a valid argument",
            },
            {
                "data": {"maxIops" : "dummy value"},
                "valid": True,
                "msg": "maxIops is a valid argument",
            },
            {
                "data": {"totalBytesSec" : "dummy value"},
                "valid": True,
                "msg": "totalBytesSec is a valid argument",
            },
            {
                "data": {"readBytesSec" : "dummy value"},
                "valid": True,
                "msg": "readBytesSec is a valid argument",
            },
            {
                "data": {"writeBytesSec" : "dummy value"},
                "valid": True,
                "msg": "writeBytesSec is a valid argument",
            },
            {
                "data": {"totalIopsSec" : "dummy value"},
                "valid": True,
                "msg": "totalIopsSec is a valid argument",
            },
            {
                "data": {"readIopsSec" : "dummy value"},
                "valid": True,
                "msg": "readIopsSec is a valid argument",
            },
            {
                "data": {"writeIopsSec" : "dummy value"},
                "valid": True,
                "msg": "writeIopsSec is a valid argument",
            },
            {
                "data": {"totalBytesSecMax" : "dummy value"},
                "valid": True,
                "msg": "totalBytesSecMax is a valid argument",
            },
            {
                "data": {"readBytesSecMax" : "dummy value"},
                "valid": True,
                "msg": "readBytesSecMax is a valid argument",
            },
            {
                "data": {"writeBytesSecMax" : "dummy value"},
                "valid": True,
                "msg": "writeBytesSecMax is a valid argument",
            },
            {
                "data": {"totalIopsSecMax" : "dummy value"},
                "valid": True,
                "msg": "totalIopsSecMax is a valid argument",
            },
            {
                "data": {"readIopsSecMax" : "dummy value"},
                "valid": True,
                "msg": "readIopsSecMax is a valid argument",
            },
            {
                "data": {"writeIopsSecMax" : "dummy value"},
                "valid": True,
                "msg": "writeIopsSecMax is a valid argument",
            },
            {
                "data": {"sizeIopsSec" : "dummy value"},
                "valid": True,
                "msg": "sizeIopsSec is a valid argument",
            },
            {
                "data": {"sizeIopsSec" : "dummy value", "readBytesSecMax" : "dummy value"},
                "valid": True,
                "msg": "sizeIopsSec and readBytesSecMax are valid arguments",
            },
            {
                "data": {"foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
            {
                "data": {"totalBytesSecs" : "dummy value"},
                "valid": False,
                "msg": "totalBytesSecs is an invalid argument",
            },
            {
                "data": {"maxIop" : "dummy value"},
                "valid": False,
                "msg": "maxIop is an invalid argument",
            },
            {
                "data": {"location" : "dummy value", "foo" : "dummy value"},
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
