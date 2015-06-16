from __future__ import absolute_import

from docker.client import Client
from docker.utils import kwargs_from_env


# Taken from the docker-compose source
def client():
    """
    Returns a docker-py client configured using environment variables
    according to the same logic as the official Docker client.
    """
    kwargs = kwargs_from_env()
    if 'tls' in kwargs:
        kwargs['tls'].assert_hostname = False
    return Client(version='auto', **kwargs)
