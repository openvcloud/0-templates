import os
import uuid
import logging
import time
import unittest
from js9 import j
from testconfig import config
from requests.exceptions import HTTPError
from jinja2 import Environment, FileSystemLoader
from zerorobot.dsl.ZeroRobotAPI import ZeroRobotAPI
from zerorobot.cli import utils


class constructor(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(constructor, self).__init__(*args, **kwargs)
        templatespath = './framework/utils/templates'
        self.j2_env = Environment(loader=FileSystemLoader(searchpath=templatespath), trim_blocks=True)
        self.j2_env.globals.update(random_string=self.random_string)
        self.j2_env.globals.update(config_params=self.config_params)
        self.api = ZeroRobotAPI()

    def setUp(self):
        self._testID = self._testMethodName
        self._startTime = time.time()
        self._logger = logging.LoggerAdapter(logging.getLogger('openvcloud_testsuite'),
                                             {'testid': self.shortDescription() or self._testID})

    def random_string(self):
        return str(uuid.uuid4())[0:8]

    def config_params(self, param):
        return config['main'][param]

    def log(self, msg):
        self._logger.info(msg)

    def create_blueprint(self, yaml, **kwargs):
        """
        yaml file that is used for blueprint creation
        """
        blueprint = self.j2_env.get_template('base.yaml').render(services=yaml,
                                                                 actions='actions.yaml',
                                                                 **kwargs)
        return blueprint

    def execute_blueprint(self, blueprint):
        os.system('echo "{0}" >> /tmp/{1}_{2}.yaml'.format(blueprint, self._testID,
                                                           self.random_string()))
        instance, _ = utils.get_instance()
        client = j.clients.zrobot.get(instance)
        content = j.data.serializer.yaml.loads(blueprint)
        data = {'content': content}
        try:
            tasks, _ = client.api.blueprints.ExecuteBlueprint(data)
            result = dict()
            for task in tasks:
                result[task.service_name] = task.guid
            return result
        except HTTPError as err:
            msg = err.response.json()['message']
            self.log('message: %s' % msg)
            self.log('code: %s' % err.response.json()['code'])
            return msg

    def delete_services(self):
        for r in self.api.robots.keys():
            robot = self.api.robots[r]
            for service in robot.services.names.values():
                service.delete()

    def wait_for_service_action_status(self, servicename, task_guid,
                                       action='install', timeout=100):
        for r in self.api.robots.keys():
            robot = self.api.robots[r]
            service = robot.services.names[servicename]
            task = service.task_list.get_task_by_guid(task_guid)
            if task.action_name == action:
                for i in range(timeout):
                    time.sleep(1)
                    if task.state != 'new':
                        break
                break

    def check_if_service_exist(self, servicename):
        for r in self.api.robots.keys():
            robot = self.api.robots[r]
            if servicename in robot.services.names.keys():
                return True
            return False
