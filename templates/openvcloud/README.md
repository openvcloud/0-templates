
# template: openvcloud

## Description:
This template is responsible for configuring an openvcloud connection

## Schema:

- description: Arbitrary description of the account. **Optional**
- address: dns name of the openvcloud env
- port: (optional) API port, default to 443
- login: Username of the connection
- token: Itsyou.online JWT token

## Example for creating a connection
```yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__key:
        path: '/root/.ssh/id_rsa'
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__be-gen-1:
        address: 'be-gen-1.demo.greenitglobe.com'
        login: '<username>'
        token: '<jwt token>'
```
