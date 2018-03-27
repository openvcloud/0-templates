# template: vdc

## Description

This actor template creates a VDC (Virtual Data Center) on the specified environment. If required VDC already exists it will be used.

## Schema

- `account`: an [account](../account) used for this space. **required**
- `description`: Description of the cloudspace.
- `create`: defines whether VDC can be created or deleted. Default to `True`.
- `maxMemoryCapacity`: Cloudspace limits, maximum memory(GB).
- `maxCPUCapacity`: Cloudspace limits, maximum CPU capacity.
- `maxVDiskCapacity`: Cloudspace limits, maximum disk capacity(GB).
- `maxNumPublicIP`: Cloudspace limits, maximum allowed number of public IPs.
- `externalNetworkID`: External network to be attached to this cloudspace.
- `maxNetworkPeerTransfer`: Cloudspace limits, max sent/received network transfer peering(GB).
- `users`: List of [vcd users](#vdc-user) authorized on the space. **Filled in automatically, don't specify it in the blueprint**
- `cloudspaceID`: id of the cloudspace. **Filled in automatically, don't specify it in the blueprint**
- `disabled`: True if the cloudspace is disabled. **Filled in automatically, don't specify it in the blueprint**

## Access rights

For information about the different access rights check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Actions

- `install`: create a VDC in given `account` if doesn't exist.
- `uninstall`: delete a VDC.
- `user_add`: authorize a new user on the VDC, or update access rights of the existent user.
- `user_delete`: unauthorize user.
- `enable`: enable VDC.
- `disable`: disable VDC.
- `portforward_create`: create a portforward. Expected to be called from [`node` service](../node).
- `portforward_delete`: delete a portforward. Expected to be called from [`node` service](../node).
- `update`: update limits of the VDC.

```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovc:
        location: <ovc.demo>
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        openvcloud: ovc
        provider: itsyouonline
        email: admin@greenitglobe.com
    - github.com/openvcloud/0-templates/account/0.0.1__myaccount:
       openvcloud: ovc
    - github.com/openvcloud/0-templates/vdc/0.0.1__myspace:
        account: myaccount
actions:
      actions: ['install']
```

```yaml
actions:
  - temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['user_add']
     args:
        user:
          name: username
          accesstype: R
```

```yaml
actions:
  - temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['user_delete']
    args:
      username: testuser
```

```yaml
actions:
  - temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['update']
    args:
      maxMemoryCapacity: 5
      maxCPUCapacity: 1
      maxVDiskCapacity: 20
      maxNumPublicIP: 1
      externalNetworkID: -1
      maxNetworkPeerTransfer: 10
```

```yaml
actions:
  - template: temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['uninstall']
```

```yaml
actions:
  - temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['disable']
```

```yaml
actions:
  - temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['enable']
```

```yaml
actions:
  - temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['portforward_create']
    args:
      machineId: 2342
      port_forwards:
        - destination: <local port>
          source: <public port>
```

```yaml
actions:
  - temlate: github.com/openvcloud/0-templates/vdcuser/0.0.1
    service: myspace
    actions: ['portforward_delete']
    args:
      machineId: 2342
      port_forwards:
        - destination: <local port>
          source: <public port>
```