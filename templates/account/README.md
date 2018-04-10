# template: account

## Description

This template is responsible for creating an account on a openVCloud environment.

## Schema

- `name`: Name of the account on OVC **required**
- `openvcloud`: Name of the [openvcloud](../openvcloud) instance used to connect to the environment.  **Required**.
- `description`: Arbitrary description of the account. **Optional**.
- `maxMemoryCapacity`: The limit on the memory capacity that can be used by the account. Default to -1 (unlimited).
- `maxCPUCapacity`: The limit on the CPUs that can be used by the account. Default: -1 (unlimited).
- `maxNumPublicIP`: The limit on the number of public IPs that can be used by the account. Default to -1 (unlimited).
- `maxVDiskCapacity`: The limit on the disk capacity that can be used by the account. Default to -1 (unlimited).
- `consumptionFrom`: determines the start date of the required period to fetch the account consumption info from. If left empty will be creation time of the account.
- `consumptionTo`: determines the end date of the required period to fetch the account consumption info from. If left empty will be `consumptionfrom` + 1 hour.
- `consumptionData`: consumption data will be saved here as series of bytes which represents a zip file.
- `create`: defines whether account can be created or deleted. Default to `True`.
- `users`: List of [vcd users](#vdc-user)  authorized on the account. **Filled in automatically, don't specify it in the blueprint**.
- `accountID`: The ID of the account. **Filled in automatically, don't specify it in the blueprint**.

### Vdc User

- `name`: name of the [vdcuser](../vdcuser)
- `accesstype`: access type (check OVC documentation for supported access types)

### Access rights

For information about the different access rights, check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Actions

- `install`: creates an account or gets an existent account.
- `uninstall`: delete an account. All VDCs (Virtual Data Centers) related to this account will be destroyed and uninstall should not be called on those VDC services when uninstalling an account.
- `user_add`: adds a user to the account or updates access rights. In order to add a user, corresponding [`vdcuser`](#vdc-user) service should be installed.
- `user_delete`: deletes a user from the account.
- `update`: updates the account attributes:

  - `maxMemoryCapacity`
  - `maxCPUCapacity`
  - `maxNumPublicIP`
  - `maxVDiskCapacity`

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
    data={'name': 'test_account','openvcloud':'ovc_service'}
)
account.schedule_action('install')
account.schedue_action('update', {'maxMemoryCapacity': 5})

# examples to manage users
# first create a service for vdcuser admin
vdcuser = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/vdcuser/0.0.1",
    service_name="admin",
    data={'name': 'username', 'openvcloud':'ovc_service', 'email': 'email@mail.be'}
)
vdcuser.schedule_action('install')

# authorize user
account.schedule_action('user_authorize', {'vdcuser': 'admin', 'accesstype': 'R'})
# update user access of the existing user
account.schedule_action('user_authorize', {'vdcuser': 'admin', 'accesstype': 'W'})
# unauthorize user
account.schedule_action('user_unauthorize', {'vdcuser': 'admin', 'accesstype': 'W'})

account.schedule_action('uninstall')
```

## Usage examples via the 0-robot CLI

```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovc:
        name: be-gen-demo
        location: <ovc.demo>
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/account/0.0.1__account-service:
        name: test_account
        openvcloud: ovc
actions:
      actions: ['install']
```

```yaml
actions:
    - template: github.com/openvcloud/0-templates/account/0.0.1:
      service: account-service
      action: ['uninstall']
```

```yaml
services:
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        name: ovc-user
        openvcloud: ovc
        provider: itsyouonline
        email: admin@greenitglobe.com
actions:
    - service: account-service
      actions: ['user_add']
      args:
          user:
            vdcuser: admin
            accesstype: R
```

```yaml
actions:
    - service: account-service
      actions: ['user_delete']
      args:
        vdcuser: admin
```

```yaml
actions:
    - service: account-service
      actions: ['update']
      args:
        maxMemoryCapacity: 5
```
