import click
import datetime
import json
import sys

from docker.errors import APIError

from ansibleroletest.docker import client as docker_client
from ansibleroletest.framework import TestFramework


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def snapshots():
    """
    Manipulate saved containers
    """
    pass


@snapshots.command(name='list', context_settings={'help_option_names': ['-h', '--help']})
@click.option('-f', '--filter', help='Filter by role name')
def snapshots_list(filter):
    """
    List all snapshots and whether they failed or succeeded
    """
    docker = docker_client()

    output_fmt = '{role_name:<24s}{container:<20s}{status:<16s}{date:<24s}{image_name}'
    click.echo(output_fmt.format(
        role_name='ROLE NAME',
        container='CONTAINER',
        status='STATUS',
        date='DATE',
        image_name='IMAGE NAME'
    ))
    for image in docker.images():
        snapshots = [
            repotag[4:]
            for repotag in image.get('RepoTags', [])
            if repotag.startswith('art/')
        ]

        if not snapshots:
            continue

        for snapshot in snapshots:
            repo, tag = snapshot.split(':')
            role_name = repo.split('.')
            container = role_name.pop()
            role_name = '.'.join(role_name)
            state, date = tag.split('-')

            if filter and role_name != filter:
                continue

            click.echo(output_fmt.format(
                role_name=role_name,
                container=container,
                status=state,
                date=datetime.datetime.fromtimestamp(int(date)).isoformat(),
                image_name=snapshot
            ))


@snapshots.command(name='purge', context_settings={'help_option_names': ['-h', '--help']})
def snapshots_purge():
    """
    Delete all snapshots
    """
    click.confirm('This will delete all snapshots from the local registry', abort=True)

    docker = docker_client()

    for image in docker.images():
        snapshots = [
            repotag
            for repotag in image.get('RepoTags', [])
            if repotag.startswith('art/')
        ]

        if not snapshots:
            continue

        for snapshot in snapshots:
            click.echo('Deleting %s ... ' % snapshot, nl=False)
            try:
                docker.remove_image(snapshot)
                click.secho('DONE', fg='green')
            except APIError as e:
                click.secho('FAILED [%s]' % e.explanation.decode('utf-8'), fg='red')


@snapshots.command(name='rm', context_settings={'help_option_names': ['-h', '--help']})
@click.argument('image', default=None, required=False)
def snapshots_rm(image):
    """
    Remove a specific snapshot
    """
    docker = docker_client()

    image, image_name = _resolve_image(docker, image)

    if not image and not image_name:
        click.secho('error: no image to delete', err=True, fg='red')
        sys.exit(1)

    click.echo('Deleting %s ... ' % image_name, nl=False)
    try:
        docker.remove_image(image_name)
        click.secho('DONE', fg='green')
    except APIError as e:
        click.secho('FAILED [%s]' % e.explanation.decode('utf-8'), fg='red')


@snapshots.command(name='view', context_settings={'help_option_names': ['-h', '--help']})
@click.argument('image', default=None, required=False)
def snapshots_view(image):
    """
    Display the output of the ansible play that was run on this snapshot
    """
    docker = docker_client()

    image, image_name = _resolve_image(docker, image)

    try:
        res = docker.inspect_image(image=image_name)
    except APIError as e:
        click.secho('error: %s' % e.explanation.decode('utf-8'), fg='red', err=True)
        sys.exit(1)

    try:
        play = json.loads(res.get('Comment'))
    except ValueError as e:
        click.secho('error: %s' % str(e), fg='red')
        sys.exit(1)

    repo, tag = image_name.split(':')
    repo = repo.split('.')
    host = repo.pop()

    TestFramework.print_header('PLAY [%s]' % host)

    for task in play['tasks']:
        TestFramework.print_header('TASK: [%s]' % task['name'])
        if task['state'] == 'ok':
            if 'changed' in task['res'] and task['res']['changed'] is True:
                click.secho('changed: [%s]' % host, fg='yellow')
            else:
                click.secho('ok: [%s]' % host, fg='green')
        elif task['state'] == 'skipped':
            click.secho('skipped: [%s]' % host, fg='cyan')
        elif task['state'] == 'failed':
            click.secho('failed: [%s]\n%s' % (host, task['res']), fg='red')

    TestFramework.print_header('PLAY RECAP [%s]' % image_name)

    click.secho('{host:<27s}: {ok} {changed} {unreachable} {failed}\n'.format(
        host=click.style(host, fg='yellow'),
        ok=click.style('ok=%-4d' % play['stats']['ok'], fg='green'),
        changed=click.style('changed=%-4d' % play['stats']['changed'], fg='yellow'),
        unreachable='unreachable=%-4d' % play['stats']['unreachable'],
        failed=click.style('failed=%-4d' % play['stats']['failed'], fg='red'),
    ))


def _resolve_image(docker, image):
    """
    If no image is provided, list them and ask the user to choose,
    otherwise check that the repo name is in it
    :param docker:
    :param image:
    :return:
    """
    if not image:
        snapshots = []
        for image in docker.images():
            snapshots += [
                repotag[4:]
                for repotag in image.get('RepoTags', [])
                if repotag.startswith('art/')
            ]

        if not snapshots:
            return None, None

        if len(snapshots) > 1:
            for idx in range(0, len(snapshots)):
                print('%d: %s' % (idx + 1, snapshots[idx]))

            try:
                idx = int(click.prompt('\nPlease enter the id of the snapshot you want to inspect'))
                image = snapshots[idx - 1]
            except BaseException:
                click.secho('\nerror: invalid id entered, exiting')
                sys.exit(1)
        else:
            image = snapshots[0]

    image_name = image
    if not image.startswith('art/'):
        image_name = 'art/' + image

    return image, image_name
