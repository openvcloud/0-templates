# template: github.com/openvcloud/0-templates/sshkey/0.0.1

## Description

This templates makes sure an ssh key is loaded in the agent.
If doesn't exist, the key will be generated with given passphrase.
If the sshkey with given name exists in the directory, the service will try to use this key with provided passphrase.

## Schema

- `name`: name of the sskhey. **Required**.
- `dir`: path to the ssh private key. **Required**.
- `passphrase`: passphrase of the sshkey key with minimum length 5 symbols. **Required**.

## Actions

- `install`: install `sshkey` service, if key with given key doesn't exist, it will be created and uploaded to the ssh agent.
- `uninstall`: delete sshkey managed by the service.

## Usage examples via the 0-robot DSL

``` python
from zerorobot.dsl import ZeroRobotAPI
api = ZeroRobotAPI.ZeroRobotAPI()
robot = api.robots['main']

# create service
sshkey = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/sshkey/0.0.1",
    service_name="key-service",
    data={'name': 'id_rsa', 'dir':'/root/.ssh/', 'passphrase': 'testpassphrase'}
)
sshkey.schedule_action('install')
sshkey.schedule_action('uninstall')
```

## Usage examples via the 0-robot CLI

```yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__<keyName>:
        name: id_test
        dir: '/root/.ssh/'
        passphrase: <passphrase>
actions:
    - actions: ['install']
```

```yaml
actions:
    - actions: ['uninstall']
```
