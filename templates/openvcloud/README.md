
# template: openvcloud

## Description

This template is responsible for configuring an OpenvCloud connection.

## Schema

- `address`: dns name of the openvcloud env. **Required**.
- `token`: Itsyou.online JWT token. **Required**.
- `location`: environment to connect to. **Required**.
- `port`: API port. Default to 443.
- `description`: Arbitrary description of the account. **Optional**.

## Example for creating a connection

```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__be-gen-1:
        location: be-gen-1
        address: 'be-gen-1.demo.greenitglobe.com'
        token: '<jwt token>'
```
