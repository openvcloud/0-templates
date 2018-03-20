# template: sshkey

## Description
This templates makes sure an ssh key is loaded in the agent.
Name of the service corresponds to the name of the key.
If doesn't exist, the key will be generated with given passphrase.
If the sshkey exists in the given directory, the service will try to use this key with provided passphrase.

## Schema

- `dir`: path to the ssh private key. **required**
- `passphrase`: passphrase of the sshkey key with minimum length 5 symbols. **required**

## Example

```yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__<keyName>:
        dir: '/root/.ssh/'
        passphrase: <passphrase>
```
