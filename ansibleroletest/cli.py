from __future__ import print_function

import click
import logging
import sys

from .container import ContainerManager
from .docker import client as docker_client
from .framework import TestFramework

logging.captureWarnings(True)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
# path options
@click.option('--roles-path', default=None,
              metavar='ROLES_PATH',
              help='Search path for non-galaxy roles that might be required '
                   'as dependencies')
@click.option('--library-path', default=None,
              metavar='LIBRARY_PATH',
              help='Search path for custom ansible modules',
              envvar='ANSIBLE_LIBRARY')
@click.option('--action-plugins-path', default=None,
              metavar='ACTION_PLUGINS_PATH',
              help='Search path for custom action plugins',
              envvar='ANSIBLE_ACTION_PLUGINS')
# ansible options
@click.option('-e', '--extra-vars', multiple=True,
              metavar='EXTRA_VARS',
              help='Set additional variables as key=value or YAML/JSON')
@click.option('-l', '--limit',
              metavar='SUBSET',
              help='Limit selected hosts to a given pattern')
@click.option('--skip-tags', default=None,
              metavar='SKIP_TAGS',
              help='Only run plays and tasks whose tags do not match these '
                   'values')
@click.option('-t', '--tags', default=None,
              metavar='TAGS',
              help='Only run plays and tasks tagged with these values')
@click.option('-v', 'verbosity', count=True,
              help='Verbose mode (-vvv for more, -vvvv to enable connection '
                   'debugging)')
# extra
@click.option('--ansible-version', default='latest',
              metavar='ANSIBLE_VERSION',
              help='The ansible version to use (either 1.8, 1.9 or latest)',
              type=click.Choice(['1.8', '1.9', 'latest']))
@click.option('--privileged', is_flag=True, default=False)
@click.argument('role')
def main(role,
         # path args
         roles_path, library_path, action_plugins_path,
         # ansible-playbook args
         extra_vars, limit, skip_tags, tags, verbosity,
         # misc
         ansible_version, privileged):
    """
    ansible-role-test is a docker based testing utility for ansible roles.

    ROLE can be either be a local path, a git repository or an ansible-galaxy
    role name.
    """
    with ContainerManager(docker_client()) as docker:
        ansible_paths = {
            'roles': roles_path,
            'library': library_path,
            'plugins': {
                'action': action_plugins_path
            }
        }
        framework = TestFramework(docker, role, ansible_paths, ansible_version)
        res = framework.run(
            extra_vars=extra_vars,
            limit=limit,
            skip_tags=skip_tags,
            tags=tags,
            verbosity=verbosity,
            privileged=privileged
        )
    sys.exit(res)


if __name__ == '__main__':
    main()
