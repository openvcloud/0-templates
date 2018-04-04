# template: vdcuser

## Description

This template represents a user on an environment. If the user doesn't exist it will be created.

## Schema

- name (required): name of the vdc user on OpenVCloud.
- openvcloud (required): Name of the [openvcloud](../openvcloud) instance used to connect to the environment.
- password: Password of the user. (optional) if an Oauth provider is set.
- email: Email of the user.
- provider: Oauth provider. Currently: itsyou.online
- groups: Groups that the user will belong to.

## Actions

- `install`: install a vdcuser. Create a vdcuser if doesn't exist.
- `uninstall`: delete a vdcuser.
- `groups_set`: set user groups.

```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__myovc:
        location: be-gen-demo
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        openvcloud: myovc
        provider: itsyouonline
        email: admin@greenitglobe.com

actions:
      actions: ['install']
```


```yaml
actions:
  - service: admin
    actions: ['groups_set']
    args:
      groups:
        - group1
        - group2
```
