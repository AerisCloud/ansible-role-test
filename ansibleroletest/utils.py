import appdirs
import click
import humanize
import json


def pull_image_progress():
    """
    Provides a progressbar when pulling images, kinda rough for now
    """
    ids = {}

    def _internal(progress):
        if progress == 'finished':
            click.echo('')
            return

        progress = json.loads(progress)

        if 'progressDetail' not in progress or 'status' not in progress:
            return

        if not progress['progressDetail']:
            if progress['id'] not in ids:
                ids[progress['id']] = {
                    'current': 0,
                    'total': 0
                }
        else:
            ids[progress['id']] = progress['progressDetail']

        if progress['status'] == 'Already exists':
            ids[progress['id']] = {
                'current': 100,
                'total': 100
            }

        done = sum([1 for p in ids.values()
                    if 0 < p['total'] == p['current']])
        current = sum([p['current'] for p in ids.values()])
        total = sum([p['total'] for p in ids.values()])

        if total > 0:
            pc_done = int(40.0*current/total)
        else:
            pc_done = 0

        if pc_done < 40:
            pbar = ('=' * (pc_done - 1)) + '>' + (' ' * (40 - pc_done))
        else:
            pbar = '=' * 40

        click.echo(
            '\r\033[K{0}/{1} layers [{2}] {3}/{4}'.format(
                done,
                len(ids.keys()),
                pbar,
                humanize.naturalsize(current),
                humanize.naturalsize(total)
            ),
            nl=False
        )

    return _internal

cache_dir = appdirs.user_cache_dir('ansible_role_test', 'aeriscloud')
