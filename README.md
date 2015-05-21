# ansible-role-test

`ansible-role-test` is a tool that uses docker containers to quickly create
disposable boxes that can be provisioned by a test ansible playbook via ssh.

## Requirements

* docker
* python 2.7 or 3.x

## Installation

* Clone repository
* Run `make dist`
* Either run `venv/bin/ansible-role-test` or `dist/ansible-role-test-<OS>-<arch>`

## Usage

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
containers:
  centos6: 'centos:6'
  centos7: 'centos:7'
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

## Available test containers

You can find them on the wizcorp user on the docker registry, they should be
named `ansible-<distro>:<version>`.

* `centos:6`
* `centos:7`
* `debian:wheezy`
* `debian:jessie`
* `ubuntu:14.04`
* `ubuntu:15.04`

Please check [`aeriscloud@docker`](https://registry.hub.docker.com/repos/aeriscloud/) for
the current list of available images.

If you wish to build all the images locally, you can run `make docker`.
