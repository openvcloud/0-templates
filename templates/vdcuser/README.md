# template: vdcuser

## Description

This template represents a user on an environment. If the user doesn't exist it will be created. Service of type `vdcuser` depends on a service of type [`ovc`](../openvcloud).

## Schema

- `name`: name of the vdc user on OpenVCloud. **Required**.
- `openvcloud`: Name of the [openvcloud](../openvcloud) instance used to connect to the environment. **Required**.
- `email`: Email of the user. **Required**.
- `provider`: Oauth provider. Default to `itsyouonline`.
- `groups`: Groups that the user will belong to. **Optional**.
- `password`: Password of the user. Used only if `provider` is set to an empty string. **Optional**.

## Actions

- `install`: install a vdcuser. Create a vdcuser if doesn't exist.
- `uninstall`: delete a vdcuser.
- `groups_set`: set user groups.

## Usage examples via the 0-robot DSL

``` python
from zerorobot.dsl import ZeroRobotAPI
api = ZeroRobotAPI.ZeroRobotAPI()
robot = api.robots['main']

# create services
ovc = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/openvcloud/0.0.1",
    service_name="ovc_service",
    data={'name': 'ovc_instance',
          'location':'be-gen-demo', 
          'address': 'ovc.demo.greenitglobe.com',
          'token': '<iyo jwt token>'}
)
ovc.schedule_action('install')
vdcuser = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/vdcuser/0.0.1",
    service_name="admin",
    data={'name': 'username', 'openvcloud':'ovc_service', 'email': 'email@mail.be'}
)
vdcuser.schedule_action('install')
vdcuser.schedule_action('groups_set', {'groups': ['group1', 'group2']})
vdcuser.schedule_action('uninstall')
```

## Usage examples via the 0-robot CLI

```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__myovc:
        name: be-gen-demo
        location: be-gen-demo
        address: 'ovc.demo.greenitglobe.com'
        token: '<iyo jwt token>'
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__admin:
        name: username
        openvcloud: myovc
        provider: itsyouonline
        email: admin@greenitglobe.com
actions:
    - actions: ['install']
```

```yaml
actions:
    - actions: ['uninstall']
      service: admin
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
