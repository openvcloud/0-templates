from js9 import j
from zerorobot.template.base import TemplateBase


class Openvcloud(TemplateBase):

    version = '0.0.1'
    template_name = "openvcloud"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        sshkey_path = self._validate_data()

        ovc = j.clients.openvcloud.get(
            name,
            {
                'address': data['address'],
                'login': data['login'],
                'appkey_': data['token'],
                'port': data.get('port', 443)
            },
            create=True,
            sshkey_path=sshkey_path
        )

        # No, the create flag is not enough, we need to save
        ovc.config.save()

    def _validate_data(self):
        for key in ['address', 'login', 'token']:
            if key not in self.data:
                raise ValueError('%s is required' % key)

        SSHKEY_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
        ssh_keys = self.api.services.find(template_uid=SSHKEY_TEMPLATE, name=self.data.get('sshkey', None))

        if len(ssh_keys) != 1:
            raise RuntimeError('found %s ssh keys, requires exactly 1' % len(ssh_keys))

        sshkey = ssh_keys[0]
        self.data['sshkey'] = sshkey.name

        key, state = sshkey.state.get('path').popitem()
        if state != 'ok':
            raise ValueError('invalid sshkey configured')

        return key
