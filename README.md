# 0-templates [![Build Status](https://travis-ci.org/openvcloud/0-templates.svg?branch=master)](https://travis-ci.org/openvcloud/0-templates) [![codecov](https://codecov.io/gh/openvcloud/0-templates/branch/master/graph/badge.svg)](https://codecov.io/gh/openvcloud/0-templates)

This repo contains OpenvCloud (OVC) templates that can be managed by [0-robot](https://github.com/Jumpscale/0-robot).

Templates:

- [account template](https://github.com/openvcloud/0-templates/tree/master/templates/account):
  - create and delete accounts
  - add and delete users
  - update account flags
- [openvcloud template](https://github.com/openvcloud/0-templates/tree/master/templates/openvcloud):
  - create connection to OVC
- [vdc template](https://github.com/openvcloud/0-templates/tree/master/templates/vdc)
  - create and delete VDC (Vertual Data Center)
  - add and delete portforwars
  - add and delete VDC users
- [vdcuser template](https://github.com/openvcloud/0-templates/tree/master/templates/vdcuser):
  - authorize and unauthorize vdc users, create a user if doesn't exists
  - set user groups
- [sshkey template](https://github.com/openvcloud/0-templates/tree/master/templates/sshkey):
  - upload ssh-key
- [node template](https://github.com/openvcloud/0-templates/blob/master/templates/node/node.py):
  - create virtual machines (VMs)
  - manage VMs: start, stop, reset, delete, clone
  - create and delete snapshots of VMs
  - add and delete portforwards
- [disk template](https://github.com/openvcloud/0-templates/blob/master/templates/disk/disk.py):
  - create and delete disks
 
 
Contribution:

Please check the [contribution](https://github.com/zero-os/0-templates/blob/master/CONTRIBUTING.md) guidelines before contributing to this repo.
