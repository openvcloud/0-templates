from js9 import j
import os

from unittest import TestCase

from zerorobot import config, template_collection

class TestAccount(TestCase):
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
        ]
