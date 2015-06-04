# ansible-role-test

`ansible-role-test` is a tool that uses docker containers to quickly create
disposable boxes that can be provisioned by a test ansible playbook via ssh.

## Requirements

* docker
* python 2.7+, 3.x

## Installation

* Clone repository
* Optional: Activate your virtualenv or run `make venv` to create a local one
* Run `make install`
* Either run `ansible-role-test` or `venv/bin/ansible-role-test`

## Development

Instead of running `make install`, run `make dev` and use `venv/bin/ansible-role-test`.

## Usage

```
Usage: ansible-role-test [OPTIONS] ROLE

  ansible-role-test is a docker based testing utility for ansible roles.

  ROLE can be either be a local path, a git repository or an ansible-galaxy
  role name.

Options:
  -c, --config FILENAME           Config file to use for the tests
  --roles-path ROLES_PATH         Search path for non-galaxy roles that might
                                  be required as dependencies
  --library-path LIBRARY_PATH     Search path for custom ansible modules
  --plugins-action-path PLUGINS_ACTION_PATH
                                  Search path for custom action plugins
  --plugins-filter-path PLUGINS_FILTER_PATH
                                  Search path for custom filter plugins
  --plugins-lookup-path PLUGINS_LOOKUP_PATH
                                  Search path for custom lookup plugins
  -e, --extra-vars EXTRA_VARS     Set additional variables as key=value or
                                  YAML/JSON
  -l, --limit SUBSET              Limit selected hosts to a given pattern
  --skip-tags SKIP_TAGS           Only run plays and tasks whose tags do not
                                  match these values
  -t, --tags TAGS                 Only run plays and tasks tagged with these
                                  values
  -v                              Verbose mode (-vvv for more, -vvvv to enable
                                  connection debugging)
  --ansible-version ANSIBLE_VERSION
                                  The ansible version to use (either 1.8, 1.9
                                  or latest)
  --privileged                    Run test containers in privileged mode
                                  (dangerous)
  --cache                         Cache yum/apt folders on the host
  --save-failed / --no-save-failed
                                  Save failed containers for inspection
  -h, --help                      Show this message and exit.
```

```bash
# Test a local role
ansible-role-test /path/to/role
# Test a git repository
ansible-role-test https://github.com/org/repo.git
# Test a branch on a git repository
ansible-role-test https://github.com/org/repo.git#my-branch
# Test an ansible-galaxy role
ansible-role-test user.role
```

## Writing tests

Create a `tests` folder in your role, then in that folder create a yaml file that
looks like that one:

```yaml
---
# The name of your test
name: "My test name"
# The containers you will use for this test, you could for example spawn a debian
# centos, ubuntu, etc... and run the tests on "all" hosts
# If skipped, tests will be run on every containers available
#containers:
#  master1: 'centos:6'
#  slave1:
#    image: 'centos:7'
#    vars:
#      host_var1: foobar # defines host_var1 on this host on particular
#  slave2: 'centos:7'
#  slave3: 'debian:wheezy'
# You can also setup custom inventory groups to be declared in the inventory, if
# no containers are declared above, they will be merged with the default groups.
# For exemple the following declaration will create 2 groups, master and slaves.
#groups:
#  masters:
#  - master1
#  slaves:
#  - slave1
#  - slave2
#  - slave3
# This is your test playbook
playbook:
- hosts: all
# You should have your role called in roles, with the proper variables set, you
# can call the same role several times in a row but I'd rather recommend creating
# separate test files for each call to ensure that they run in a clean env
  roles:
# "@ROLE_NAME@" is a magic variable that will be replaced by the name of the role
# on your filesystem before running the tests
  - role: "@ROLE_NAME@"
    var1: something
    var2: something
  tasks:
# You should verify that your role executed properly here, using tasks
  tasks:
  - name: "Check that my-role did that thing properly"
    module: do-something
```

## On test failed

On test failure, it is possible to commit the current state of the container to
`failed/{HOSTNAME}:{STAMP}` which can then be manually inspected to determine
what could be wrong. To enable this feature, one just needs to pass the
`--save-failed` option to the command line.

Saved images can be found by running `docker images` and finding containers
whose repository start with `failed/`. Once found, one can inspect the container
by running:

```bash
$ docker run -t -i failed/container-name:tag bash
[root@671165bdfcb0 /]#
```

Once done, one can removed failed containers by running `docker rmi failed/foo:tag`.
An fast way to remove all failed containers is to run:

```bash
# find all the images in the failed/ repository and remove them
$ docker images | grep '^failed/' | awk '{ print $1":"$2 }' | xargs -r docker rmi
Untagged: failed/debian-wheezy:1433320037
Deleted: 5a6b24509052d9c1a8dc7c046797b11f25c58d74179827d17269f016bf1a20ee
Untagged: failed/debian-jessie:1433320031
Deleted: 7d4557d199bd75b17f47d6e2c1f5d207bbb98bf4600b52b4786c71c645cf266e
...
```

## Paths and config file

Most of the time, your roles might depend on other local roles or plugins, in
which case you can use the `--role-path`, `--library-path`, etc... flags to help
ansible find those. In some cases though it might result in unwieldy commands
due to the sheer amount of flags passed around. When that happens you can use a
config file that follows this format to provide the proper information to ansible:

```yaml
---
roles: ansible/roles
library: ansible/library
plugins:
  action: ansible/plugins/actions
  filter: ansible/plugins/filters
```

Then call `ansible-role-test` with the `--config` flag pointing to this file.
The given paths are relative to the config file's location.

## Available test containers

You can find them on the wizcorp user on the docker registry, they should be
named `ansible-<distro>:<version>`.

`image name`    | `name in playbook`
----------------|-------------------
centos:6        | centos-6
centos:7        | centos-7
debian:wheezy   | debian-wheezy
debian:jessie   | debian-jessie
ubuntu:14.04    | ubuntu-lts
ubuntu:15.04    | ubuntu-15

They are also automatically separated in 3 groups `centos`, `debian` and `ubuntu`.

Please check [`aeriscloud@docker`](https://registry.hub.docker.com/repos/aeriscloud/)
for the current list of available images.

If you wish to build all the images locally, you can run `make docker`.

## Known issues/caveats

* Any role that deals with kernel modules or raw hardware (eg. `iptables` or
  formatting disks) will run into issues while running in docker.
  `iptables` seems to work in privileged mode with no side effects but
  anything that does destructive operations should not be tested with
  privileged mode on.
* While the centos boxes are running `systemd-container`, debian and ubuntu
  boxes are not and as such calls to systemctl/initd might not behave the
  same way as a real system.


## Disclaimer

This is currently a work in progress, I am not responsible and shall not
be held responsible in any manner if this tool causes loss of data, hardware
faults, act of gods, invocation of old or ancient ones, elder gods and other
horrors from the depths.
