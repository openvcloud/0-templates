from js9 import j
from zerorobot.template.base import TemplateBase


class Account(TemplateBase):

    version = '0.0.1'
    template_name = "account"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._validate_data()

    def _validate_data(self):
        OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
        ovcs = self.api.services.find(template_uid=OVC_TEMPLATE, name=self.data.get('openvcloud', None))

        if len(ovcs) != 1:
            raise RuntimeError('found %s openvcloud connections, requires exactly 1' % len(ovcs))

        self.data['openvcloud'] = ovcs[0].name

        # validate users
        VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
        for user in self.data['users']:
            users = self.api.services.find(template_uid=VDCUSER_TEMPLATE, name=user['name'])
            if len(users) != 1:
                raise ValueError('no vdcuser found with name "%s"', user['name'])

    @property
    def ovc(self):
        return j.clients.openvcloud.get(self.data['openvcloud'])

    def install(self):
        cl = self.ovc
        # Set limits
        # if account does not exist, it will create it
        account = cl.account_get(
            name=self.name,
            create=True,
            maxMemoryCapacity=self.data['maxMemoryCapacity'],
            maxVDiskCapacity=self.data['maxDiskCapacity'],
            maxCPUCapacity=self.data['maxCPUCapacity'],
            maxNumPublicIP=self.data['maxNumPublicIP'],
        )

        self.data['accountID'] = account.model['id']

        # TODO: fix authorize_user
        # authorization_user(account, service, g8client)

        # Unauthorize users not in the schema
        # THIS FUNCTIONALITY IS DISABLED UNTIL OVC DOESN'T REQUIRE USERS TO BE ADMIN

        # update capacity in case account already existed
        account.model['maxMemoryCapacity'] = self.data['maxMemoryCapacity']
        account.model['maxVDiskCapacity'] = self.data['maxDiskCapacity']
        account.model['maxNumPublicIP'] = self.data['maxNumPublicIP']
        account.model['maxCPUCapacity'] = self.data['maxCPUCapacity']
        account.save()

        self.state.set('actions', 'install', 'ok')

# def init_actions_(service, args):
#     dependencies = {
#         'list_disks': ['init'],
#         'get_consumption': ['install']
#     }
#     return dependencies


# def init(job):
#     service = job.service
#     if 'g8client' not in service.producers:
#         raise j.exceptions.AYSNotFound("No producer g8client found. Cannot continue init of %s" % service)

#     users = service.model.data.accountusers
#     for user in users:
#         uservdc = service.aysrepo.serviceGet('uservdc', user.name)
#         service.consume(uservdc)

#     service.saveAll()


def authorization_user(account, service, g8client):
    authorized_users = account.authorized_users

    userslist = service.producers.get('uservdc', [])
    if not userslist:
        return
    users = []
    user_exists = True
    for u in userslist:
        if u.model.data.provider != '':
            users.append(u.model.dbobj.name + "@" + u.model.data.provider)
        else:
            users.append(u.model.dbobj.name)

    # Authorize users
    for user in users:
        if user not in authorized_users:
            user_exists = False
        for uvdc in service.model.data.accountusers:
            if uvdc.name == user.split('@')[0]:
                if user_exists:
                    for acl in account.model['acl']:
                        if acl['userGroupId'] == user and acl['right'] != uvdc.accesstype:
                            account.update_access(username=user, right=uvdc.accesstype)
                else:
                    account.authorize_user(username=user, right=uvdc.accesstype)
        # Unauthorize users not in the schema
    for user in authorized_users:
        if user not in users:
            if user == g8client.model.data.login:
                raise j.exceptions.Input("Can't remove current authenticating user: %s. To remove use another user for g8client service." % user)
            account.unauthorize_user(username=user)


def get_user_accessright(username, service):
    for u in service.model.data.accountusers:
        if u.name == username:
            return u.accesstype





def processChange(job):
    service = job.service

    if 'g8client' not in service.producers:
        raise j.exceptions.AYSNotFound("No producer g8client found. Cannot continue processChange of %s" % service)

    g8client = service.producers["g8client"][0]
    config_instance = "{}_{}".format(g8client.aysrepo.name, g8client.model.data.instance)
    cl = j.clients.openvcloud.get(instance=config_instance, create=False, die=True, sshkey_path="/root/.ssh/ays_repos_key")
    account = cl.account_get(name=service.model.dbobj.name, create=False)

    args = job.model.args
    category = args.pop('changeCategory')
    if category == "dataschema" and service.model.actionsState['install'] == 'ok':
        for key, value in args.items():
            if key == 'accountusers':
                # value is a list of (uservdc)
                if not isinstance(value, list):
                    raise j.exceptions.Input(message="%s should be a list" % key)

                if 'uservdc' in service.producers:
                    for s in service.producers['uservdc']:
                        if not any(v['name'] == s.name for v in value):
                            service.model.producerRemove(s)
                        for v in value:
                            accessRight = v.get('accesstype', '')
                            if v['name'] == s.name and accessRight != get_user_accessright(s.name, service) and accessRight:
                                name = s.name + '@' + s.model.data.provider if s.model.data.provider else s.name
                                account.update_access(name, v['accesstype'])

                for v in value:
                    userservice = service.aysrepo.serviceGet('uservdc', v['name'])
                    if userservice not in service.producers.get('uservdc', []):
                        service.consume(userservice)
            setattr(service.model.data, key, value)

        authorization_user(account, service, g8client)

        # update capacity
        account.model['maxMemoryCapacity'] = service.model.data.maxMemoryCapacity
        account.model['maxVDiskCapacity'] = service.model.data.maxDiskCapacity
        account.model['maxNumPublicIP'] = service.model.data.maxNumPublicIP
        account.model['maxCPUCapacity'] = service.model.data.maxCPUCapacity
        account.save()

        service.save()


def uninstall(job):
    service = job.service
    if 'g8client' not in service.producers:
        raise j.exceptions.AYSNotFound("No producer g8client found. Cannot continue uninstall of %s" % service)

    g8client = service.producers["g8client"][0]
    config_instance = "{}_{}".format(g8client.aysrepo.name, g8client.model.data.instance)
    cl = j.clients.openvcloud.get(instance=config_instance, create=False, die=True, sshkey_path="/root/.ssh/ays_repos_key")
    acc = cl.account_get(service.model.dbobj.name)
    acc.delete()


def list_disks(job):
    service = job.service
    g8client = service.producers["g8client"][0]
    config_instance = "{}_{}".format(g8client.aysrepo.name, g8client.model.data.instance)
    cl = j.clients.openvcloud.get(instance=config_instance, create=False, die=True, sshkey_path="/root/.ssh/ays_repos_key")
    account = cl.account_get(name=service.model.dbobj.name)
    service.model.disks = account.disks
    service.save()


def get_consumption(job):
    import datetime
    service = job.service
    g8client = service.producers["g8client"][0]
    config_instance = "{}_{}".format(g8client.aysrepo.name, g8client.model.data.instance)
    cl = j.clients.openvcloud.get(instance=config_instance, create=False, die=True, sshkey_path="/root/.ssh/ays_repos_key")
    account = cl.account_get(name=service.model.dbobj.name)
    if not service.model.data.consumptionFrom and not service.model.data.consumptionTo:
        service.model.data.consumptionFrom = account.model['creationTime']
        end = datetime.datetime.fromtimestamp(service.model.data.consumptionFrom) + datetime.timedelta(hours=1)
        service.model.data.consumptionTo = end.timestamp()
    service.model.data.consumptionData = account.get_consumption(service.model.data.consumptionFrom, service.model.data.consumptionTo)
