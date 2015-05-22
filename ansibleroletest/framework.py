import appdirs
import click
import giturlparse
import os
import shutil
import six
import sys
import traceback
import uuid
import yaml

from .container import ExecuteReturnCodeError
from .test import Test
from .utils import pull_image_progress


def mktmpdir():
    """
    Due to OSX and boot2docker, I can't use the tempdir module as /tmp cannot
    be mounted in boot2docker (only /Users/<user> is available)
    """
    base_dir = appdirs.user_cache_dir('ansible_role_test', 'aeriscloud')
    tmp_dir = os.path.join(base_dir, uuid.uuid4().hex)
    os.makedirs(tmp_dir)
    return tmp_dir


class TestFramework(object):
    """
    This is our test framework, it takes care of creating the ansible images
    and setting up the role and it's dependencies, modules, etc...
    """
    TYPE_GALAXY = 'galaxy'
    TYPE_GIT = 'git'
    TYPE_LOCAL = 'local'

    def __init__(self, docker, role,
                 ansible_paths=None, ansible_version='latest'):
        self.ansible = None
        self.docker = docker
        self.role = role
        self.work_dir = mktmpdir()
        self.res = {'success': 0, 'skip': 0, 'failed': 0}
        self.ansible_version = ansible_version
        self.environment = {}

        # check the role type
        self.role_name = self.role
        self.role_path = '/etc/ansible/roles/{0}'.format(role)
        self.bindings = {self.work_dir: {'bind': '/work', 'ro': True}}
        self.type = TestFramework.TYPE_GALAXY

        self.ansible_paths = {
            'roles': None,
            'library': None,
            'plugins': {
                'action': None
            }
        }
        if ansible_paths:
            self.ansible_paths.update(ansible_paths)
            self.setup_bindings()

        if os.path.isdir(role):
            # role is a folder name, use that
            role = os.path.realpath(role)
            self.role_name = os.path.basename(role)
            self.role_path = '/etc/ansible/roles/{0}'.format(self.role_name)
            self.bindings[os.path.realpath(self.role)] = {
                'bind': self.role_path,
                'ro': True
            }
            self.type = TestFramework.TYPE_LOCAL
        elif role.endswith('.git') or '.git#' in role:
            # role is a git repository
            p = giturlparse.parse(role)

            self.role_name = p.repo
            self.role_path = '/etc/ansible/roles/{0}'.format(self.role_name)
            self.type = TestFramework.TYPE_GIT

    def cleanup(self):
        """
        Final cleanup, destroy any container created with our ContainerManager
        and delete temporary files before showing the test recap
        :return:
        """
        self.print_header('CLEANING TESTS')
        for name, container in six.iteritems(self.docker.containers):
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
        Check the meta file and install role dependencies recursively
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

                # try to get a role on galaxy if we do not have it
                role_path = os.path.join(self.ansible_paths['roles'],
                                         role_name)
                has_role_locally = self.ansible_paths['roles'] and \
                    os.path.exists(role_path)

                if '.' in role_name and not has_role_locally:
                    self.print_header('DEPENDENCY: [%s]' % role_name)
                    self.stream('ansible-galaxy', 'install', role_name)
                # otherwise copy it from the role-path if set
                else:
                    self.print_header('LOCAL DEPENDENCY: [%s]' % role_name)
                    if not self.ansible_paths['roles']:
                        raise ImportError(
                            'No roles path, please set --roles-path')
                    if not has_role_locally:
                        raise ImportError('Role %s was not found in %s' % (
                            role_name,
                            self.ansible_paths['roles']
                        ))
                    src_path = os.path.join('/roles', role_name)
                    target_path = '/etc/ansible/roles/{0}'.format(role_name)
                    click.echo('- copy from %s' % src_path)
                    self.ansible.execute(['cp', '-r', src_path, target_path])
                    roles.append(target_path)

                click.secho('ok: [%s]' % role_name, fg='green')

                installed.append(role_name)

    @staticmethod
    def print_header(text):
        """
        Helper method to display an ansible-like header
        :param text:
        :return:
        """
        click.echo('\n' + text + ' ' + ((78 - len(text)) * '*'))

    def run(self, extra_vars=None, limit=None, skip_tags=None,
            tags=None, verbosity=None, privileged=False):
        """
        Run all the tests
        :param extra_vars: extra vars to pass to ansible
        :param limit: limit on which targets to run the tests
        :param skip_tags: skip certain tags
        :param tags: run only those tags
        :param verbosity: augment verbosity of ansible
        :param privileged: start containers in privileged mode
        :return: 0 on success, 1 on error, 2 if no tests are found
        """
        try:
            self.print_header('TESTS [%s]' % self.role_name)
            self.setup_ansible()
            self.install_role_deps()

            for test in self.tests():
                test.run(
                    extra_vars=extra_vars,
                    limit=limit,
                    skip_tags=skip_tags,
                    tags=tags,
                    verbosity=verbosity,
                    privileged=privileged
                )
                self.res['success'] += 1

            if self.res['success'] == 0:
                # no tests
                self.print_header('NO TESTS')
                click.secho('warning: no test found', fg='yellow')
                return 2
            return 0
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
        Setup our ansible container, pulling it from the registry if necessary
        also if the repo is of type GIT or GALAXY, clone/download it
        """
        self.print_header('STARTING ANSIBLE')

        image_name = 'aeriscloud/ansible:' + self.ansible_version
        self.ansible = self.docker.create('ansible', tty=True,
                                          image=image_name,
                                          environment=self.environment)

        self.ansible.start(binds=self.bindings,
                           progress=pull_image_progress())

        if self.ansible.pulled:
            click.secho('pulled: [%s]' % self.ansible.image, fg='yellow')
        else:
            click.secho('ok: [%s]' % self.ansible.image, fg='green')

        if self.type == TestFramework.TYPE_GIT:
            self.print_header('GIT CLONE [%s]' % self.role)
            branch = None
            if '#' in self.role:
                self.role, branch = self.role.split('#')
            git_cmd = ['git', 'clone', self.role]
            if branch:
                git_cmd += ['-b', branch]
            git_cmd.append(self.role_path)
            self.stream(*git_cmd)
        elif self.type == TestFramework.TYPE_GALAXY:
            # role is an ansible galaxy role
            self.print_header('GALAXY [%s]' % self.role)
            self.stream('ansible-galaxy', 'install', self.role)

    def setup_bindings(self):
        """
        Setup ansible bidings based on the configuration passed
        """
        if self.ansible_paths['roles']:
            self.bindings[self.ansible_paths['roles']] = {
                'bind': '/roles',
                'ro': True
            }

        if self.ansible_paths['library']:
            self.bindings[self.ansible_paths['library']] = {
                'bind': '/usr/share/ansible/library',
                'ro': True
            }
            self.environment['ANSIBLE_LIBRARY'] = '/usr/share/ansible/library'

        if self.ansible_paths['plugins']['action']:
            self.bindings[self.ansible_paths['plugins']['action']] = {
                'bind': '/usr/share/ansible_plugins/action_plugins',
                'ro': True
            }

        if self.ansible_paths['plugins']['filter']:
            self.bindings[self.ansible_paths['plugins']['filter']] = {
                'bind': '/usr/share/ansible_plugins/filter_plugins',
                'ro': True
            }

        if self.ansible_paths['plugins']['lookup']:
            self.bindings[self.ansible_paths['plugins']['lookup']] = {
                'bind': '/usr/share/ansible_plugins/lookup_plugins',
                'ro': True
            }

    def stream(self, *cmd):
        """
        Run a command on the ansible container and stream the result
        to stdout
        """
        if not self.ansible:
            raise RuntimeError('ansible container is not running')
        for line in self.ansible.stream(cmd, tty=True):
            click.echo(line, nl=False)

    def tests(self):
        """
        Generator that yields Test objects found in the role
        :yield: Test
        """
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
