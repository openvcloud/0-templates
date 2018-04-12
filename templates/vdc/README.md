# template: vdc

## Description

This template manages VDC (Virtual Data Center) on the specified environment. If VDC with given name doesn't exist, it will be created. Service of type `vdc` depends on the services of types [`ovc`](../openvcloud) and [`account`](../account).

## Schema

- `name`: name of the VDC, unique on the given account. **Required**.
- `account`: an [account](../account) used for this space. **Required**.
- `description`: Description of the cloudspace. **Optional**.
- `create`: defines whether VDC can be created or deleted. Default to `True`.
- `maxMemoryCapacity`: Cloudspace limits, maximum memory(GB). **Optional**.
- `maxCPUCapacity`: Cloudspace limits, maximum CPU capacity. **Optional**.
- `maxVDiskCapacity`: Cloudspace limits, maximum disk capacity(GB). **Optional**.
- `maxNumPublicIP`: Cloudspace limits, maximum allowed number of public IPs. **Optional**.
- `externalNetworkID`: External network to be attached to this cloudspace. **Optional**.
- `maxNetworkPeerTransfer`: Cloudspace limits, max sent/received network transfer peering(GB). **Optional**.
- `users`: List of [vcd users](#vdc-user) authorized on the space. **Filled in automatically, don't specify it in the blueprint**.
- `cloudspaceID`: id of the cloudspace. **Filled in automatically, don't specify it in the blueprint**.
- `disabled`: True if the cloudspace is disabled. **Filled in automatically, don't specify it in the blueprint**.

## Access rights

For information about the different access rights check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Actions

- `install`: create a VDC in given `account` if doesn't exist.
- `uninstall`: delete a VDC.
- `enable`: enable VDC.
- `disable`: disable VDC.
- `portforward_create`: create a port forward.
- `portforward_delete`: delete a port forward.
- `update`: update limits of the VDC.
- `user_authorize`: authorize a new user on the VDC, or update access rights of the existent user.
- `user_unauthorize`: unauthorize user.

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
vdc.schedule_action('enable')
vdc.schedule_action('disable')
vdc.schedule_action('update', {'maxMemoryCapacity': 5,
                               'maxCPUCapacity': 1,
                               'maxVDiskCapacity': 20,
                               'maxNumPublicIP': 1,
                               'externalNetworkID': -1,
                               'maxNetworkPeerTransfer': 10})

# examples to manage users
# first create a service for vdcuser admin
  vdcuser = robot.services.create(
      template_uid="github.com/openvcloud/0-templates/vdcuser/0.0.1",
      service_name="admin",
      data={'name': 'username', 'openvcloud':'ovc_service', 'email': 'email@mail.be'}
  )
  vdcuser.schedule_action('install')

# authorize user
vdc.schedule_action('user_authorize', {'vdcuser': 'admin', 'accesstype': 'R'})
# update user access of the existing user
vdc.schedule_action('user_authorize', {'vdcuser': 'admin', 'accesstype': 'W'})
# unauthorize user
vdc.schedule_action('user_unauthorize', {'vdcuser': 'admin', 'accesstype': 'W'})

vdc.schedule_action('uninstall')

# example creating/deleting port forwards
# managing port forwards is always linked to a specific VM, therefore vm service should be running
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

vdc.schedule_action('portforward_create', {'node_service': 'mynode', 'ports':[{'source':22, 'destination':22}]})
vdc.schedule_action('portforward_delete', {'node_service': 'mynode', 'ports':[{'source':22, 'destination':22}]})

```

## Usage examples via the 0-robot CLI

```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovc:
        name: be-gen-demo
        location: <ovc.demo>
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/account/0.0.1__account:
       name: ovc_account_name
       openvcloud: ovc
    - github.com/openvcloud/0-templates/vdc/0.0.1__space:
        name: ovc_space_name
        account: account
actions:
      - actions: ['install']
```

```yaml
actions:
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
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
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
      actions: ['uninstall']
```

```yaml
actions:
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
      actions: ['disable']
```

```yaml
actions:
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
      actions: ['enable']
```

```yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__key-service:
        name: id_rsa
        dir: '/root/.ssh/'
        passphrase: <passphrase>
    - github.com/openvcloud/0-templates/node/0.0.1__mynode:
        name: vm_name
        sshKey: key-service
        vdc: vdc-service
actions:
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
      actions: ['portforward_create']
      args:
        node_service: mynode
        ports:
          - destination: <local port>
            source: <public port>
```

```yaml
actions:
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
      actions: ['portforward_delete']
      args:
        node_service: mynode
        ports:
          - destination: <local port>
            source: <public port>
```

Authorizing/unauthorizing/updating rights is only supported for users managed by services of type `vdcuser`.
It means that for each user we define a service as follows:

```yaml
services:
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        name: user-name
        openvcloud: ovc
        provider: itsyouonline
        email: admin@greenitglobe.com
actions:
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
      actions: ['user_authorize']
      args:
          vdcuser: admin
          accesstype: R
```

```yaml
actions:
    - template: github.com/openvcloud/0-templates/vdcuser/0.0.1
      service: space
      actions: ['user_unauthorize']
      args:
        username: admin
```