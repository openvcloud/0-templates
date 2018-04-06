from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError

class Vdcuser(TemplateBase):

    version = '0.0.1'
    template_name = "vdcuser"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        self._ovc_instance = None

    def validate(self):
        '''
        Validate service data received during creation
        '''

        for key in ['name', 'email', 'openvcloud']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

    def _get_proxy(self, template_uid, service_name):
        '''
        Get proxy object of the service of type @template_uid with name @service_name
        '''

        matches = self.api.services.find(template_uid=template_uid, name=service_name)
        if len(matches) != 1:
            raise RuntimeError('found %d services with name "%s", required exactly one' % (len(matches), service_name))
        return matches[0]

    @property
    def ovc(self):
        '''
        Get ovc client
        '''
        if not self._ovc_instance:
            # get ovc instance name
            self._ovc_proxy = self._get_proxy(self.OVC_TEMPLATE, self.data['openvcloud'])
            task = self._ovc_proxy.schedule_action('get_name')
            task.wait()
            self._ovc_instance = task.result
        return j.clients.openvcloud.get(self._ovc_instance)

    def get_name(self):
        '''
        Returns the full openvcloud username (username@provider).
        Raises StateCheckError when install was not successfully run before.
        '''
        self.state.check('actions', 'install', 'ok')
        return self._get_fqid()

    def _get_fqid(self):
        '''
        Returns the full openvcloud username (username@provider).
        '''
        provider = self.data.get('provider')
        return "%s@%s" % (self.data.get('name'), provider) if provider else self.data.get('name')

    def install(self):
        '''
        Install vdcuser
        '''
        
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # create user if it doesn't exists
        username = self._get_fqid()
        password = self.data['password']
        email = self.data['email']

        provider = self.data.get('provider')
        password = password if not provider else \
            j.data.idgenerator.generatePasswd(8, '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

        client = self.ovc
        if not client.api.system.usermanager.userexists(name=username):
            groups = self.data['groups']
            client.api.system.usermanager.create(
                username=username,
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
            username = self.get_fqid()
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
