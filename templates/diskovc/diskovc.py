from js9 import j
from zerorobot.template.base import TemplateBase

class Diskovc(TemplateBase):

    version = '0.0.1'
    template_name = "diskovc"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    SSH_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        
        self.data['devicename'] = name
        self._ovc = None
        self._account = None
    
    def validate(self):
        data = self.data

        # Get object for an OVC service, make sure exactly one is running
        ovcs = self.api.services.find(template_uid=self.OVC_TEMPLATE, name=data.get('openvcloud', None))
        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))
        data['openvcloud'] = ovcs[0].name

        # ensure location is given
        if not data['location']:
            raise j.exceptions.Input("location is not given")      

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
    def sshkey(self):
        """ Get a path and keyname of the sshkey service """

        sshkeys = self.api.services.find(template_uid=self.SSH_TEMPLATE)
        if len(sshkeys) != 1:
            raise RuntimeError('found %s ssh services, requires exactly 1' % len(sshkeys))

        # Get key name and path
        path = sshkeys[0].data['path']
        key = path.split('/')[-1]
  
        return key 

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        self._ovc = j.clients.openvcloud.get(self.data['openvcloud'])
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

        guid = [location['gid'] for location in ovc.locations if location['name']==data['location']]
        if not guid:
            raise RuntimeError('location "%s" not found'%data['location'])

        data['diskId'] = account.disk_create(
                            name=data['devicename'],
                            gid=guid,
                            description=data['description'],
                            size=data['size'],
                            type=data['type'],
                        )
        import ipdb; ipdb.set_trace()
        self.save()        


    def delete(self):
        import ipdb; ipdb.set_trace()
        data = self.data
        account = self.account

        if data['diskId'] not in [disk['id'] for disk in account.disks]:
            raise j.exceptions.AYSNotFound(
                "Data Disk was not found. cannot continue init of %s" % self.template_name
                )
        
        account.disk_delete(data['diskId'])

    
    def limit_io(self):
        data = self.data
        account = self.account
        ovc = self.ovc

        if data['diskId'] not in [disk['id'] for disk in account.disks]:
            raise j.exceptions.AYSNotFound(
                "Data Disk was not found. cannot continue init of %s" % self.template_name
                )

        ovc.api.cloudapi.disks.limitIO(
            diskId=data['diskId'], iops=data['maxIOPS'], total_bytes_sec=data['totalBytesSec'],
            read_bytes_sec=data['readBytesSec'], write_bytes_sec=data['writeBytesSec'], total_iops_sec=data['totalIopsSec'],
            read_iops_sec=data['readIopsSec'], write_iops_sec=data['writeIopsSec'],
            total_bytes_sec_max=data['totalBytesSecMax'], read_bytes_sec_max=data['readBytesSecMax'],
            write_bytes_sec_max=data['writeBytesSecMax'], total_iops_sec_max=data['totalIopsSecMax'],
            read_iops_sec_max=data['readIopsSecMax'], write_iops_sec_max=data['writeIopsSecMax'],
            size_iops_sec=data['sizeIopsSec']
            )                

    def err_log_disk_not_found(self):
        """
        Log error in zrobot log if machine is not found
        """
        self.logger.error('disk %s in not found in the openvcloud %s'%(
            self.data['name'],
            self.data['openvcloud'])
            )