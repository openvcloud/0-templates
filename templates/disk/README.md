# template: disk

## Description

This template is responsible for managing disks on an openVCloud environment.
Disk service can be linked with an existing disk, based on disk ID, or create a new disk.
Disk service is unaware if the disk is attached to a machine.

## Schema

- `vdc`: virtual Data Center id. **required**
- `size`: disk size in GB, default: 1.
- `type`: type of the disk (B=Boot; D=Data), default: `D`.
- `location`: location of the resource on cloud (i.e be-g8-3).
- `deviceName`: name of the disk. **optional**
- `description`: description of the disk. **optional**
- `totalBytesSec`: total throughput limit in bytes per second. This cannot appear with read_bytes_sec or write_bytes_sec. **optional**
- `readBytesSec`: read throughput limit in bytes per second. **optional**
- `writeBytesSec`: write throughput limit in bytes per second. **optional**
- `totalIopsSec`: number of total I/O operations per second. This cannot appear with read_iops_sec or write_iops_sec (same as maxIOPS). **optional**
- `readIopsSec`: number of read I/O operations per second. **optional**
- `writeIopsSec`: number of write I/O operations per second. **optional**
- `totalBytesSecMax`: maximum total throughput limit in bytes per second. **optional**
- `readBytesSecMax`: maximum read throughput limit in bytes per second. **optional**
- `writeBytesSecMax`: maximum write throughput limit in bytes per second. **optional**
- `totalIopsSecMax`: maximum number of total I/O operations per second. This cannot appear with read_iops_sec_max or write_iops_sec_max. **optional**
- `readIopsSecMax`: maximum number of read I/O operations per second. **optional**
- `writeIopsSecMax`: maximum number of write I/O operations per second. **optional**
- `sizeIopsSec`: I/O operations per second. **optional**
- `diskId`: id of the disk. **Filled in automatically, don't specify it in the blueprint**

## Actions

- `install`: installs disk service; if `diskId` is given links the service with earlier created disk, if not given - creates new disk.
- `uninstall`: delete disk.
- `update`: update limits.

## Usage examples via the 0-robot DSL

``` python
from zerorobot.dsl import ZeroRobotAPI
api = ZeroRobotAPI.ZeroRobotAPI()
robot = api.robots['main']

# create services
ovc = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/openvcloud/0.0.1",
    service_name="ovc_service",
    data={'name': 'ovc_instance',
          'location':'be-gen-demo', 
          'address': 'ovc.demo.greenitglobe.com',
          'token': '<iyo jwt token>'}
)
ovc.schedule_action('install')

account = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/account/0.0.1",
    service_name="account-service",
    data={'name': 'account_name','openvcloud':'ovc_service'}
)
account.schedule_action('install')

vdc = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/vdc/0.0.1",
    service_name="vdc-service",
    data={'name': 'vdc_name' ,'account':'account-service'}
)
vdc.schedule_action('install')

disk = = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/disk/0.0.1",
    service_name="vdc-service",
    data={'vdc': 'vdc-service'}
)

disk.schedule_action('install')
disk.schedule_action('update', {'writeBytesSec': 5})
disk.schedule_action('uninstall')
```

## Usage examples via the 0-robot CLI

``` yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__myovc:
        name: be-gen
        location: be-gen-demo
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/account/0.0.1__myaccount:
        name: my_account_name
        openvcloud: myovc
    - github.com/openvcloud/0-templates/vdc/0.0.1__myspace:
        name: my_space_name
        account: myaccount
    - github.com/openvcloud/0-templates/disk/0.0.1__mydisk:
        vdc: myspace

actions:
    - service: mydisk
      actions: ['install']
```

``` yaml
actions:
    - service: mydisk
      actions: ['update']
      args:
        writeBytesSec: 10
```

``` yaml
actions:
    - service: mydisk
      actions: ['uninstall']
```