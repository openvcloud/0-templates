# template: node

## Description

The template is responsible for managing a virtual machine (VM) on the OpenvCloud environment.

## Schema

- `name`: name of the VM, unique in given vdc. **Required**.
- `vdc`: name of Virtual Data Center (VDC) where the VM belongs. **Required**.
- `sshKey`: name of ssh-key service that manages ssh-key used to secure ssh connection to the VM. **Required**.
- `sizeId`: denotes type of VM, this size impact the number of CPU and memory available for the vm. Default to 1.
- `osImage`: OS image to use for the VM. Default to 'Ubuntu 16.04'.
- `bootdiskSize`: boot disk size in GB. Default to 10.
- `dataDiskSize`: size of data disk in GB. Default to 10.
- `dataDiskMountpoint`: data disk mount point. Default to `/var`.
- `dataDiskFilesystem`: file system of the data disk, supports: `xfs`, `ext2`, `ext3`, `ext4`. **Optional**.
- `description`: arbitrary description of the VM. **Optional**.
- `vCpus`: number of CPUs in the VM. **Filled in automatically, don't specify it in the blueprint**.
- `memSize`: memory size in the VM **Filled in automatically, don't specify it in the blueprint**.
- `machineId`: unique identifier of the VM. **Filled in automatically, don't specify it in the blueprint**.
- `ipPublic`: public IP of the VM. **Filled in automatically, don't specify it in the blueprint**.
- `ipPrivate`: private IP of the VM. **Filled in automatically, don't specify it in the blueprint**.
- `sshLogin`: login for ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**.
- `sshPassword`: password for ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**.
- `disks`: list of services, managing disks at the VM. **Filled in automatically, don't specify it in the blueprint**.

## Actions

- `install`: install VM. If state of action `install` is not `ok`, a new VM will be created. If machine with the same name already exists, if will be deleted and installed again.
- `uninstall`: delete VM.
- `stop`: stop VM.
- `start`: start VM.
- `restart`: restart VM.
- `pause`: pause VM.
- `resume`: resume VM.
- `clone`: clone VM.
- `snapshot`: create a snapshot of the VM.
- `snapshot_delete`: delete a snapshot of the VM.
- `list_snapshots`: return a list of snapshots of the VM.
- `disk_add`: create a new disk on the VM.
- `disk_attach`: attach disk to the VM.
- `disk_detach`: detach disk from the VM.
- `disk_delete`: delete disk, attached to the VM.

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

sshkey = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/sshkey/0.0.1",
    service_name="key-service",
    data={'name': 'id_rsa', 'dir':'/root/.ssh/', 'passphrase': 'testpassphrase'}
)
sshkey.schedule_action('install')

node = robot.services.create(template_uid="github.com/openvcloud/0-templates/node/0.0.1",
    service_name="mynode",
    data={'sshKey':'key-service', 'vdc':'vdc-service'}
)
node.schedule_action('install')

# run actions
node.schedule_action('install')
node.schedule_action('stop')
node.schedule_action('start')
node.schedule_action('pause')
node.schedule_action('resume')
node.schedule_action('restart')
node.schedule_action('clone')
node.schedule_action('snapshot')
node.schedule_action('snapshot_delete', {'snapshot_epoch': 1522839792})
node.schedule_action('disk_add', {'name': 'testDisk', 'size': 10})
node.schedule_action('disk_attach', {'disk_service_name': 'Disk0000'})
node.schedule_action('disk_detach', {'disk_service_name': 'Disk0000'})
node.schedule_action('disk_delete', {'disk_service_name': 'Disk0000'})

# get result of an action
task = node.schedule_action('list_snapshots')
task.wait()
snapshots = taks.result

node.schedule_action('uninstall')

```

## Usage examples via the 0-robot CLI

``` yaml

services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovc-service:
        name: ovc_instance_name
        location: be-gen-demo
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/account/0.0.1__account-service:
        name: account_name
        openvcloud: ovc-service
    - github.com/openvcloud/0-templates/vdc/0.0.1__vdc-service:
        account: account-service
    - github.com/openvcloud/0-templates/sshkey/0.0.1__key-service:
        name: id_rsa
        dir: '/root/.ssh/'
        passphrase: <passphrase>
    - github.com/openvcloud/0-templates/node/0.0.1__node-service:
        name: vm_name
        sshKey: key-service
        vdc: vdc-service
actions:
    - actions: ['install']
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['start']
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['stop']
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['pause']
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['resume']
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['restart']
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['clone']
      args:
        clone_name: <clone name>
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['snapshot']
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['snapshot_delete']
      args:
        snapshot_epoch: <epoch>
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['snapshot_rollback']
      args:
        snapshot_epoch: <epoch>
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['disk_add']
      args:
        name: testDisk
        size: 10
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['disk_attach']
      args:
        disk_service_name: Disk0000
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['disk_detach']
      args:
        disk_service_name: Disk0000
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['disk_delete']
      args:
        disk_service_name: Disk0000
```