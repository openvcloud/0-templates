from unittest import TestCase
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile
import shutil
import os
import pytest

from js9 import j
from zerorobot.template.base import TemplateBase
from nodeovc import Nodeovc

class TestNodeovc(TemplateBase):

    def test_invalid_data(self):
        """
        Test creating a vm with invalid data
        """
        with pytest.raises(ValueError, message='template should fail to instantiate if data dict is missing the node'):
            Nodeovc(name='node_ovc_test', data={})

        with pytest.raises(ValueError, message='template should fail to instantiate if data dict is missing the node'):
            Nodeovc(name='node_ovc_test', data={'node': 'node'})