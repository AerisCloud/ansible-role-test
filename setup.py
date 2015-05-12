from __future__ import absolute_import

from setuptools import setup, find_packages
from ansibleroletest import __version__, __author__, __email__, __license__

install_requires = [
    'click == 4.0',
    'docker-py >= 1.2.0, < 1.3',
    'giturlparse.py == 0.0.5',
    'PyYAML >= 3.10, < 4'
]

dev_requires = [
    'git+https://github.com/pyinstaller/pyinstaller.git#egg=pyinstaller'
]

setup(
    name='ansible-role-test',
    version=__version__,
    description='Test ansible-galaxy roles using docker',
    author=__author__,
    author_email=__email__,
    license=__license__,
    packages=find_packages(exclude=['tests.*', 'tests']),
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'ansible-role-test = ansibleroletest.cli:main'
        ]
    }
)
