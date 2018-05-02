from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Vdcuser(TemplateBase):

    version = '0.0.1'
    template_name = "vdcuser"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        self._ovc = None

    def validate(self):
        """
        Validate service data received during creation
        """

        for key in ['name', 'email', 'openvcloud']:
            if not self.data[key]:
                raise ValueError('%s is required' % key)

    @property
    def ovc(self):
        """
        Get ovc client
        """
        if not self._ovc:
            # get ovc instance name
            proxy = self.api.services.get(
                template_uid=self.OVC_TEMPLATE, name=self.data['openvcloud'])
            ovc_info = proxy.schedule_action(action='get_info').wait().result
            self._ovc = j.clients.openvcloud.get(ovc_info['name'])

        return self._ovc

    def get_info(self):
        """ Return vdcuser info """
        self.state.check('actions', 'install', 'ok')
        return {
            'name': self._get_fqid(),
            'groups': self.data['groups'],
        }

    def _get_fqid(self):
        """
        Returns the full openvcloud username (username@provider).
        """
        provider = self.data.get('provider')
        return "%s@%s" % (self.data.get('name'), provider) if provider else self.data.get('name')

    def install(self):
        """
        Install vdcuser
        """

        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # create user if it doesn't exists
        username = self._get_fqid()
        provider = self.data['provider']
        password = self.data['password']
        email = self.data['email']

        client = self.ovc
        if not client.api.system.usermanager.userexists(name=username):
            groups = self.data['groups']
            client.api.system.usermanager.create(
                username=self.data['name'],
                password=password,
                groups=groups,
                emails=[email],
                domain='',
                provider=provider
            )

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        """
        unauthorize user to all consumed vdc
        """
        client = self.ovc
        try:
            username = self._get_fqid()
        except StateCheckError:
            # skip uninstall as install was not run before
            return

        if client.api.system.usermanager.userexists(name=username):
            client.api.system.usermanager.delete(username=username)

        self.state.delete('actions', 'install')

    def groups_set(self, groups):
        """
        Set user groups

        :param groups: list of groups
        """
        self.state.check('actions', 'install', 'ok')
        client = self.ovc

        if set(groups) == set(self.data['groups']):
            return

        # update groups
        username = self._get_fqid()
        emails = [self.data['email']]

        client.api.system.usermanager.editUser(
            username=username,
            groups=groups,
            provider=self.data['provider'],
            emails=emails
        )

        self.data['groups'] = groups
