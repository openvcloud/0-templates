from js9 import j
from zerorobot.template.base import TemplateBase


class Sshkey(TemplateBase):

    version = '0.0.1'
    template_name = "sshkey"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        if 'path' not in self.data or self.data['path'] == '':
            raise ValueError('path is required')

        j.clients.ssh.load_ssh_key(self.data['path'])
