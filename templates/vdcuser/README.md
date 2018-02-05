# template: uservdc

## Description

This template represents a user on an environment. If the user doesn't exist it will be created.

## Schema

- password: Password of the user.
- email: Email of the user.
- provider: Oauth provider. Currently: itsyou.online
- groups: Groups that the user will belong to.
- g8client: User login.

## Example

* You will need to configure OVC client firstly: [docs](https://github.com/openvcloud/ays_templates/blob/master/docs/OVC_Client/README.md)
```yaml
g8client__{environment}:
  instance: '{ovc_config_instance(i.e. main)}'
  account: '{account}'

uservdc__ex:
    password: '<password>'
    email: '<email>'
    provider: 'itsyouonline'
    groups: '<list of groups>'
    g8client: 'example'
    
actions:
  - action: install
```
