import click
import os
import yaml

DEFAULT_CONTAINERS = {
    'centos6': 'centos:6',
    'centos7': 'centos:7',
    'debian-wheezy': 'debian:wheezy',
    'debian-jessie': 'debian:jessie',
    'ubuntu-lts': 'ubuntu:lts',
    'ubuntu15': 'ubuntu:15.04'
}


class Test(object):
    _counter = 0

    def __init__(self, framework, test):
        self.framework = framework
        self.docker = self.framework.docker.new()
        self.role_name = self.framework.role_name
        self.test = test
        Test._counter += 1
        self.id = Test._counter

        self.inventory_file = 'inventory_%d' % self.id
        self.playbook_file = 'test_%d.yml' % self.id

    @property
    def inventory(self):
        inventory = '[test]\n'
        for name, container in self.docker.containers.iteritems():
            inventory += '{0} ansible_ssh_host={1} ansible_ssh_user=ansible ' \
                         'ansible_ssh_pass=ansible\n' \
                .format(name, container.internal_ip)
        return inventory

    @property
    def name(self):
        if 'name' in self.test:
            return self.test['name']
        return 'Test #%d' % self.id

    def cleanup(self):
        self.framework.print_header('CLEANING TEST CONTAINERS')
        for name, container in self.docker.containers.copy().iteritems():
            self.docker.destroy(name)
            click.secho('ok: [%s]' % container.image, fg='green')

    def run(self, extra_vars=None, limit=None, skip_tags=None,
            tags=None, verbosity=None, privileged=False):
        try:
            self.framework.print_header('TEST [%s]' % self.name)
            self.setup(limit, privileged)

            self.framework.print_header('RUNNING TESTS')

            ansible_cmd = [
                'ansible-playbook',
                '-i', os.path.join('/work', self.inventory_file)
            ]

            if extra_vars:
                for extra_var in extra_vars:
                    ansible_cmd += ['--extra-vars', extra_var]

            if limit:
                ansible_cmd += ['--limit', limit]

            if skip_tags:
                ansible_cmd += ['--skip-tags', skip_tags]

            if tags:
                ansible_cmd += ['--tags', tags]

            if verbosity:
                ansible_cmd.append('-%s' % ('v' * verbosity))

            ansible_cmd.append(os.path.join('/work', self.playbook_file))

            self.framework.stream(*ansible_cmd)
        finally:
            self.cleanup()

    def setup(self, limit=None, privileged=False):
        self.setup_playbook()
        self.start_containers(limit, privileged)
        self.setup_inventory()

    def setup_playbook(self):
        if 'playbook' not in self.test:
            raise NameError('Missing key "playbook" in test file')

        with open(os.path.join(self.framework.work_dir, self.playbook_file), 'w') as fd:
            playbook = yaml.dump(self.test['playbook'])\
                .replace('@ROLE_NAME@', self.role_name)
            fd.write(playbook)

    def setup_inventory(self):
        with open(os.path.join(self.framework.work_dir, self.inventory_file), 'w') as fd:
            fd.write(self.inventory)

    def start_containers(self, limit=None, privileged=False):
        self.framework.print_header('STARTING CONTAINERS')

        if 'containers' not in self.test:
            self.test['containers'] = DEFAULT_CONTAINERS

        # do not start containers that do not match the given limit
        if limit and limit != 'all':
            unwanted = set(self.test['containers']) - set(limit.split(','))
            for unwanted_container in unwanted:
                del self.test['containers'][unwanted_container]

        for name, image in self.test['containers'].iteritems():
            full_image = 'aeriscloud/ansible-%s' % image
            self.docker.create(name, image=full_image).start(privileged=privileged)
            click.secho('ok: [%s]' % full_image, fg='green')