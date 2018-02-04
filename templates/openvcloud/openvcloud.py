from js9 import j
from zerorobot.template.base import TemplateBase


class Openvcloud(TemplateBase):

    version = '0.0.1'
    template_name = "openvcloud"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._validate_data()

        ovc = j.clients.openvcloud.new(
            name,
            {
                'address': data['address'],
                'login': data['login'],
                'appkey_': data['token'],
                'port': data.get('port', 443)
            }
        )

        print(ovc)

    def _validate_data(self):
        for key in ['address', 'login', 'token']:
            if key not in self.data:
                raise ValueError('%s is required' % key)
