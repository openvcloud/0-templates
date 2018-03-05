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
        for key in ['address', 'location']:
            if not self.data[key]:
                raise ValueError('%s is required' % key)

    def _configure(self):
        # find IYO service
        IYO_TEMPLATE = 'github.com/openvcloud/0-templates/iyo/0.0.1'
        matches = self.api.services.find(template_uid=IYO_TEMPLATE, name=self.data['iyo'])
        if len(matches) != 1:
            raise RuntimeError('found %d iyo with name "%s"' % (len(matches), self.data['iyo']))
        iyo = matches[0]
        self.iyo = iyo.name

        # get jwt token from IYO service
        task = iyo.schedule_action('get_jwt')
        task.wait()
        jwt = task.result
        
        # get ovc client
        ovc = j.clients.openvcloud.get(
            self.name,
            {
                'address': self.data['address'],
                'jwt_': jwt,
                'port': self.data.get('port', 443),
                'location': self.data['location']
            },
            create=True
        )

        # No, the create flag is not enough, we need to save
        ovc.config.save()

    def update(self, address=None, port=None):
        kwargs = locals()

        for key in ['address', 'port']:
            value = kwargs[key]
            if value is not None:
                self.data[key] = value

        self._configure()

    def install(self):
        # we do nothing in install, but we add it to make calling install
        # on all services easier
        pass
