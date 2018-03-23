# template: account

## Description

This template is responsible for creating an account on any openVCloud environment.

## Schema

- `openvcloud`: Name of the [openvcloud](../openvcloud) instance used to connect to the environment.  **required**
- `description`: Arbitrary description of the account. **optional**
- `maxMemoryCapacity`: The limit on the memory capacity that can be used by the account. Default to -1 (unlimited)
- `maxCPUCapacity`: The limit on the CPUs that can be used by the account. Default: -1 (unlimited)
- `maxNumPublicIP`: The limit on the number of public IPs that can be used by the account. Default to -1 (unlimited)
- `maxDiskCapacity`: The limit on the disk capacity that can be used by the account. Default to -1 (unlimited)
- `consumptionFrom`: determines the start date of the required period to fetch the account consumption info from. If left empty will be creation time of the account.
- `consumptionTo`: determines the end date of the required period to fetch the account consumption info from. If left empty will be `consumptionfrom` + 1 hour.
- `consumptionData`: consumption data will be saved here as series of bytes which represents a zip file. Example of writing the data:
- `create`: defines whether account can be created or deleted. Default to `True`.
- `users`: List of [vcd users](#vdc-user)  authorized on the account. **Filled in automatically, don't specify it in the blueprint**
- `accountID`: The ID of the account. **Filled in automatically, don't specify it in the blueprint**

### Vdc User

- `name`: name of the [vdcuser](../vdcuser)
- `accesstype`: access type (check OVC documentation for supported access types)

### Access rights

For information about the different access rights, check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Actions

- `install`: creates an account or gets an existent account.
- `uninstall`: delete an account. All VDCs (Virtual Data Centers) related to this account will be destroyed and uninstall should not be called on those VDC services when uninstalling an account.
- `user_add`: adds a user to the account or updates access rights.
- `user_delete`: deletes a user from the account.
- `update`: updates the account attributes:

  - `maxMemoryCapacity`
  - `maxCPUCapacity`
  - `maxNumPublicIP`
  - `maxDiskCapacity`

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
actions:
      actions: ['install']
```

```yaml
actions:
  - template: github.com/openvcloud/0-templates/account/0.0.1:
    service: myaccount
    action: ['uninstall']
```

```yaml
actions:
  - service: myaccount
    actions: ['user_add']
     args:
        user:
          name: thabet
          accesstype: R
```

```yaml
actions:
  - service: myaccount
    actions: ['user_delete']
    args:
      username: testuser
```

```yaml
actions:
  - service: myaccount
    actions: ['update']
    args:
      maxMemoryCapacity: 5
```
