from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError

class Disk(TemplateBase):

    version = '0.0.1'
    template_name = "disk"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._ovc = None
        self._account = None
        self._config = None
        self._space = None

    def validate(self):
        """
        Validate service data received during creation
        """

        if not self.data['vdc']:
            raise ValueError('vdc service name is required')

        if not self.data['diskId'] and not self.data['name']:
            raise ValueError('provide name to create a new device')         

        # ensure that disk has a valid type
        if self.data['type'].upper() not in ["D", "B"]:
            raise ValueError("disk type must be data D or boot B only")

        self._validate_limits()

    def _validate_limits(self):
        """
        Validate limits on the Disk
        """
        data = self.data
        # ensure that limits are given correctly
        if (data['maxIops'] or data['totalIopsSec']) and (data['readIopsSec'] or data['writeIopsSec']):
            raise RuntimeError("total and read/write of iops_sec cannot be set at the same time")

        if data['totalBytesSec'] and (data['readBytesSec'] or data['writeBytesSec']):
            raise RuntimeError("total and read/write of bytes_sec cannot be set at the same time")

        if data['totalBytesSecMax'] and (data['readBytesSecMax'] or data['writeBytesSecMax']):
            raise RuntimeError("total and read/write of bytes_sec_max cannot be set at the same time")

        if data['totalIopsSecMax'] and (data['readIopsSecMax'] or data['writeIopsSecMax']):
            raise RuntimeError("total and read/write of iops_sec_max cannot be set at the same time")

    def update(self, maxIops=None, totalBytesSec=None, readBytesSec=None,
               writeBytesSec=None, totalIopsSec=None, readIopsSec=None,
               writeIopsSec=None, totalBytesSecMax=None, readBytesSecMax=None,
               writeBytesSecMax=None, totalIopsSecMax=None, readIopsSecMax=None,
               writeIopsSecMax=None, sizeIopsSec=None):
        """ Update limits 
        
        Interpretation of argument values:
        :value 0: unset limit
        :value None: parameter was not provided in the action data and limit will not be updated
        :other values: update of the limit 
        """

        self.state.check('actions', 'install', 'ok')
        updated = []
        updated.append(self._update_value('maxIops', maxIops))
        updated.append(self._update_value('totalBytesSec', totalBytesSec))
        updated.append(self._update_value('readBytesSec', readBytesSec))
        updated.append(self._update_value('writeBytesSec', writeBytesSec))
        updated.append(self._update_value('totalIopsSec', totalIopsSec))
        updated.append(self._update_value('readIopsSec', readIopsSec))
        updated.append(self._update_value('writeIopsSec', writeIopsSec))
        updated.append(self._update_value('totalBytesSecMax', totalBytesSecMax))
        updated.append(self._update_value('readBytesSecMax', readBytesSecMax))
        updated.append(self._update_value('writeBytesSecMax', writeBytesSecMax))
        updated.append(self._update_value('totalIopsSecMax', totalIopsSecMax))
        updated.append(self._update_value('readIopsSecMax', readIopsSecMax))
        updated.append(self._update_value('writeIopsSecMax', writeIopsSecMax))
        updated.append(self._update_value('sizeIopsSec', sizeIopsSec))

        if any(updated):
            # check that new limits are valid
            self._validate_limits()

            # apply new limits
            self._limit_io()

    def _update_value(self, arg, value):
        if value is not None:
            if isinstance(self.data[arg], type(value)):
                if self.data[arg] != value: 
                    self.data[arg] = value
                    return True
            else:
                raise TypeError("limit {lim} has type {type}, expected type {expect_type}".format(
                                lim=arg, type=type(value), expect_type=type(self.data[arg]))
                                )
        return False
      

    def install(self):
        """
        Install disk.
        If disk @id is present in data: check if disk with id exists and apply limits.
        If disk @id is not given: create new disk with given limits.
        """

        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        self.data['location'] = self.space.model['location']
        if self.data['diskId']:
            # if disk is given in data, check if disk exist
            disks = self.account.disks
            disk = [disk for disk in disks if disk['id'] == self.data['diskId']]
            if not disk:
                raise ValueError('Disk with id {} does not exist on account "{}"'.format(
                                  self.data['diskId'], self.account.model['name'])
                                  )
            self.data['name'] = disk[0]['name']

        else:
            self._create()

        self.state.set('actions', 'install', 'ok')

    def _create(self):
        """ Create disk in isolation
        """
        data = self.data
        # check existence of the disk. If ID field was updated in the service
        gid = [location['gid'] for location in self.ovc.locations if location['name'] == data['location']]
        if not gid:
            raise RuntimeError('location "%s" not found' % data['location'])
        
        data['diskId'] = self.account.disk_create(
                            name=data['name'],
                            gid=gid,
                            description=data['description'],
                            size=data['size'],
                            type=data['type'],
                        )
        
    def uninstall(self):
        """
        Uninstall disk. Delete disk if exists.

        :param machine_service: name of the service, 
                                managing VM where the disk attached.
                                Relevant only for attached disks
        """
        disks = [disk['id'] for disk in self.account.disks]   
        if self.data['diskId'] in disks:
            if self.data['type'] == 'B':
                raise RuntimeError("can't delete boot disk")
            self.account.disk_delete(self.data['diskId'], detach=False)
        
        self.state.delete('actions', 'install')
        self.data['diskId'] = 0

    @property
    def config(self):
        """
        Return an object with names of vdc, account, and ovc
        """

        if self._config is not None:
            return self._config

        config = {}

        # get real vdc name
        proxy = self.api.services.get(
            template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        vdc_info = proxy.schedule_action(action='get_info').wait().result
        config['vdc'] = vdc_info['name']

        # get account name
        proxy = self.api.services.get(
            template_uid=self.ACCOUNT_TEMPLATE, name=vdc_info['account'])
        account_info = proxy.schedule_action(action='get_info').wait().result
        config['account'] = account_info['name']

        # get ovc name
        proxy = self.api.services.get(
            template_uid=self.OVC_TEMPLATE, name=account_info['openvcloud'])
        ovc_info = proxy.schedule_action(action='get_info').wait().result
        config['ovc'] = ovc_info['name']

        self._config = config
        return self._config

    @property
    def ovc(self):
        """ An ovc connection instance """
        if not self._ovc:
            self._ovc = j.clients.openvcloud.get(instance=self.config['ovc'])
        return self._ovc

    @property
    def space(self):
        """ Return vdc client """

        if not self._space:
            self._space = self.ovc.space_get(
                accountName=self.config['account'],
                spaceName=self.config['vdc']
            )

        return self._space

    @property
    def account(self):
        if not self._account:
            self._account = self.space.account

        return self._account

    def _limit_io(self):

        data = self.data
        self.ovc.api.cloudapi.disks.limitIO(
            diskId=data['diskId'], iops=data['maxIops'], total_bytes_sec=data['totalBytesSec'],
            read_bytes_sec=data['readBytesSec'], write_bytes_sec=data['writeBytesSec'],
            total_iops_sec=data['totalIopsSec'], read_iops_sec=data['readIopsSec'],
            write_iops_sec=data['writeIopsSec'], total_bytes_sec_max=data['totalBytesSecMax'],
            read_bytes_sec_max=data['readBytesSecMax'], write_bytes_sec_max=data['writeBytesSecMax'],
            total_iops_sec_max=data['totalIopsSecMax'], read_iops_sec_max=data['readIopsSecMax'],
            write_iops_sec_max=data['writeIopsSecMax'], size_iops_sec=data['sizeIopsSec']
        )

    def get_info(self):
        """ Retrun disk info if disk is installed """
        self.state.check('actions', 'install', 'ok')

        return {
            'serviceName' : self.name,
            'deviceName' : self.data['name'],
            'diskId' : self.data['diskId'],
            'diskType' : self.data['type'],
            'vdc' : self.data['vdc'],
        }
