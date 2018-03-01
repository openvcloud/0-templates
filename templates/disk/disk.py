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
        if not self.data['vdc']:
            raise RuntimeError('vdc name should be given')
        self._validate_limits()

    def update_data(self, data):
        # merge new data
        self.data.update(data)

        # check that new limits are valid
        self._validate_limits()

        # apply new limits
        self._limit_io()

        self.save()

    def _validate_limits(self):
        """
        Validate limits on the Disk
        """
        data = self.data
        # ensure that disk has a valid type
        if data['type'] and data['type'].upper() not in ["D", "B"]:
            raise RuntimeError("diskovc's type must be data (D) or boot (B) only")

        # ensure that limits are given correctly
        if (data['maxIops'] or data['totalIopsSec']) and (data['readIopsSec'] or data['writeIopsSec']):
            raise RuntimeError("total and read/write of iops_sec cannot be set at the same time")

        if data['totalBytesSec'] and (data['readBytesSec'] or data['writeBytesSec']):
            raise RuntimeError("total and read/write of bytes_sec cannot be set at the same time")

        if data['totalBytesSecMax'] and (data['readBytesSecMax'] or data['writeBytesSecMax']):
            raise RuntimeError("total and read/write of bytes_sec_max cannot be set at the same time")

        if data['totalIopsSecMax'] and (data['readIopsSecMax'] or data['writeIopsSecMax']):
            raise RuntimeError("total and read/write of iops_sec_max cannot be set at the same time")

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
        guid = [location['gid'] for location in ovc.locations if location['name'] == data['location']]
        if not guid:
            raise RuntimeError('location "%s" not found' % data['location'])

        # if doesn't exist - create
        data['diskId'] = account.disk_create(
                            name=data['devicename'],
                            gid=guid,
                            description=data['description'],
                            size=data['size'],
                            type=data['type'],
                        )
        self._limit_io()
        self.save()

    def delete(self):
        """
        Delete disk if not boot disk
        """
        data = self.data
        account = self.account

        if data['type'] == 'B':
            raise RuntimeError("can't delete boot disk")
        if data['diskId'] in [disk['id'] for disk in account.disks]:
            account.disk_delete(data['diskId'])

    def _limit_io(self):
        data = self.data
        if data['diskId'] not in [disk['id'] for disk in self.account.disks]:
            raise RuntimeError('Data Disk with Id = "%s" was not found' % data['diskId'])

        self.ovc.api.cloudapi.disks.limitIO(
            diskId=data['diskId'], iops=data['maxIops'], total_bytes_sec=data['totalBytesSec'],
            read_bytes_sec=data['readBytesSec'], write_bytes_sec=data['writeBytesSec'],
            total_iops_sec=data['totalIopsSec'], read_iops_sec=data['readIopsSec'],
            write_iops_sec=data['writeIopsSec'], total_bytes_sec_max=data['totalBytesSecMax'],
            read_bytes_sec_max=data['readBytesSecMax'], write_bytes_sec_max=data['writeBytesSecMax'],
            total_iops_sec_max=data['totalIopsSecMax'], read_iops_sec_max=data['readIopsSecMax'],
            write_iops_sec_max=data['writeIopsSecMax'], size_iops_sec=data['sizeIopsSec']
        )
