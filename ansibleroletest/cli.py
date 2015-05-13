from __future__ import print_function

import click
import sys

from .container import ContainerManager
from .docker import client as docker_client
from .framework import TestFramework


@click.command()
@click.option('--ansible-version', default='latest')
@click.option('--roles-path', default=None)
@click.argument('role')
def main(ansible_version, roles_path, role):
    with ContainerManager(docker_client()) as docker:
        framework = TestFramework(docker, role, roles_path, ansible_version)
        res = framework.run()
    sys.exit(res)


if __name__ == '__main__':
    main()
