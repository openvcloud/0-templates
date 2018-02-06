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

    def get_openvcloud(self):
        return self.data['openvcloud']

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

        self._authorize_users(account)

        # update capacity in case account already existed
        account.model['maxMemoryCapacity'] = self.data['maxMemoryCapacity']
        account.model['maxVDiskCapacity'] = self.data['maxDiskCapacity']
        account.model['maxNumPublicIP'] = self.data['maxNumPublicIP']
        account.model['maxCPUCapacity'] = self.data['maxCPUCapacity']
        account.save()

        self.state.set('actions', 'install', 'ok')

    def _authorize_users(self, account):
        users = {}
        VDCUSER_TEMPLATE = 'github.com/openvcloud/0-templates/vdcuser/0.0.1'
        for user in self.data['users']:
            found = self.api.services.find(template_uid=VDCUSER_TEMPLATE, name=user['name'])
            if len(found) != 1:
                raise ValueError('no vdcuser found with name "%s"', user['name'])

            instance = found[0]
            task = instance.schedule_action('get_fqid')
            task.wait()

            users[task.result] = user['accesstype']

        authorized = {user['userGroupId']: user['right'] for user in account.model['acl']}

        toremove = []
        for user, current_perm in authorized.items():
            new_perm = users.pop(user, None)
            if new_perm is None:
                # user has been removed
                # we delay removing the user to avoid deleting the last admin, in case a new one is added
                toremove.append(user)
            elif new_perm != current_perm:
                account.update_access(username=user, right=new_perm)

        for user, new_perm in users.items():
            account.authorize_user(username=user, right=new_perm)

        for user in toremove:
            account.unauthorize_user(username=user)

    def uninstall(self):
        cl = self.ovc
        acc = cl.account_get(self.name)
        acc.delete()


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
