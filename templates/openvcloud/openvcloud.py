from js9 import j
from zerorobot.template.base import TemplateBase


class Openvcloud(TemplateBase):

    version = '0.0.1'
    template_name = "openvcloud"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._validate_data()
        self._configure()

    def _validate_data(self):
        for key in ['address', 'login', 'token']:
            if key not in self.data:
                raise ValueError('%s is required' % key)

    def _configure(self):
        ovc = j.clients.openvcloud.get(
            self.name,
            {
                'address': self.data['address'],
                'login': self.data['login'],
                'appkey_': self.data['token'],
                'port': self.data.get('port', 443)
            },
            create=True
        )

        # No, the create flag is not enough, we need to save
        ovc.config.save()

    def update_data(self, data):
        self.data.update(data)
        self._configure()
