# template: vdc

## Description

This actor template creates a cloudspace (Virtual Data Center) on the specified environment. If required cloudspace already exists it will be used.

## Schema

- description: Description of the cloudspace.
- account: an [account](../account) used for this space, if not specified and there is exactly one account instance configured, this instance will be used (and remembered), otherwise it's an error.
- location: Environment to deploy this cloudspace.
- users: List of [vcd users](#vdc-user) that will be authorized on the space.
- cloudspaceID: id of the cloudspace. **Filled in automatically, don't specify it in the blueprint**
- maxMemoryCapacity: Cloudspace limits, maximum memory(GB).
- maxCPUCapacity: Cloudspace limits, maximum CPU capacity.
- maxDiskCapacity: Cloudspace limits, maximum disk capacity(GB).
- maxNumPublicIP: Cloudspace limits, maximum allowed number of public IPs.
- externalNetworkID: External network to be attached to this cloudspace.
- maxNetworkPeerTransfer: Cloudspace limits, max sent/received network transfer peering(GB).
- disabled: True if the cloudspace is disabled. **Filled in automatically, don't specify it in the blueprint**

## Access rights

For information about the different access rights check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Example for creating VDC

VDC requires an [account](../account).

For the creation of the vdc the action specified is install, to delete the vdc action uninstall needs to be specified in the `actions` parameter as seen in the second example below.

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
    - github.com/openvcloud/0-templates/vdc/0.0.1__myspace:
        location: be-gen-1
        users:
            - name: admin
              accesstype: CXDRAU

actions:
    - actions: ['install']
```
## Actions
### `user_add` action
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

  - service: myspace
    actions: ['user_add']
     args:
        user:
          name: thabet
          accesstype: R
```

## Actions
### `user_delete` action
Remove users from an account

params:
- username: user name to delete
```yaml
actions:
  - service: myspace
    actions: ['user_delete']
    args:
      username: testuser
```


### `update` action
Update account attributes

params:
- maxMemoryCapacity: Cloudspace limits, maximum memory(GB).
- maxCPUCapacity: Cloudspace limits, maximum CPU capacity.
- maxDiskCapacity: Cloudspace limits, maximum disk capacity(GB).
- maxNumPublicIP: Cloudspace limits, maximum allowed number of public IPs.
- externalNetworkID: External network to be attached to this cloudspace.
- maxNetworkPeerTransfer: Cloudspace limits, max sent/received network transfer peering(GB).

```yaml
actions:
  - service: myspace
    actions: ['update']
    args:
      maxMemoryCapacity: 5
```

### Example for Deleting VDC

```yaml
actions:
  - service: myspace
    actions: ['uninstall']
```

### Example for disabling VDC

```yaml
actions:
  - service: myspace
    actions: ['disable']
```

### Example for enabling VDC
```yaml
actions:
  - service: myspace
    actions: ['enable']
```
