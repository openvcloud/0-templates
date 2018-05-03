# template: github.com/openvcloud/0-templates/disk/0.0.1

## Description

This template is responsible for managing disks on an openVCloud environment.
Disk service can be linked with an existing disk, based on disk ID, or create a new disk.

## Schema

- `name`: name of the disk. When creating a new device, `name` is **Required.**
- `vdc`: Virtual Data Center(VDC) service name. **Required.**
- `diskId`: id of the disk. If provided during service creation, the service will link to the disk with this `diskId`. If disk with given id does not exist on the location, `zrobot` will log a corresponding error. When linking to an earlier created disk, `diskId` is  **Required.**
 If `diskId` is not given, new disk will be created.
- `size`: disk size in GB, default: 1.
- `type`: type of the disk (B=Boot; D=Data), default: `D`.
- `location`: location of the resource on cloud (i.e be-g8-3). Fetched from VDC object and **Filled automatically**.
- `description`: description of the disk. **Optional.**
- `totalBytesSec`: total throughput limit in bytes per second. This cannot appear with read_bytes_sec or write_bytes_sec. **Optional.**
- `readBytesSec`: read throughput limit in bytes per second. **Optional.**
- `writeBytesSec`: write throughput limit in bytes per second. **Optional.**
- `totalIopsSec`: number of total I/O operations per second. This cannot appear with read_iops_sec or write_iops_sec (same as maxIOPS). **Optional.**
- `readIopsSec`: number of read I/O operations per second. **Optional.**
- `writeIopsSec`: number of write I/O operations per second. **Optional.**
- `totalBytesSecMax`: maximum total throughput limit in bytes per second. **Optional.**
- `readBytesSecMax`: maximum read throughput limit in bytes per second. **Optional.**
- `writeBytesSecMax`: maximum write throughput limit in bytes per second. **Optional.**
- `totalIopsSecMax`: maximum number of total I/O operations per second. This cannot appear with read_iops_sec_max or write_iops_sec_max. **Optional.**
- `readIopsSecMax`: maximum number of read I/O operations per second. **Optional.**
- `writeIopsSecMax`: maximum number of write I/O operations per second. **Optional.**
- `sizeIopsSec`: I/O operations per second. **Optional.**

## Actions

- `install`: installs disk service; if `diskId` is given links the service with earlier created disk, if not given - creates new disk.
- `uninstall`: delete disk.
- `update`: update limits. Note that updating limits is allowed only for attached disks. Trying to update limits of detached disk will produce an error.

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
    data={'name': 'account_name',
          'openvcloud':'ovc_service'}
)
account.schedule_action('install')

vdc = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/vdc/0.0.1",
    service_name="vdc-service",
    data={'name': 'vdc_name' ,'account':'account-service'}
)
vdc.schedule_action('install')

disk = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/disk/0.0.1",
    service_name="vdc-service",
    data={'name': 'test_disk',
          'vdc': 'vdc-service'}
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
        name: test_disk
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