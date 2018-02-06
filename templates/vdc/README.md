# template: vdc

## Description

This actor template creates a cloudspace (Virtual Data Center) on the specified environment. If required cloudspace already exists it will be used.

## Schema

- description: Description of the cloudspace.
- vdcfarm: Specify vdc group. If not specified group will be auto created.
- g8client: User login.
- account: Account used for this space(if doesn't exist will be created), if empty will use existing account that belongs to the specified user.
- location: Environment to deploy this cloudspace.
- uservdc: Users to have access to this cloudpsace. Name is name of user service to be consumed and accesstype is the user access right to this cloudspace.
- allowedVMSizes: Specify the allowed size ids for virtual machines on this cloudspace.
- cloudspaceID: id of the cloudspace. **Filled in automatically, don't specify it in the blueprint**
- maxMemoryCapacity: Cloudspace limits, maximum memory(GB).
- maxCPUCapacity: Cloudspace limits, maximum CPU capacity.
- maxDiskCapacity: Cloudspace limits, maximum disk capacity(GB).
- maxNumPublicIP: Cloudspace limits, maximum allowed number of public IPs.
- externalNetworkID: External network to be attached to this cloudspace.
- maxNetworkPeerTransfer: Cloudspace limits, max sent/received network transfer peering(GB).
- disabled: True if the cloudspace is disabled. **Filled in automatically, don't specify it in the blueprint**

## User access rights

Use the uservdc parameter to specify the user access right to the vdc. Note that if only name exist in the entry(no accesstype) then the access right will be by default `ACDRUX`.

Note that the data in the blueprint is always reflected in the vdc, which means that removing an entry in the blueprint will remove or change it in the vdc. If the user only wants to edit some data then it is possible to do so by using processChange action.

Using process change it is possible to add, remove and update user access to the cloudspace. To add user after executing the run and creating the vdc, add a new user in the blueprint and execute the blueprint to trigger process change and add new user to the cloudspace or removing user by deleting the entry in the blueprint. Changing the accesstype will update the user access when executing the blueprint and as above removing it will change the access right to the default value `ACDRUX`.

## Access rights

For information about the different access rights check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Example for creating VDC

For authentication `g8client` service is needed to represent the user sending the requests to the environment API. The user needs to exist in the environment. The `account` will be the owner of the cloudpsace, the `account` service is created automatically if not specified in the blueprint. if the account exists it will be used otherwise it will be created.

The `g8client` and `account` services need to be consumed by the `vdc` service(see blueprint below). The blueprint will create a cloudspace on the specified environment and give access to users specified in the `uservdc` parameter, and set the cloudspace limits as specified.

For the creation of the vdc the action specified is install, to delete the vdc action uninstall needs to be specified in the `actions` parameter as seen in the second example below.

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

uservdc__usertest:
    password: 'test1234'
    email: 'fake@fake.com'
    groups:
      - user
    g8client: 'example'

vdcfarm__vdcfarm1:


vdc__cs2:
    description: '<description>'
    vdcfarm: 'vdcfarm1'
    g8client: 'example'
    account: '<account name>'
    location: '<name of the environment>'
    uservdc:
        - name: 'usertest'
          accesstype: 'ACDRUX'
    allowedVMSizes:
        - 1
        - 2
    maxMemoryCapacity: 10
    maxDiskCapacity: 15
    maxCPUCapacity: 4
    maxNetworkPeerTransfer: 15
    maxNumPublicIP: 7
actions:
  - action: install
```

## Example for Deleting VDC

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

vdc__cs2:
    location: '<name of the environment>'

actions:
  - action: uninstall
```

## Example for disabling VDC

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

vdc__cs2:
    location: '<name of the environment>'

actions:
  - action: disable
```

## Example for enabling VDC

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

vdc__cs2:
    location: '<name of the environment>'

actions:
  - action: enable
```

## Example for executing routeros script on VDC

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

vdc__cs2:
    location: '<name of the environment>'
    # script can be a single line i.e '/ip service set www address=0.0.0.0/0'
    # or use YAML multi lines using "|" i.e:
    # |
    # /ip service
    # set www address=0.0.0.0/0
    script: '<SCRIPT>'

actions:
  - action: execute_routeros_script
```
