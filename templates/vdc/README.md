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

## User access rights

Use the uservdc parameter to specify the user access right to the vdc. Note that if only name exist in the entry (no accesstype) then the access right will be by default `ACDRUX`.

Note that the data in the blueprint is always reflected in the vdc, which means that removing an entry in the blueprint will remove or change it in the vdc.

Using process change it is possible to add, remove and update user access to the cloudspace. To add user after executing the run and creating the vdc, add a new user in the blueprint and execute the blueprint to trigger process change and add new user to the cloudspace or removing user by deleting the entry in the blueprint. Changing the accesstype will update the user access when executing the blueprint and as above removing it will change the access right to the default value `ACDRUX`.

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

## Example for Deleting VDC

```yaml
actions:
  - service: myspace
    actions: ['uninstall']
```

## Example for disabling VDC

```yaml
actions:
  - service: myspace
    actions: ['disable']
```

## Example for enabling VDC
```yaml
actions:
  - service: myspace
    actions: ['enable']
```
