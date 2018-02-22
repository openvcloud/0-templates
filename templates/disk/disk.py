from js9 import j
from zerorobot.template.base import TemplateBase

class Disk(TemplateBase):

    version = '0.0.1'
    template_name = "disk"

    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        
        self.data['devicename'] = name
        self._ovc = None
        self._account = None
        self._vdc = None
    
    def validate(self):
        data = self.data
        if not data['vdc']:
            raise RuntimeError('vdc name should be given')

        # ensure that disk has a valid type
        if data['type']  and data['type'].upper() not in ["D", "B"]:
            raise RuntimeError("diskovc's type must be data (D) or boot (B) only")

        # ensure that limits are given correctly
        if (data['maxIOPS'] or data['totalIopsSec']) and (data['readIopsSec'] or data['writeIopsSec']):
            raise RuntimeError("total and read/write of iops_sec cannot be set at the same time")

        if data['totalBytesSec'] and (data['readBytesSec'] or data['writeBytesSec']):
            raise RuntimeError("total and read/write of bytes_sec cannot be set at the same time")

        if data['totalBytesSecMax'] and (data['readBytesSecMax'] or data['writeBytesSecMax']):
            raise RuntimeError("total and read/write of bytes_sec_max cannot be set at the same time")

        if data['totalIopsSecMax'] and (data['readIopsSecMax'] or data['writeIopsSecMax']):
            raise RuntimeError("total and read/write of iops_sec_max cannot be set at the same time")

        # ensure uploaded key
        self.sshkey

    def update_data(self, data):
        # merge new data
        self.data.update(data)
        
        self.save()

    @property
    def sshkey(self):
        """ Get a path and keyname of the sshkey service """

        sshkeys = self.api.services.find(template_uid=self.SSH_TEMPLATE)
        if not len(sshkeys):
            raise RuntimeError('no %s ssh services found' % len(sshkeys))

        # Get key name and path
        path = sshkeys[0].data['path']
        key = path.split('/')[-1]

        return key

    @property
    def vdc(self):
        if self._vdc:
            return self._vdc

        # Get object for an VDC service, make sure exactly one is running
        vdc = self.api.services.find(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        if len(vdc) != 1:
            raise RuntimeError('found %s vdc, requires exactly 1' % len(vdc))
        
        self._vdc = vdc[0]

        return self._vdc

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc
        
        vdc = self.vdc
        instance = vdc.ovc.instance
        self._ovc = j.clients.openvcloud.get(instance=instance)

        return self._ovc      

    @property
    def account(self):
        """
        Return an account
        """
        if self._account is not None:
            return self._account

        # Get object for an OVC service, make sure exactly one is running
        accounts = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=self.data.get('account', None))
        if len(accounts) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(accounts))
        account = accounts[0].name  
        self._account = self.ovc.account_get(account, create=True)

        return self._account

    def create(self):
        data = self.data
        ovc = self.ovc
        account = self.account

        # check existence of the disk. If ID field was updated in the service

        guid = [location['gid'] for location in ovc.locations if location['name']==data['location']]
        if not guid:
            raise RuntimeError('location "%s" not found'%data['location'])

        # if dons'nt exist - create
        data['diskId'] = account.disk_create(
                            name=data['devicename'],
                            gid=guid,
                            description=data['description'],
                            size=data['size'],
                            type=data['type'],
                        )
        self.limit_io()                        
        self.save()        


    def delete(self):
        """
        Delete disk if not boot disk
        """
        data = self.data
        account = self.account

        if data['diskId'] not in [disk['id'] for disk in account.disks]:
            raise RuntimeError("data Disk was not found. cannot continue init of %s" % self.template_name)
        if data['type'] == 'B':
            raise RuntimeError("can't delete boot disk")
        
        account.disk_delete(data['diskId'])

    
    def limit_io(self):
        data = self.data
        account = self.account
        ovc = self.ovc

        if data['diskId'] not in [disk['id'] for disk in account.disks]:
            raise RuntimeError('Data Disk with Id = "%s" was not found' % data['diskId'])

        ovc.api.cloudapi.disks.limitIO(
            diskId=data['diskId'], iops=data['maxIOPS'], total_bytes_sec=data['totalBytesSec'],
            read_bytes_sec=data['readBytesSec'], write_bytes_sec=data['writeBytesSec'], total_iops_sec=data['totalIopsSec'],
            read_iops_sec=data['readIopsSec'], write_iops_sec=data['writeIopsSec'],
            total_bytes_sec_max=data['totalBytesSecMax'], read_bytes_sec_max=data['readBytesSecMax'],
            write_bytes_sec_max=data['writeBytesSecMax'], total_iops_sec_max=data['totalIopsSecMax'],
            read_iops_sec_max=data['readIopsSecMax'], write_iops_sec_max=data['writeIopsSecMax'],
            size_iops_sec=data['sizeIopsSec']
            )