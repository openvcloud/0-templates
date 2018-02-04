
# template: ovc.account

## Description:
This actor template is responsible for creating an account on any openVCloud environment.

## Schema:

- description: Arbitrary description of the account. **Optional**

- openvcloud: Name of the g8client used to connect to the environment.

- users: List of vcdusers that will be authorized on the account.

- accountID: The ID of the account. **Filled in automatically, don't specify it in the blueprint**

- maxMemoryCapacity: The limit on the memory capacity that can be used by the account. Default: -1 (unlimited)

- maxCPUCapacity: The limit on the CPUs that can be used by the account. Default: -1 (unlimited)

- maxNumPublicIP: The limit on the number of public IPs that can be used by the account. Default: -1 (unlimited)

- maxDiskCapacity: The limit on the disk capacity that can be used by the account. Default: -1 (unlimited)

- consumptionFrom: determines the start date of the required period to fetch the account consumption info from. If left empty will be creation time of the account.

- consumptionTo: determines the end date of the required period to fetch the account consumption info from. If left empty will be consumptionfrom + 1 hour.

- consumptionData: consumption data will be saved here as series of bytes which represents a zip file. Example of writing the data:
```
service = response.json() # response is the service view that can be obtained from getServiceByName
with open('/tmp/account.zip', 'wb') as f:
    f.write(service['data']['consumptionData'])
```

## Add/remove/update user

Use the accountusers parameter to specify the user access right to the account. Note that if only name exist in the entry(no accesstype) then the access right will be by default `ACDRUX`.

Note that the data in the blueprint is always reflected in the account, which means that removing an entry in the blueprint will remove or change it in the account. If the user only wants to edit some data then it is possible to do so by using processChange action.

>This is especially relevant to the account template because it is possible to remove the user who created the account(which might be the g8client), so it is very important to reflect that in the blueprint with correct access rights. The original user can be removed if another user with admin access is specified in the blueprint. But the user specified in g8client should be in this case different than the original user.
This means that unlike node and vdc templates if no users are sepcified, there would be no change to the account access, so for example if it is required to remove all access except the owner, the owner needs to be specified in the users list.

It is possible to add, remove and update user access to the account. To add a user after creating the account, a new uservdc has to be added in the blueprint. Executing the blueprint will trigger the process change and add it to the account. In the same way a user can be removed from the account by deleting the entry from the accountusers in the blueprint. Changing the accesstype of as user will update the user access to the account when executing the blueprint and as above removing it will change the access right to the default value `ACDRUX`.

## Access rights

For information about the different access rights check docs at [openvcloud](https://github.com/0-complexity/openvcloud/blob/2.1.7/docs/EndUserPortal/Authorization/AuthorizationModel.md).

## Example for creating an account

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

uservdc__<username>:

account__acc:
  description: 'test account'
  g8client: 'env'
  accountusers:
    - name: '<username>'
      accesstype: '<accesstype>'
  maxMemoryCapacity: <value>
  maxCPUCapacity:  <value>
  maxDiskCapacity: <value>
  maxNumPublicIP: <value>

actions:
  - action: install
```

## Example for adding user 'usertest' to account

```yaml
uservdc__usertest:
    password: 'test1234'
    email: 'fake@example.com'
    groups:
      - 'user'
    g8client: 'env'

account__acc:
  accountusers:
      - name: '<username>'
        accesstype: '<accesstype>'
      - name: 'usertest'
        accesstype: '<accesstype>'

```

## Example for changing access rights of user 'usertest'

```yaml
account__acc:
  accountusers:
      - name: '<username>'
        accesstype: '<accesstype>'
      - name: 'usertest'
        accesstype: '<changed_accesstype>'

```

## Example for removing user 'usertest' from account

```yaml
account__acc:
  accountusers:
    - name: '<username>'
      accesstype: '<accesstype>'
```

## Example for updating the limits of the account

```yaml
account__acc:
    maxMemoryCapacity: <changed_value>
    maxCPUCapacity: <changed_value>
    maxDiskCapacity: <changed_value>
    maxNumPublicIP: <changed_value>
```


## Example for listing disks associated with account:

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'


account__account1:

actions:
  - action: install
    actor: g8client
    service: env
  - action: list_disks
    actor: account
    service: account1
```

## Example for getting consumption info

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

account__acc:
  description: 'test account'
  g8client: 'env'
  consumptionFrom: <start epoch>
  consumptionTo: <end epoch>

actions:
  - action: get_consumption
```
