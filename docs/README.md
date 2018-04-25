# Communication with Zero-Robot

Each [Zero-Robot](https://github.com/zero-os/0-robot) exposes a RESTful API.
API requests allow to create/delete/manage services on the Zero-Robot. Each API call can be addressed to an individual service, as well as contain a blueprint with a list of services to create and list of actions to execute on the Zero-Robot.
There are several possibilities to send API calls:

* (recommended) directly with applications like Insomnia or Postman.
* (recommended) using the JumpScale client for Zero-Robot, this requires [JumpScale](https://github.com/Jumpscale) environment (easy to set up and use with Zero-Robot, convenient for automation).
* (not recommended) using the `zrobot` CLI tool, for sending blueprints and control services.

## Design

Network of Zero-Robots managing G8s depends on the use case and can be chosen.
We currently assume that you have one Zero-Robot per Partner Portal, responsible for managing all accounts, users, virtual datacenters (VDCs), virtual machines (nodes) and disks linked to that Partner Portal. This Zero-Robot can be deployed by another "master" Zero-Robot responsible monitoring all Zero-Robots, and deploying all partner portals.
All OpenvCloud objects (users, accounts, VDCs, VMs, and disks) are managed by services of corresponding type. Each service is an instance of a template, specifically designed to be used by a Zero-Robot.
Creating, deleting services and scheduling  tasks on the services is possible by sending API calls to the Zero-Robot managing an OpenvCloud account.
All actions for an OpenvCloud object have to be executed via Zero-Robot services, therefore, it is important that all communication (also from the VDC Control Panel) go through the Zero-Robot, and thus not directly to the G8s. This concept is illustrated by the figure below.
OpenvCloud templates with examples for communication with a Zero-Robot using the JumpScale client for Zero-Robot and the Zero-Robot CLI tool for creating services and managing OpenvCloud objects can be found [here](https://github.com/openvcloud/0-templates). Examples include creating and managing accounts, VDCs, VMs, and disks.

<img src="https://docs.google.com/drawings/d/e/2PACX-1vR7UL8ZphMb8P6fsvmmcT3HOITiu8bRK6lhD1ZTlA-sp5v-yg_sgC_WbC6dhB0r9pj2I_Q0axr8ZUFt/pub?w=713&h=625">