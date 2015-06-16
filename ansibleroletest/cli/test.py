import click
import os
import six
import sys
import yaml

from ansibleroletest.container import ContainerManager
from ansibleroletest.docker import client as docker_client
from ansibleroletest.framework import TestFramework


@click.command(context_settings={'help_option_names': ['-h', '--help']})
# path options
@click.option('-c', '--config', default=None,
              help='Config file to use for the tests',
              type=click.File(mode='rb'))
@click.option('--roles-path', default=None,
              metavar='ROLES_PATH',
              help='Search path for non-galaxy roles that might be required '
                   'as dependencies')
@click.option('--library-path', default=None,
              metavar='LIBRARY_PATH',
              help='Search path for custom ansible modules',
              envvar='ANSIBLE_LIBRARY')
@click.option('--plugins-action-path', default=None,
              metavar='PLUGINS_ACTION_PATH',
              help='Search path for custom action plugins',
              envvar='ANSIBLE_ACTION_PLUGINS')
@click.option('--plugins-filter-path', default=None,
              metavar='PLUGINS_FILTER_PATH',
              help='Search path for custom filter plugins',
              envvar='ANSIBLE_FILTER_PLUGINS')
@click.option('--plugins-lookup-path', default=None,
              metavar='PLUGINS_LOOKUP_PATH',
              help='Search path for custom lookup plugins',
              envvar='ANSIBLE_LOOKUP_PLUGINS')
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
@click.option('--privileged', is_flag=True, default=False,
              help='Run test containers in privileged mode (dangerous)')
@click.option('--cache', is_flag=True,
              help='Cache yum/apt folders on the host')
@click.option('--save', default=None, type=click.Choice(['failed', 'successful', 'all']),
              help='Save containers, can be either one of "failed", '
                   '"successful" and "all"')
@click.argument('role')
def test(role,
         config,
         # path args
         roles_path, library_path, plugins_action_path,
         plugins_filter_path, plugins_lookup_path,
         # ansible-playbook args
         extra_vars, limit, skip_tags, tags, verbosity,
         # misc
         ansible_version, privileged, cache, save):
    """
    Run tests

    ROLE can be either be a local path, a git repository or an ansible-galaxy
    role name.
    """
    with ContainerManager(docker_client()) as docker:
        ansible_paths = {
            'roles': roles_path,
            'library': library_path,
            'plugins': {
                'action': plugins_action_path,
                'filter': plugins_filter_path,
                'lookup': plugins_lookup_path,
            }
        }

        _load_config(ansible_paths, config)

        framework = TestFramework(docker, role, ansible_paths,
                                  ansible_version)
        res = framework.run(
            extra_vars=extra_vars,
            limit=limit,
            skip_tags=skip_tags,
            tags=tags,
            verbosity=verbosity,
            privileged=privileged,
            cache=cache,
            save=save
        )

        if res != 0 and save != 'failed':
            click.secho('''
info: some of the tests have failed. If you wish to inspect the failed
      containers, rerun the command while adding the --save=failed flag
      to your command line.''', fg='blue')
    sys.exit(res)


def _load_config(conf, config_file=None):
    if not config_file:
        return

    base = os.path.dirname(os.path.realpath(config_file.name))
    content = yaml.load(config_file)

    # merge both objects if the original value is none
    def _update(obj_from, obj_to):
        for k, v in six.iteritems(obj_to):
            if isinstance(v, dict):
                _update(obj_from[k], v)
            elif v is None and k in obj_from and obj_from[k]:
                obj_to[k] = os.path.join(base, obj_from[k])

    _update(content, conf)
