# template: sshkey

## Description
This templates makes sure an ssh key is loaded in the agent

## Schema

- path: path to the ssh private key

## Example

```yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__key:
        path: '/root/.ssh/id_rsa'
```
