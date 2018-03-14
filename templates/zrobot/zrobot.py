from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError
import gevent


class Zrobot(TemplateBase):

    version = '0.0.1'
    template_name = "zrobot"

    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    DOCKER_IMAGE = 'jumpscale/0-robot:latest'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._ovc = None
        self._account = None
        self._space = None

    def validate(self):
        for key in ['node', 'port']:
            if not self.data[key]:
                raise ValueError('%s is required' % key)

        # validate accounts
        nodes = self.api.services.find(template_uid=self.NODE_TEMPLATE, name=self.data['node'])

        if len(nodes) != 1:
            raise RuntimeError('found %s nodes, requires exactly one' % len(nodes))

    def _prepare_repos(self, prefab, base):
        for dir in ['data', 'config', 'ssh']:
            prefab.core.dir_ensure(j.sal.fs.joinPaths(base, dir))

        for dir in ['data', 'config']:
            prefab.core.run('cd %s && git init' % j.sal.fs.joinPaths(base, dir))

        key_dir = j.sal.fs.joinPaths(base, 'ssh')
        if not prefab.core.exists('%s/id_rsa' % key_dir):
            prefab.core.run('ssh-keygen -b 2048 -t rsa -f %s/id_rsa -q -N ""' % key_dir)

    @property
    def node(self):
        nodes = self.api.services.find(template_uid=self.NODE_TEMPLATE, name=self.data['node'])

        return nodes[0]

    def install(self, force=False):
        try:
            self.state.check('actions', 'install', 'ok')
            if not force:
                return
        except StateCheckError:
            pass

        node = j.tools.nodemgr.get(self.data['node'])
        prefab = node.prefab
        prefab.virtualization.docker.install()

        prefab.core.run('docker rm -vf %s' % self.name, die=False)

        prefab.core.run('docker pull %s' % self.DOCKER_IMAGE)
        base = '/opt/zrobot'
        self._prepare_repos(prefab, base)

        cfg = j.sal.fs.fileGetContents(
            j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), 'jumpscale9.toml')
        )

        prefab.core.file_write(
            j.sal.fs.joinPaths(base, 'jumpscale9.toml'),
            cfg.format(config=j.sal.fs.joinPaths(base, 'config'))
        )

        templates = ''
        for template in self.data['templates']:
            templates += ' -T %s' % template

        prefab.core.run('''\
        docker run -d --name {name} \
                -v {base}/data:/opt/code/github/zrobot/data \
                -v {base}/config:/opt/code/github/zrobot/config \
                -v {base}/ssh:/root/.ssh \
                -v {base}/jumpscale9.toml:/root/js9host/cfg/jumpscale9.toml \
                -p 6600:6600 \
                {image} \
                zrobot server start \
                    -C git@github.com:zrobot/config -D git@github.com:zrobot/data \
                    {templates}
        '''.format(
            name=self.name,
            base=base,
            image=self.DOCKER_IMAGE,
            templates=templates
        ))

        # expose port forward
        self.node.schedule_action(
            'portforward_create',
            {
                'ports': [{
                    'source': self.data['port'],
                    'destination': 6600,
                }]
            }
        )

        for i in range(10):
            if j.sal.nettools.tcpPortConnectionTest(node.addr, self.data['port']):
                break
            gevent.sleep(3)
        else:
            raise Exception('can not connect to robot "%s"' % self.name)

        j.clients.zrobot.get(
            self.name,
            create=True,
            data={
                'url': 'http://%s:%s' % (node.addr, self.data['port'])
            }
        )

        self.state.set('actions', 'install', 'ok')
