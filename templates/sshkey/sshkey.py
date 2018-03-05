from js9 import j
from zerorobot.template.base import TemplateBase


class Sshkey(TemplateBase):

    version = '0.0.1'
    template_name = "sshkey"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        dir = self.data['dir']
        passphrase = self.data['passphrase']

        if dir == '':
            raise ValueError('path is required')

        if len(passphrase) < 5:
            raise ValueError('passphrase must be min of 5 characters')

        path = j.sal.fs.joinPaths(dir, name)
        if not j.sal.fs.exists(path):
            j.clients.sshkey.key_generate(path, passphrase=passphrase, overwrite=True, returnObj=False)

        j.clients.sshkey.get(
            name,
            create=True,
            data={
                'path': path,
                'passphrase_': passphrase,
            },
        )

    def install(self):
        pass

    # def update_data(self, data):
    #     if self.data['path'] == data['path']:
    #         return

    #     old = self.data['path']
    #     self.data.update(data)
    #     self.save()  # making sure data is not breaking the schema before we do key unload

    #     j.clients.ssh.ssh_key_unload(old)
    #     j.clients.ssh.load_ssh_key(self.data['path'])
