import paramiko
from js9 import j
from zerorobot.template.base import TemplateBase


class Sshkey(TemplateBase):

    version = '0.0.1'
    template_name = "sshkey"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        dir = self.data['dir']
        passphrase = self.data['passphrase']

        path = j.sal.fs.joinPaths(dir, name)
        if not j.sal.fs.exists(path):
            j.clients.sshkey.key_generate(path, passphrase=passphrase, overwrite=True, returnObj=False)
        else:
            paramiko.RSAKey.from_private_key_file(path, password=passphrase)

        j.clients.sshkey.get(
            name,
            create=True,
            data={
                'path': path,
                'passphrase_': passphrase,
            },
        )
    
    def validate(self):
        # validate dir
        if 'dir' not in self.data:
            raise ValueError('dir is required')

        # validate passphrase
        if 'passphrase' not in self.data:
            raise ValueError('passphrase is required')
        if len(self.data['passphrase']) < 5:
            raise ValueError('passphrase must be min of 5 characters')

    def install(self):
        pass

    