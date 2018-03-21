# temptate: node

## Description

The template is responsible for managing a virtual machine(VM) on an openVCloud environment.

## Schema

- `vdc`: denotes name of 'vdc' where the VM belongs. **required**
- `sshKey`: name of ssh-key used to secure ssh connection to the VM. **required**
- `sizeId`: denotes type of VM, this size impact the number of CPU and memory available for the vm, default: 1.
- `osImage`: OS image to use for the VM. default:'Ubuntu 16.04'.
- `bootdiskSize`: boot disk size in GB default: 10.
- `dataDiskSize`: size of data disk in GB default: 10.
- `FilesystemType`: file system of the data disk, suports: xfs,	ext2, ext3, ext4. **optional**
- `dataDiskMountpoint`: default: `/var`.
- `dataDiskFilesystem`: type of filesystem
- `description`: arbitrary description of the VM. **optional**
- `ports`: list of port forwards of the VM. Ports can be configured with actions `['portforward_create']`, `['portforward_delete']`.
- `vCpus`: number of CPUs in the VM **Filled in automatically, don't specify it in the blueprint**
- `memSize`: memory size in the VM **Filled in automatically, don't specify it in the blueprint**
- `machineId`: unique identifier of the VM. **Filled in automatically, don't specify it in the blueprint**
- `ipPublic`: public IP of the VM. **Filled in automatically, don't specify it in the blueprint**
- `ipPrivate`: private IP of the VM. **Filled in automatically, don't specify it in the blueprint**
- `sshLogin`: login for ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**
- `sshPassword`: password for ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**
- `disks`: list of services, managing disks at the VM. **Filled in automatically, don't specify it in the blueprint**

## Actions

- `install`: install a VM.
- `uninstall`: delete the VM.
- `stop`: stop the VM.
- `start`: start the VM.
- `restart`: restart the VM.
- `pause`: pause the VM.
- `resume`: resume the VM.
- `clone`: clone the VM.
- `snapshot`: create a snapshot of the VM.
- `snapshot_delete`: delete a snapshot of the VM.
- `list_snapshots`: return a list of snapshots of the VM.
- `portforward_create`: create a portforward on the VM.
- `portforward_delete`: delete a portforward on the VM.

``` yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__mykey:
        dir: '/root/.ssh/'
        passphrase: <passphrase>
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__myovc:
        location: be-gen-demo
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        openvcloud: myovc
        provider: itsyouonline
        email: admin@greenitglobe.com
    - github.com/openvcloud/0-templates/account/0.0.1__myaccount:
        openvcloud: myovc
    - github.com/openvcloud/0-templates/vdc/0.0.1__myspace:
        openvcloud: myovc
    - github.com/openvcloud/0-templates/node/0.0.1__mynode:
        sshKey: mykey
        vdc: myspace
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
- template: github.com/openvcloud/0-templates/node/0.0.1
  service: mynode
  actions: ['portforward_create']
  args:
    ports:
        - source: <public port>
          destination: <local port>
```

``` yaml
actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      service: mynode
      actions: ['portforward_delete']
      args:
        ports:
            - source: <public port>
              destination: <local port>
```
