from __future__ import absolute_import

from setuptools import setup, find_packages
from ansibleroletest import __version__, __author__, __email__, __license__, __url__

install_requires = [
    'appdirs >= 1.4.0, < 2',
    'click == 4.0',
    'docker-py >= 1.2.0, < 1.3',
    'giturlparse.py == 0.0.5',
    'PyYAML >= 3.10, < 4',
    'six >= 1.9.0, < 2',
    # fix urllib warning on OSX
    'pyopenssl',
    'ndg-httpsclient',
    'pyasn1'
]

setup(
    name='ansible-role-test',
    version=__version__,
    description='Test ansible-galaxy roles using docker',
    url=__url__,
    author=__author__,
    author_email=__email__,
    license=__license__,
    packages=find_packages(exclude=['tests.*', 'tests']),
    install_requires=install_requires,
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Installation/Setup',
    ],
    entry_points={
        'console_scripts': [
            'ansible-role-test = ansibleroletest.cli:main'
        ]
    }
)
