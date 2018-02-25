# template: account

## Description:
This template is responsible for creating an account on any openVCloud environment.

## Schema:

- description: (optional) Arbitrary description of the account.
- openvcloud: Name of the [openvcloud](../openvcloud) instance used to connect to the environment. If not provided and there is exactly one openvcloud instance configured, this instance will be used (and remembered), otherwise it's an error.
- users: List of [vcd users](#vdc-user) that will be authorized on the account.
- accountID: The ID of the account. **Filled in automatically, don't specify it in the blueprint**
- maxMemoryCapacity: The limit on the memory capacity that can be used by the account. Default: -1 (unlimited)
- maxCPUCapacity: The limit on the CPUs that can be used by the account. Default: -1 (unlimited)
- maxNumPublicIP: The limit on the number of public IPs that can be used by the account. Default: -1 (unlimited)
- maxDiskCapacity: The limit on the disk capacity that can be used by the account. Default: -1 (unlimited)
- consumptionFrom: determines the start date of the required period to fetch the account consumption info from. If left empty will be creation time of the account.
- consumptionTo: determines the end date of the required period to fetch the account consumption info from. If left empty will be consumptionfrom + 1 hour.
- consumptionData: consumption data will be saved here as series of bytes which represents a zip file. Example of writing the data:

## Vdc User
- name: name of the [vdcuser](../vdcuser)
- accesstype: access type (check OVC documentation for supported access types)

## Access rights

For information about the different access rights check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Example for creating an account

```yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__key:
        path: '/root/.ssh/id_rsa'
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovc:
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

actions:
      actions: ['install']
```

## Actions
### `add_user` action
Add user to an account

params:
- user object
  - name: username reference to user instance
  - accesstype: (optional) access type

```yaml
# Create the user instance if it doesn't already exist
services:
  - github.com/openvcloud/0-templates/vdcuser/0.0.1__testuser:
      provider: itsyouonline
      email: testuser@greenitglobe.com
actions:
  - service: testuser
    action: ['install']

  - service: myaccount
    actions: ['add_user']
     args:
        user:
          name: thabet
          accesstype: R
```

### `delete_user` action
Remove users from an account

params:
- username: user name to delete
```yaml
actions:
  - service: myaccount
    actions: ['delete_user']
    args:
      username: testuser
```


### `update` action
Update account attributes

params:
- maxMemoryCapacity (optional): The limit on the memory capacity that can be used by the account.
- maxCPUCapacity (optional): The limit on the CPUs that can be used by the account.
- maxNumPublicIP (optional): The limit on the number of public IPs that can be used by the account.
- maxDiskCapacity (optional): The limit on the disk capacity that can be used by the account.

```yaml
actions:
  - service: myaccount
    actions: ['update']
    args:
      maxMemoryCapacity: 5
```