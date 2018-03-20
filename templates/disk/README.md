# template: disk

## Description: 
This actor template is responsible for creating an account on any openVCloud environment.

## Schema:
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

Disk name will be service name.

## Example for creating disks

``` yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__key:
        path: '/root/.ssh/id_rsa'
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__myovc:
        location: be-gen-demo
        address: 'ovc.demo.greenitglobe.com'
        login: '<username>'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        provider: itsyouonline
        email: admin@greenitglobe.com
    - github.com/openvcloud/0-templates/account/0.0.1__myaccount:
        users:
            - name: admin
              accesstype: CXDRAU
    - github.com/openvcloud/0-templates/vdc/0.0.1__myspace:
        openvcloud: myovc
        users:
            - name: admin
              accesstype: CXDRAU          
    - github.com/openvcloud/0-templates/node/0.0.1__mydisk:
        vdc: myspace

actions:
    - service: mydisk     
      actions: ['create']    
```

## Example for deleting disks
``` yaml
actions:
    - service: mydisk     
      actions: ['delete']  
```