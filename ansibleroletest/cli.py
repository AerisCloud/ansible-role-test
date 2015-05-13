from __future__ import print_function

import click
import os
import shutil
import sys
import tempfile
import traceback
import yaml

from giturlparse import parse

from .container import ContainerManager
from .docker import client as docker_client


class ExecuteReturnCodeError(BaseException):
    def __init__(self, cmd, code):
        super(ExecuteReturnCodeError, self).__init__('%s exited with code %d' % (cmd, code))
        self._code = code

    @property
    def code(self):
        return self._code


def ansible_header(text):
    """
    Display an ansible-like header
    :param text:
    :return:
    """
    click.echo('\n' + text + ' ' + ((78 - len(text)) * '*'))


def run(container, cmd):
    """
    Run a command and return the output code and command result
    :param container:
    :param cmd:
    :return:
    """
    out, res = container.execute(cmd, tty=True)
    if res.get('ExitCode') != 0:
        raise ExecuteReturnCodeError(cmd[0], res.get('ExitCode'))

    return out


def stream(container, cmd):
    """
    Stream a command to stdout
    :param container:
    :param cmd:
    :return: None
    :raise: ExecuteReturnCodeError on exitcode not zero
    """
    res = {}
    for line in container.stream(cmd, tty=True):
        if not isinstance(line, basestring):
            res = line
            break
        click.echo(line, nl=False)

    if not res:
        raise RuntimeError('error while running %s' % cmd[0])

    if res.get('ExitCode') != 0:
        raise ExecuteReturnCodeError(cmd[0], res.get('ExitCode'))


def generate_inventory(targets):
    """
    Generate an inventory for the given test
    :param targets:
    :return:
    """
    inventory = '[test]\n'
    for name, container in targets.iteritems():
        inventory += '{0} ansible_ssh_host={1} ansible_ssh_user=ansible ' \
                     'ansible_ssh_pass=ansible\n'\
            .format(name,container.internal_ip)
    return inventory


def setup_ansible(docker, work_dir, ansible_version, role):
    """
    Setup our ansible container
    :param docker: Instance of ContainerManager
    :param work_dir: Temp work dir used by the app
    :param ansible_version: The ansible version we want to use
    :param role: The role to test
    :return:
    """
    ansible_header('STARTING ANSIBLE')

    ansible = docker.create('ansible', tty=True,
                            image='wizcorp/ansible:' + ansible_version)
    binds = {
        work_dir: '/work'
    }

    role_name = role
    role_path = '/etc/ansible/roles/{0}'.format(role)
    if os.path.isdir(role):
        # role is a folder name, use that
        role_name = os.path.basename(role)
        role_path = '/etc/ansible/roles/{0}'.format(role_name)

        binds[os.path.realpath(role)] = role_path
        ansible.start(binds=binds)
        click.secho('ok: [%s]' % ansible.image, fg='green')

        install_role_deps(ansible, role_path)
    elif role.endswith('.git') or '.git#' in role:
        # role is a git repository
        p = parse(role)

        role_name = p.repo
        role_path = '/etc/ansible/roles/{0}'.format(role_name)
        ansible.start(binds=binds)
        click.secho('ok: [%s]' % ansible.image, fg='green')

        ansible_header('GIT CLONE [%s]' % role)
        branch = None
        if '#' in role:
            role, branch = role.split('#')
        git_cmd = ['git', 'clone', role]
        if branch:
            git_cmd += ['-b', branch]
        git_cmd.append(role_path)
        stream(ansible, git_cmd)

        install_role_deps(ansible, role_path)
    else:
        # role is an ansible galaxy role
        ansible.start(binds=binds)
        click.secho('ok: [%s]' % ansible.image, fg='green')

        ansible_header('GALAXY [%s]' % role)
        stream(ansible, ['ansible-galaxy', 'install', role])

    return ansible, role_path, role_name


