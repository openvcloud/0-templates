from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError

class Openvcloud(TemplateBase):

    version = '0.0.1'
    template_name = "openvcloud"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)


    def validate(self):
        for key in ['name', 'address', 'token', 'location']:
            if not self.data[key]:
                raise ValueError('%s is required' % key)

    def get_info(self):
        """
        Return info of ovc connection if successfully installed
        """

        self.state.check('actions', 'install', 'ok')
        return {
            'name' : self.data['name'],
            'location' : self.data['location'],
            'address' : self.data['address'],
        }

    def _configure(self):
        ovc = j.clients.openvcloud.get(
            self.data['name'],
            {
                'address': self.data['address'],
                'jwt_': self.data['token'],
                'port': self.data.get('port', 443),
                'location': self.data['location']
            },
            create=True
        )

        # save config
        ovc.config.save()

    def install(self):
        """
        Configure ovc connection
        """
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        self._configure()
        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        """
        Delete ovc connection from config manager on zrobot machine
        """

        conf_manager = j.tools.configmanager
        conf_manager.delete(location="j.clients.openvcloud", instance=self.data['name'])
        self.state.delete('actions', 'install')

    def update(self, address=None, token=None, port=None):
        """
        Update data and reconfigure ovc connection
        """
        self.state.check('actions', 'install', 'ok')
        kwargs = locals()

        for key in ['address', 'token', 'port']:
            value = kwargs[key]
            if value is not None:
                self.data[key] = value

        self._configure()
