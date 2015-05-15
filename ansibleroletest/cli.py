from __future__ import print_function

import click
import sys

from .container import ContainerManager
from .docker import client as docker_client
from .framework import TestFramework


@click.command(context_settings={'help_option_names':['-h', '--help']})
@click.option('--roles-path', default=None,
              metavar='ROLES_PATH',
              help='search path for non-galaxy roles that might be required as dependencies')
@click.option('--library-path', default=None,
              metavar='LIBRARY_PATH',
              help='search path for custom ansible modules')
@click.option('--action-plugins-path', default=None,
              metavar='ACTION_PLUGINS_PATH',
              help='search path for custom action plugins')
@click.option('-e', '--extra-vars', multiple=True,
              metavar='EXTRA_VARS',
              help='set additional variables as key=value or YAML/JSON')
@click.option('-l', '--limit',
              metavar='SUBSET',
              help='limit selected hosts to a given pattern')
@click.option('--skip-tags', default=None,
              metavar='SKIP_TAGS',
              help='only run plays and tasks whose tags do not match these '
                   'values')
@click.option('-t', '--tags', default=None,
              metavar='TAGS',
              help='only run plays and tasks tagged with these values')
@click.option('-v', 'verbosity', count=True,
              help='verbose mode (-vvv for more, -vvvv to enable connection '
                   'debugging)')
@click.option('--ansible-version', default='latest')
@click.argument('role')
def main(role,
         # path args
         roles_path, library_path, action_plugins_path,
         # ansible-playbook args
         extra_vars, limit, skip_tags, tags, verbosity,
         # misc
         ansible_version):
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
            verbosity=verbosity
        )
    sys.exit(res)


if __name__ == '__main__':
    main()
