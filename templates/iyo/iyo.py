from js9 import j
from zerorobot.template.base import TemplateBase


class Iyo(TemplateBase):

    version = '0.0.1'
    template_name = "iyo"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def get_jwt(self):
        if not self.data['token']:
            # look for instance "main", let error if "main" doesn't exist
            client = j.clients.itsyouonline.get('main', create=False)
            self.data['token'] = client.jwt
            self.save()

        return self.data['token']
        
        
