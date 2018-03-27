import os

from unittest import TestCase

from zerorobot import config, template_collection

class TestZrobot(TestCase):
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
                "data": {"node" : "dummy value"},
                "valid": True,
                "msg": "node is a valid argument",
            },
            {
                "data": {"port" : "dummy value"},
                "valid": True,
                "msg": "port is a valid argument",
            },
            {
                "data": {"templates" : "dummy value"},
                "valid": True,
                "msg": "templates is a valid argument",
            },
            {
                "data": {"description" : "dummy value", "templates" : "dummy value"},
                "valid": True,
                "msg": "description and templates are valid arguments",
            },
            {
                "data": {"foo" : "dummy value"},
                "valid": False,
                "msg": "foo is an invalid argument",
            },
            {
                "data": {"nodes" : "dummy value"},
                "valid": False,
                "msg": "nodes is an invalid argument",
            },
            {
                "data": {"template" : "dummy value"},
                "valid": False,
                "msg": "template is an invalid argument",
            },
            {
                "data": {"description" : "dummy value", "foo" : "dummy value"},
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
