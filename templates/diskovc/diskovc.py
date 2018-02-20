from js9 import j
from zerorobot.template.base import TemplateBase

class Diskovc(TemplateBase):

    version = '0.0.1'
    template_name = "diskovc"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        
        self._ovc = None
    
    def validate(self):
        data = self.data
        # Get object for an OVC service, make sure exactly one is running
        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=data.get('openvcloud', None))
        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        data['openvcloud'] = ovcs[0].name
        
        # ensure uploaded key
        self.sshkey

        # ensure that disk has a valid type
        if data['type']  and data['type'].upper() not in ["D", "B"]:
            raise j.exceptions.Input("diskovc's type must be data (D) or boot (B) only")

        # ensure that limits are given correctly
        if (data['maxIOPS'] or data['totalIopsSec']) and (data['readIopsSec'] or data['writeIopsSec']):
            raise j.exceptions.Input("total and read/write of iops_sec cannot be set at the same time")

        if data['totalBytesSec'] and (data['readBytesSec'] or data['writeBytesSec']):
            raise j.exceptions.Input("total and read/write of bytes_sec cannot be set at the same time")

        if data['totalBytesSecMax'] and (data['readBytesSecMax'] or data.writeBytesSecMax):
            raise j.exceptions.Input("total and read/write of bytes_sec_max cannot be set at the same time")

        if data['totalIopsSecMax'] and (data['readIopsSecMax'] or data['writeIopsSecMax']):
            raise j.exceptions.Input("total and read/write of iops_sec_max cannot be set at the same time")


    def update_data(self, data):
        # merge new data
        self.data.update(data)
        
        self.save()

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        self._ovc = j.clients.openvcloud.get(self.data['openvcloud'])
        return self._ovc        


    def create(self):
        data = self.data
        ovc = self.ovc

        data['diskId'] = account.create_disk(
            name=data['name'],
            gid=data['location']['gid'],
            description=service.model.data.description,
            size=service.model.data.size,
            type=service.model.data.type,
            ssd_size=service.model.data.ssdSize
        )
        service.saveAll()        