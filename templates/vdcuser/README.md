# template: vdcuser

## Description

This template represents a user on an environment. If the user doesn't exist it will be created.

## Schema

- openvcloud (required): Name of the [openvcloud](../openvcloud) instance used to connect to the environment.
- password: Password of the user. (optional) is an Oauth provider is set
- email: Email of the user.
- provider: Oauth provider. Currently: itsyou.online
- groups: Groups that the user will belong to.

## Example

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

actions:
      actions: ['install']
```

## Actions
### `groups_set` set user groups
```yaml
actions:
  - service: admin
    actions: ['groups_set']
    args:
      groups:
        - group1
        - group2
```