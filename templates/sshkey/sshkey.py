import paramiko
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Sshkey(TemplateBase):

    version = '0.0.1'
    template_name = "sshkey"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    
    def validate(self):
        '''
        Implements 0-Robot validate
        Validates the sshkey service
        '''

        # validate sshkey name
        if not self.data['name']:
            raise ValueError('name is required')

        # validate passphrase
        if not self.data['passphrase']:
            raise ValueError('passphrase is required')

        if len(self.data['passphrase']) < 5:
            raise ValueError('passphrase must be min of 5 characters')

    def install(self):
        '''
        Installs the ssh key
        '''
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        dir = self.data['dir']
        passphrase = self.data['passphrase']
        name = self.data['name']

        path = j.sal.fs.joinPaths(dir, name)
        if not j.sal.fs.exists(path):
            j.clients.sshkey.key_generate(path, passphrase=passphrase, overwrite=True, returnObj=False)
        else:
            paramiko.RSAKey.from_private_key_file(path, password=passphrase)

        self._get_key()

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        '''
        Uninstalls the sshkey client
        Also deletes the key
        '''
        key = self._get_key()
        key.delete()

        self.state.delete('actions', 'install')

    def _get_key(self):
        """
        returns an SSHKey instance of provided key in provided path
        """
        path = j.sal.fs.joinPaths(self.data['dir'], self.data['name'])
        return j.clients.sshkey.get(
            self.data['name'],
            create=True,
            data={
                'path': path,
                'passphrase_': self.data['passphrase'],
            },
        )

    def get_name(self):
        '''
        Return key name
        '''
        self.state.check('actions', 'install', 'ok')
        return self.data['name']