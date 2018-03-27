from js9 import j
from zerorobot.template.base import TemplateBase


class Openvcloud(TemplateBase):

    version = '0.0.1'
    template_name = "openvcloud"

    # allowed service arguments
    _ARGS = [
        'description',
        'address',
        'port',
        'token',
        'location',
    ]

    def __init__(self, name, guid=None, data=None):
        self._validate_args(data)
        super().__init__(name=name, guid=guid, data=data)

        self._validate_data()
        self._configure()

    def _validate_data(self):
        for key in ['address', 'token', 'location']:
            if not self.data[key]:
                raise ValueError('%s is required' % key)

    def _validate_args(self, data):
        """
        Validates if provided data object contains supported args
        """
        if data is None:
            return

        for arg in data:
            if arg not in self._ARGS:
                raise ValueError('%s is not a supported argument' % str(arg))

    def _configure(self):
        ovc = j.clients.openvcloud.get(
            self.name,
            {
                'address': self.data['address'],
                'jwt_': self.data['token'],
                'port': self.data.get('port', 443),
                'location': self.data['location']
            },
            create=True
        )

        # No, the create flag is not enough, we need to save
        ovc.config.save()

    def update(self, address=None, login=None, token=None, port=None):
        kwargs = locals()

        for key in ['address', 'token', 'port']:
            value = kwargs[key]
            if value is not None:
                self.data[key] = value

        self._configure()

    def install(self):
        # we do nothing in install, but we add it to make calling install
        # on all services easier
        pass
