from js9 import j
from zerorobot.template.base import TemplateBase


class Vdcuser(TemplateBase):

    version = '0.0.1'
    template_name = "vdcuser"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        self._validate_data()

    def _validate_data(self):
        for key in ['email']:
            if key not in self.data:
                raise ValueError('"%s" is required' % key)

        OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
        ovcs = self.api.services.find(template_uid=OVC_TEMPLATE, name=self.data.get('openvcloud', None))

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['openvcloud'] = ovcs[0].name

    @property
    def ovc(self):
        return j.clients.openvcloud.get(self.data['openvcloud'])

    def install(self):
        # create user if it doesn't exists
        username = self.name
        password = self.data['password']
        email = self.data['email']

        provider = self.data['provider']
        username = "%s@%s" % (username, provider) if provider else username
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
        # unauthorize user to all consumed vdc
        username = self.name
        client = self.ovc
        provider = self.data['provider']
        username = "%s@%s" % (username, provider) if provider else username
        if client.api.system.usermanager.userexists(name=username):
            client.api.system.usermanager.delete(username=username)


def processChange(job):
    service = job.service
    g8client = service.producers["g8client"][0]
    config_instance = "{}_{}".format(g8client.aysrepo.name, g8client.model.data.instance)
    client = j.clients.openvcloud.get(instance=config_instance, create=False, die=True, sshkey_path="/root/.ssh/ays_repos_key")
    old_args = service.model.data
    new_args = job.model.args
    # Process Changing Groups
    old_groups = set(old_args.groups)
    new_groups = set(new_args.get('groups', []))
    if old_groups != new_groups:
        username = service.model.dbobj.name
        provider = old_args.provider
        username = "%s@%s" % (username, provider) if provider else username
        # Editing user api requires to send a list contains user's mail
        emails = [old_args.email]
        new_groups = list(new_groups)
        client.api.system.usermanager.editUser(username=username, groups=new_groups, provider=provider, emails=emails)
        service.model.data.groups = new_groups
        service.save()

