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


## Add/remove/update user

Use the accountusers parameter to specify the user access right to the account. Note that if only name exist in the entry (no accesstype) then the access right will be by default `ACDRUX`.

Note that the data in the blueprint is always reflected in the account, which means that removing an entry in the blueprint will remove or change it in the account.

>This is especially relevant to the account template because it is possible to remove the user who created the account (which might be the connection user), so it is very important to reflect that in the blueprint with correct access rights. The original user can be removed if another user with admin access is specified in the blueprint. But the user specified in client should be in this case different than the original user.
This means that unlike node and vdc templates if no users are sepcified, there would be no change to the account access, so for example if it is required to remove all access except the owner, the owner needs to be specified in the users list.

It is possible to add, remove and update user access to the account. To add a user after creating the account, a new [uservdc](../vdcuser) has to be added in the blueprint. Executing the blueprint will trigger the `update_data` and add it to the account. In the same way a user can be removed from the account by deleting the entry from the accountusers in the blueprint. Changing the accesstype of as user will update the user access to the account when executing the blueprint and as above removing it will change the access right to the default value `ACDRUX`.

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

## Example for adding user 'usertest' to account

```yaml
services:
  - github.com/openvcloud/0-templates/vdcuser/0.0.1__testuser:
      provider: itsyouonline
      email: testuser@greenitglobe.com
  - github.com/openvcloud/0-templates/account/0.0.1__myaccount:
      users:
        - name: testuser
          accesstype: R
```