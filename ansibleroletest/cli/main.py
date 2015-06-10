from __future__ import print_function

import click
import logging

from .init import init
from .snapshots import snapshots
from .test import test

logging.captureWarnings(True)


@click.group()
def cli():
    """
    ansible-role-test is a docker based testing utility for ansible roles.
    """
    pass

cli.add_command(init)
cli.add_command(snapshots)
cli.add_command(test)

if __name__ == '__main__':
    cli()
