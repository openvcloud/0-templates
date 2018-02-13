from js9 import j
from zerorobot.template.base import TemplateBase

class Nodeovc(TemplateBase):

    version = '0.0.1'
    template_name = "nodeovc"

    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self.data['name'] = name
        self._ovc = None


    def validate(self):
        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=self.data.get('openvcloud', None))

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['openvcloud'] = ovcs[0].name
        
        accounts = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=self.data.get('account', None))

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['account'] = accounts[0].name

        locations = self.ovc.locations

        if len(locations) != 1:
            raise RuntimeError('found %s openvcloud locations, requires exactly 1' % len(locations))

        self.data['location'] = locations[0]['name']

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        self._ovc = j.clients.openvcloud.get(self.data['openvcloud'])
        return self._ovc

    def create_vm(self):
        client = self.ovc

        space = client.space_get(accountName=self.data['account'],
                                 spaceName=self.data['openvcloud'],
                                 location=self.data['location'])
        space.machine_create(name=self.data['name'],
                             sshkeyname='id_rsa',
#                            image=self.data['osImage'],
#                            memsize=self.data['memsize'],
                            # vcpus=self.data['vcpus'],
                            # disksize=self.data['bootDiskSize'],
                            # datadisks=self.data['disks'],
                            # sizeId=self.data['sizeId']
                            )
        import ipdb; ipdb.set_trace()

