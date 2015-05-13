import click
import giturlparse
import os
import shutil
import sys
import tempfile
import traceback
import yaml

from .container import ExecuteReturnCodeError
from .test import Test

class TestFramework(object):
    TYPE_GALAXY = 'galaxy'
    TYPE_GIT = 'git'
    TYPE_LOCAL = 'local'

    def __init__(self, docker, role, roles_path, ansible_version='latest'):
        self.ansible = None
        self.docker = docker
        self.role = role
        self.roles_path = roles_path
        self.work_dir = tempfile.mkdtemp(prefix='ansible-test')
        self.res = {'success':0, 'skip':0, 'failed':0}
        self.ansible_version = ansible_version

        # check the role type
        self.role_name = self.role
        self.role_path = '/etc/ansible/roles/{0}'.format(role)
        self.bindings =  {self.work_dir: '/work'}
        self.type = TestFramework.TYPE_GALAXY

        if roles_path:
            self.bindings[roles_path] = '/roles'

        if os.path.isdir(role):
            # role is a folder name, use that
            self.role_name = os.path.basename(role)
            self.role_path = '/etc/ansible/roles/{0}'.format(self.role_name)
            self.bindings[os.path.realpath(self.role)] = self.role_path
            self.type = TestFramework.TYPE_LOCAL
        elif role.endswith('.git') or '.git#' in role:
            # role is a git repository
            p = giturlparse.parse(role)

            self.role_name = p.repo
            self.role_path = '/etc/ansible/roles/{0}'.format(self.role_name)
            self.type = TestFramework.TYPE_GIT

    def cleanup(self):
        self.print_header('CLEANING TESTS')
        for name, container in self.docker.containers.copy().iteritems():
            self.docker.destroy(name)
            click.secho('ok: [%s]' % container.image, fg='green')

        # remove temp folder
        shutil.rmtree(self.work_dir)

        self.print_header('TESTS RECAP')
        click.echo(
            '%-27s: %s    %s    %s' % (
                click.style(self.role_name, fg='yellow'),
                click.style('success=%d' % self.res['success'], fg='green'),
                click.style('skip=%d' % self.res['skip'], fg='blue'),
                click.style('failed=%d' % self.res['failed'], fg='red'),
            )
        )

    def install_role_deps(self):
        """
        Check the meta file and install role dependencies
        :param ansible:
        :param role_path:
        """
        installed = []
        roles = [self.role_path]
        for role in roles:
            meta = self.ansible.content(os.path.join(role, 'meta', 'main.yml'))
            if not meta:
                continue

            metadata = yaml.load(meta)
            if 'dependencies' not in metadata or not metadata['dependencies']:
                continue

            for dependency in metadata['dependencies']:
                if 'role' not in dependency:
                    continue

                role_name = dependency['role']
                if role_name in installed:
                    continue

                if '.' in role_name:
                    self.print_header('DEPENDENCY: [%s]' % role_name)
                    self.stream('ansible-galaxy', 'install', role_name)
                else:
                    self.print_header('LOCAL DEPENDENCY: [%s]' % role_name)
                    if not self.roles_path:
                        raise ImportError('No roles path, please set --roles-path')
                    src_path = os.path.join('/roles', role_name)
                    target_path = '/etc/ansible/roles/{0}'.format(role_name)
                    click.echo('- copy from %s' % src_path)
                    self.ansible.execute(['cp', '-r', src_path, target_path])
                    roles.append(target_path)

                click.secho('ok: [%s]' % role_name, fg='green')

                installed.append(role_name)

    def print_header(self, text):
        click.echo('\n' + text + ' ' + ((78 - len(text)) * '*'))

    def run(self):
        try:
            self.print_header('TESTS [%s]' % self.role_name)
            self.setup_ansible()
            self.install_role_deps()

            for test in self.tests():
                test.run()
                self.res['success'] += 1

            if self.res['success'] == 0:
                # no tests
                self.print_header('NO TESTS')
                click.secho('warning: no test found', fg='yellow')
                return 2
        except:
            self.print_header('EXCEPTION')

            _, e, tb = sys.exc_info()
            click.secho('', fg='red', reset=False)
            traceback.print_tb(tb)
            click.secho('\n  %s' % str(e), fg='red', err=True)
            self.res['failed'] += 1
            return 1
        finally:
            self.cleanup()

    def setup_ansible(self):
        """
        Setup our ansible container
        :param docker: Instance of ContainerManager
        :param work_dir: Temp work dir used by the app
        :param ansible_version: The ansible version we want to use
        :param role: The role to test
        :return:
        """
        self.print_header('STARTING ANSIBLE')

        self.ansible = self.docker.create('ansible', tty=True,
                                          image='wizcorp/ansible:' + self.ansible_version)
        self.ansible.start(binds=self.bindings)
        click.secho('ok: [%s]' % self.ansible.image, fg='green')

        if self.type == TestFramework.TYPE_GIT:
            self.print_header('GIT CLONE [%s]' % self.role)
            branch = None
            if '#' in self.role:
                role, branch = self.role.split('#')
            git_cmd = ['git', 'clone', role]
            if branch:
                git_cmd += ['-b', branch]
            git_cmd.append(self.role_path)
            self.stream(*git_cmd)
        elif self.type == TestFramework.TYPE_GALAXY:
            # role is an ansible galaxy role
            self.print_header('GALAXY [%s]' % self.role)
            self.stream('ansible-galaxy', 'install', self.role)

        #install_role_deps(ansible, role_path)

    def stream(self, *cmd):
        if not self.ansible:
            raise RuntimeError('ansible container is not running')
        for line in self.ansible.stream(cmd, tty=True):
            click.echo(line, nl=False)

    def tests(self):
        try:
            # not the most elegent way to do things
            tests = [
                test.strip()
                for test in self.ansible.execute(
                    ['ls', '-1', os.path.join(self.role_path, 'tests')]
                ).split('\n')
                if test.strip() and test.strip().endswith('.yml')
            ]
        except ExecuteReturnCodeError as e:
            if e.code != 2:
                raise
            return

        for test in tests:
            test_file = os.path.join(self.role_path, 'tests', test.strip())
            test = yaml.load(self.ansible.content(test_file))
            yield Test(self, test)