def install_role_deps(ansible, role_path):
    """
    Check the meta file and install role dependencies
    :param ansible:
    :param role_path:
    """
    try:
        meta = run(ansible,
                   ['cat', os.path.join(role_path, 'meta', 'main.yml')])
    except ExecuteReturnCodeError as e:
        if e.code != 2:
            raise
        return

    metadata = yaml.load(meta)
    if 'dependencies' not in metadata or not metadata['dependencies']:
        return

    done = []
    for dependency in metadata['dependencies']:
        if not 'role' in dependency:
            continue

        role_name = dependency['role']
        if role_name in done:
            continue

        ansible_header('DEPENDENCY: [%s]' % role_name)
        stream(ansible, ['ansible-galaxy', 'install', role_name])
        done.append(role_name)


def get_tests(ansible, role_path):
    """
    Generator that retrieves the list of tests from the container and yield the yaml object
    :param ansible:
    :param role_path:
    :return:
    """
    try:
        tests = run(ansible,
                    ['ls', '-1', os.path.join(role_path, 'tests')])
    except ExecuteReturnCodeError as e:
        if e.code != 2:
            raise
        return

    for test in str(tests).split('\n'):
        if not test.strip():
            continue

        test_file = os.path.join(role_path, 'tests', test.strip())
        if not test_file.endswith('.yml'):
            continue

        test = yaml.load(run(ansible, ['cat', test_file]))
        yield test


def run_test(docker, ansible, work_dir, role_name, test):
    """
    Spawn docker images for the test, generate the inventory and playbook then run it
    :param docker:
    :param ansible:
    :param work_dir:
    :param test:
    :return:
    """
    ansible_header('TEST [%s]' % test['name'])

    containers = {}
    try:
        # create test containers
        ansible_header('STARTING CONTAINERS')

        for name, image in test['containers'].iteritems():
            full_image = 'aeriscloud/ansible-%s' % image
            container = docker.create(name, image=full_image)
            container.start()
            click.secho('ok: [%s]' % full_image, fg='green')
            containers[name] = container

        # create test inventory
        with open(os.path.join(work_dir, 'inventory'), 'w') as fd:
            fd.write(generate_inventory(containers))

        # create playbook
        with open(os.path.join(work_dir, 'test.yml'), 'w') as fd:
            playbook = yaml.dump(test['playbook']).replace('@ROLE_NAME@', role_name)
            fd.write(playbook)

        ansible_header('RUNNING TESTS')
        ansible_cmd = [
            'ansible-playbook', '-i', '/work/inventory',
            '/work/test.yml'
        ]
        stream(ansible, ansible_cmd)
    finally:
        ansible_header('CLEANING CONTAINERS')
        for name, container in containers.iteritems():
            docker.destroy(name)
            click.secho('ok: [%s]' % container.image, fg='green')


@click.command()
@click.option('--ansible-version', default='latest')
@click.argument('role')
def main(ansible_version, role):
    work_dir = tempfile.mkdtemp(prefix='ansible-test')
    docker = ContainerManager(docker_client())

    success = 0
    failed = 0
    skip = 0
    try:
        ansible_header('TESTS [%s]' % role)

        ansible, role_path, role_name = setup_ansible(docker, work_dir, ansible_version, role)

        for test in get_tests(ansible, role_path):
            run_test(docker, ansible, work_dir, role_name, test)
            success += 1

        if not success:
            click.secho('warning: no test found', fg='yellow')
    except:
        ansible_header('EXCEPTION')

        _, e, tb = sys.exc_info()
        failed += 1
        click.secho('', fg='red', reset=False)
        traceback.print_tb(tb)
        click.secho('\n  %s' % str(e), fg='red', err=True)
    finally:
        ansible_header('CLEANING TESTS')
        for name, container in docker.containers.copy().iteritems():
            docker.destroy(name)
            click.secho('ok: [%s]' % container.image, fg='green')

        # remove temp folder
        shutil.rmtree(work_dir)

        # remove any garbage container
        docker.destroy()

        ansible_header('TESTS RECAP')
        click.echo(
            '%-27s: %s    %s    %s' % (
                click.style(role, fg='yellow'),
                click.style('success=%d' % success, fg='green'),
                click.style('skip=%d' % skip, fg='blue'),
                click.style('failed=%d' % failed, fg='red'),
            )
        )

        if failed != 0:
            sys.exit(1)

        if success == 0:
            # no tests
            sys.exit(2)


if __name__ == '__main__':
    main()
