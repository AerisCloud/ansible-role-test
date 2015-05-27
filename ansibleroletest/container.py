from __future__ import unicode_literals, absolute_import

import six
from six.moves.urllib.parse import urlparse

OOMKilled, Dead, Paused, Running, Restarting, Stopped = range(1, 7)


class ExecuteReturnCodeError(BaseException):
    def __init__(self, cmd, code=-1, output=None):
        super(ExecuteReturnCodeError, self).__init__(
            '%s exited with code %d' % (cmd, code))
        self.code = code
        self.output = output


class Container(object):
    _images = None

    def __init__(self, client, image, detach=True, **options):
        self._client = client
        self._props = {
            'image': image,
            'detach': detach
        }
        self._props.update(options)
        self._host_ip = None
        self._inspected = False
        self._pulled = False

    @property
    def host_ip(self):
        if self._client.base_url.startswith('unix://'):
            return '0.0.0.0'

        if not self._host_ip:
            o = urlparse(self._client.base_url)
            self._host_ip = o.hostname

        return self._host_ip

    @property
    def id(self):
        if 'id' not in self._props:
            return None
        return self._props['id']

    @property
    def image(self):
        return self._props['image']

    @property
    def images(self):
        if not Container._images:
            Container._images = {
                tag: image
                for image in self._client.images()
                for tag in image['RepoTags']
            }
        return Container._images

    @property
    def internal_ip(self):
        return self.inspect()['NetworkSettings']['IPAddress']

    @property
    def pulled(self):
        return self._pulled

    @property
    def state(self):
        state_info = self.inspect()['State']
        state = {
            'status': Stopped,
            'pid': state_info['Pid'],
            'started_at': state_info['StartedAt'],
            'finished_at': state_info['FinishedAt'],
            'exit_code': state_info['ExitCode'],
            'error': state_info['Error']
        }
        if state_info['OOMKilled']:
            state['status'] = OOMKilled
        if state_info['Dead']:
            state['status'] = Dead
        if state_info['Paused']:
            state['status'] = Paused
        if state_info['Running']:
            state['status'] = Running
        if state_info['Restarting']:
            state['status'] = Restarting
        return state

    def content(self, filename):
        """
        Kinda crude way to get the content from a file
        :param filename:
        :return:
        """
        try:
            return self.execute(['cat', filename])
        except ExecuteReturnCodeError:
            return ''

    def create(self, start=False, progress=None, **options):
        if self.image not in self.images:
            # pull image from repo
            if hasattr(progress, '__call__'):
                for line in self._client.pull(self.image,
                                              insecure_registry=True,
                                              stream=True):
                    progress(line)
                progress('finished')
            else:
                self._client.pull(self.image)

            # reset image list on success
            Container._images = None
            self._pulled = True

        self._props.update(options)
        res = self._client.create_container(**self._props)
        self._props['id'] = res['Id']
        if start:
            self.start(**options)
        return res['Id']

    def destroy(self, **options):
        if not self.id:
            return
        if self.state['status'] is Running:
            self.stop()
        self._client.remove_container(container=self.id, **options)

    def execute(self, cmd, **options):
        res = self._client.exec_create(container=self.id, cmd=cmd,
                                       **options)
        out = self._client.exec_start(exec_id=res['Id'])
        exec_res = self._client.exec_inspect(exec_id=res['Id'])
        if exec_res.get('ExitCode') != 0:
            raise ExecuteReturnCodeError(cmd[0], exec_res.get('ExitCode'), out)
        return out.decode('utf-8')

    def inspect(self, update=False):
        if update:
            self._inspected = False
        if not self._inspected:
            self._inspected = self._client.inspect_container(container=self.id)
        return self._inspected

    def port(self, port):
        res = self._client.port(self.id, port)
        if not res:
            return None
        return self.host_ip, res[0]['HostPort']

    def remove(self, **options):
        self._client.remove_container(container=self.id, **options)

    def start(self, progress=None, **options):
        if not self.id:
            self.create(progress=progress)

        options['container'] = self.id
        self._client.start(**options)
        self._inspected = False

    def stream(self, cmd, **options):
        res = self._client.exec_create(container=self.id, cmd=cmd,
                                       **options)
        out = self._client.exec_start(exec_id=res['Id'], stream=True)
        for line in out:
            yield line.decode('utf-8')
        exec_res = self._client.exec_inspect(exec_id=res['Id'])
        if exec_res.get('ExitCode') != 0:
            raise ExecuteReturnCodeError(cmd[0],
                                         exec_res.get('ExitCode'),
                                         None)

    def stop(self):
        self._client.stop(container=self.id)
        self._inspected = False

    def wait(self):
        return self._client.wait(container=self.id)


class ContainerManager(object):
    def __init__(self, docker):
        self._docker = docker
        self._containers = {}

    @property
    def client(self):
        return self._docker

    @property
    def containers(self):
        return self._containers.copy()

    def new(self):
        return ContainerManager(self._docker)

    def create(self, name, progress=None, start=False, **options):
        self._containers[name] = Container(self._docker, **options)
        if start:
            self._containers[name].start(progress=progress, **options)
        return self._containers[name]

    def destroy(self, names=None):
        if not hasattr(self, '_containers'):
            return
        if not names:
            names = []
        if not isinstance(names, list):
            names = [names]
        for name, container in six.iteritems(self.containers):
            if not names or name in names:
                container.destroy()
                del self._containers[name]

    def __del__(self):
        self.destroy()

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self.destroy()
