import time
from testconfig import config
from framework.constructor import constructor
from js9 import j


class OVC_BaseTest(constructor):

    env = config['main']['environment']

    def __init__(self, *args, **kwargs):
        super(OVC_BaseTest, self).__init__(*args, **kwargs)
        self.ovc_client = self.ovc_client()

    def setUp(self):
        super(OVC_BaseTest, self).setUp()
        self.openvcloud = self.random_string()
        self.vdcusers = [{'gig_qa_1': {'openvcloud': self.openvcloud,
                                       'provider': 'itsyouonline',
                                       'email': 'dina.magdy.mohammed+123@gmail.com'}}]

    def iyo_jwt(self):
        ito_client = j.clients.itsyouonline.get(instance="main")
        return ito_client.jwt

    def ovc_client(self):
        data = {'address': OVC_BaseTest.env,
                'port': 443
                }
        return j.clients.openvcloud.get(instance='main', data=data)

    def handle_blueprint(self, yaml, *args, **kwargs):
        kwargs['token'] = self.iyo_jwt()
        blueprint = self.create_blueprint(yaml, **kwargs)
        return self.execute_blueprint(blueprint)

    def create_account(self, *args, **kwargs):
        return self.handle_blueprint('account.yaml', *args, **kwargs)

    def create_cs(self, *args, **kwargs):
        return self.handle_blueprint('vdc.yaml', *args, **kwargs)

    def create_vm(self, *args, **kwargs):
        return self.handle_blueprint('vm.yaml', *args, **kwargs)

    def get_cloudspace(self, name):
        time.sleep(2)
        cloudspaces = self.ovc_client.api.cloudapi.cloudspaces.list()
        for cs in cloudspaces:
            if cs['name'] == name:
                return cs
        return False

    def get_account(self, name):
        time.sleep(2)
        accounts = self.ovc_client.api.cloudapi.accounts.list()
        for account in accounts:
            if account['name'] == name:
                return self.ovc_client.api.cloudapi.accounts.get(accountId=account['id'])
        return False
