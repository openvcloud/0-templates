# temptate: node

## Description

The template is responsible for managing a virtual machine(VM) on an openVCloud environment.

## Schema

- vdc: denotes name of 'vdc' where the VM belongs;
- uservdc: list of vdc users that have access to the vm.
- sizeId: denotes type of VM, this size impact the number of CPU and memory available for the vm, default: 1.
- osImage: OS image to use for the VM. default:'Ubuntu 16.04'.
- bootdiskSize: boot disk size in GB default: 10.
- dataDiskSize: size of data disk in GB default: 10.
- dataDiskMountpoint: default: `/var`.
- dataDiskFilesystem: type of filesystem
- description: arbitrary description of the VM. **optional**
- ports: list of port forwards of the VM. Ports can be configured during installation of the vm or with actions `['portforward_create']`, `['portforward_delete']`.
- vCpus: number of CPUs in the VM **Filled in automatically, don't specify it in the blueprint**
- memSize: memory size in the VM **Filled in automatically, don't specify it in the blueprint**
- machineId: unique identifier of the VM. **Filled in automatically, don't specify it in the blueprint**
- ipPublic: public IP of the VM. **Filled in automatically, don't specify it in the blueprint**
- ipPrivate: private IP of the VM. **Filled in automatically, don't specify it in the blueprint**
- sshLogin: login for ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**
- sshPassword: password for ssh connection to the VM. **Filled in automatically, don't specify it in the blueprint**
- disks: list of services, managing disks at the VM. **Filled in automatically, don't specify it in the blueprint**
- sshKey: name of ssh-key used to secure ssh connection to the VM.

## Example of creating VM

``` yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__mykey:
        dir: '/root/.ssh/'
        passphrase: <passphrase>
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__myovc:
        location: be-gen-demo
        address: 'ovc.demo.greenitglobe.com'
        login: '<username>'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        openvcloud: myovc
        provider: itsyouonline
        email: admin@greenitglobe.com
    - github.com/openvcloud/0-templates/account/0.0.1__myaccount:
        openvcloud: myovc
        users:
            - name: admin
              accesstype: CXDRAU
    - github.com/openvcloud/0-templates/vdc/0.0.1__myspace:
        openvcloud: myovc
        users:
            - name: admin
              accesstype: CXDRAU
    - github.com/openvcloud/0-templates/node/0.0.1__mynode:
        sshKey: mykey
        vdc: myspace

actions:
    - template: github.com/openvcloud/0-templates/node/0.0.1
      actions: ['install']
```

By analogy the following actions can be applied to manage VM:
`['unnstall']`, `['stop']`, `['start']`, `['pause']`, `['resume']`, `['clone']`, `['snapshot']`.

When `template` is given, the actions will be applied to all services of this type.
In order to apply actions to a specific service, specify a service name.

Following examples show how to schedule actions with arguments.

## Example for cloning machine

``` yaml
- service: mynode
    actions: ['clone']
    args:
        clone_name: <clone name>
```

## Example for adding portforwards

``` yaml
- service: mynode
    actions: ['portforward_create']
    args:
        ports:
        - source: <public port>
          destination: <local port>
```

## Example for deleting portforwards

``` yaml
- service: mynode
    actions: ['portforward_delete']
    args:
        ports:
        - source: <public port>
          destination: <local port>
```

## Example for rolling back snapshot

``` yaml
- service: mynode
    actions: ['snapshot_rollback']
    args:
        snapshot_epoch: <epoch>
```

## Example for deleting snapshot

``` yaml
- service: mynode
    actions: ['snapshot_rollback']
    args:
        snapshot_epoch: <epoch>
```