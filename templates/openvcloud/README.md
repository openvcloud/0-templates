# template: github.com/openvcloud/0-templates/openvcloud/0.0.1

## Description

This template is responsible for configuring an OpenvCloud(OVC) connection.

## Schema

- `name`: name of OVC connection instance. **Required**.
- `address`: dns name of the OpenvCloud env. **Required**.
- `token`: Itsyou.online JWT token. **Required**.
- `location`: environment to connect to. **Required**.
- `port`: API port. Default to 443.
- `description`: Arbitrary description. **Optional**.

## Actions

- `install`: configure OVC connection in config manager.
- `uninstall`: delete instance of OVC connection form local config manager.
- `update`: update data fields of OVC service and reconfigure connection.

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
ovc.schedule_action('update', {'address': 'new_address.demo.com'})
ovc.schedule_action('uninstall')
```

## Usage examples via the 0-robot CLI

```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovc:
        name: 'be-gen-demo'
        location: be-gen-1
        address: 'be-gen-1.demo.greenitglobe.com'
        token: '<jwt token>'
actions:
    - actions: ['install']
```

```yaml
actions:
    - actions: ['update']
      service: ovc
      args:
        address: new_address.demo.com
```

```yaml
actions:
    - actions: ['uninstall']
      service: ovc
```