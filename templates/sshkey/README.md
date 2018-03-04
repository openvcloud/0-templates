# template: sshkey

## Description
This templates makes sure an ssh key is loaded in the agent.
Name of the service corresponds to the name of the key.
If doesn't exist, the key will be generated.

## Schema

- path: path to the ssh private key

## Example

```yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__<keyName>:
        dir: '/root/.ssh/'
        passphrase: <passphrase>
```
