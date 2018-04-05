from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError

class Vdcuser(TemplateBase):

    version = '0.0.1'
    template_name = "vdcuser"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        for key in ['email']:
            if key not in self.data:
                raise ValueError('"%s" is required' % key)

        if not self.data['openvcloud']:
            raise ValueError('openvcloud is mandatory')


        if not self.data['name']:
            raise ValueError('name is mandatory')

        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=self.data['openvcloud'])

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

    @property
    def ovc(self):
        return j.clients.openvcloud.get(self.data['openvcloud'])

    def get_fqid(self):
        '''
        Returns the full openvcloud username (username@provider).
        Raises StateCheckError when install was not successfully run before.
        '''
        self.state.check('actions', 'install', 'ok')
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
        username = self.get_fqid()
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
        username = self.get_fqid()
        emails = [self.data['email']]

        client.api.system.usermanager.editUser(
            username=username,
            groups=groups,
            provider=self.data['provider'],
            emails=emails
        )

        self.data['groups'] = groups
