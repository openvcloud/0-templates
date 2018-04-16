from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError

class Disk(TemplateBase):

    version = '0.0.1'
    template_name = "disk"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._account = None
        self._config = None
        self._space = None

    def validate(self):
        """
        Validate service data received during creation
        """

        if not self.data['vdc']:
            raise RuntimeError('vdc service name is required')

        if not self.data['diskId'] and not self.data['name']:
            raise RuntimeError('to create a new disk name is required')         

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
            if not self._attached:
                raise RuntimeError('limiting IO is not supported for detached disks')  
            self._validate_limits()

            # apply new limits
            self._limit_io()

    def _attached(self):
        """ Check if disk id attached """
        disks = self.account.disks
        machine_id = [disk['machineID'] for disk in disks if disk['id'] == self.data['diskId']]
        if machine_id:
            return True

        return False      

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
            if self.data['diskId'] not in [disk['id'] for disk in disks]:
                raise ValueError('Disk with id {} does not exist on account "{}"'.format(
                                  self.data['diskId'], self.account.model['name'])
                                  )
            if self._attached:
                # limiting IO is possible only for attached disks
                self._limit_io()
        else:
            self._create()

        self.state.set('actions', 'install', 'ok')

    def _create(self):
        """ Create disk  """
        data = self.data
        # check existence of the disk. If ID field was updated in the service
        gid = [location['gid'] for location in self.ovc.locations if location['name'] == data['location']]
        if not gid:
            raise RuntimeError('location "%s" not found' % data['location'])
        
        # if doesn't exist - create
        data['diskId'] = self.account.disk_create(
                            name=data['name'],
                            gid=gid,
                            description=data['description'],
                            size=data['size'],
                            type=data['type'],
                        )
        self._limit_io()
        
    def uninstall(self):
        """
        Uninstall disk. Delete disk if exists.
        """

        if self.data['type'] == 'B':
            raise RuntimeError("can't delete boot disk")

        disks = [disk['id'] for disk in self.account.disks]

        if self.data['diskId'] in disks:
            self.account.disk_delete(self.data['diskId'])

        self.state.delete('actions', 'install')


    @property
    def config(self):
        """
        Return an object with names of vdc, account, and ovc
        """

        if self._config is not None:
            return self._config

        config = {}
        # traverse the tree up words so we have all info we need to return, connection and
        # account

        vdc_proxy = self._get_proxy(self.VDC_TEMPLATE, self.data['vdc'])
        task = vdc_proxy.schedule_action('get_name')
        task.wait()
        config['vdc'] = task.result

        task = vdc_proxy.schedule_action('get_account')
        task.wait()
        account_service_name = task.result

        account_proxy = self._get_proxy(self.ACCOUNT_TEMPLATE, account_service_name)
        task = account_proxy.schedule_action('get_name')
        task.wait()
        config['account'] = task.result

        # get connection
        task = account_proxy.schedule_action('get_openvcloud')
        task.wait()
        config['ovc'] = task.result

        self._config = config
        return self._config

    def _get_proxy(self, template_uid, service_name):
        """
        Get proxy object of the service with name @service_name
        """

        matches = self.api.services.find(template_uid=template_uid, name=service_name)
        if len(matches) != 1:
            raise RuntimeError('found %d services with name "%s", required exactly one' % (len(matches), service_name))
        return matches[0]

    @property
    def ovc(self):
        """ An ovc connection instance """
        
        return j.clients.openvcloud.get(instance=self.config['ovc'])

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

    def get_id(self):
        """ Return id of the disk """

        self.state.check('actions', 'install', 'ok')
        return self.data['diskId']

    def get_type(self):
        """ Return type of the disk """
        
        self.state.check('actions', 'install', 'ok')
        return self.data['type']        