import os.path
import datetime

import click
from click import echo
import dateutil.parser
import pytz
import tzlocal

from .db import open_db


APP_NAME = 'boomtime'

def get_default_db_path():
    return os.path.join(click.get_app_dir(APP_NAME), 'db')

def abort(message, *args, **kwargs):
    raise click.ClickException(message.format(*args, **kwargs))


def local_to_utc(dt, tz=None):
    tz = tz or tzlocal.get_localzone()
    return tz.localize(dt).astimezone(pytz.utc).replace(tzinfo=None)

def utc_to_local(dt, tz=None):
    tz = tz or tzlocal.get_localzone()
    return pytz.utc.localize(dt).astimezone(tz).replace(tzinfo=None)


@click.group()
@click.option('--db', default=get_default_db_path, type=click.Path(dir_okay=False))
@click.pass_context
def cli(ctx, db):
    ctx.obj = open_db(db)


@cli.command()
@click.option('-t', '--title')
@click.option('-s', '--start', type=dateutil.parser.parse)
@click.option('-e', '--end', type=dateutil.parser.parse)
@click.option('--all-day/--no-all-day')
@click.pass_obj
def add(db, title, start, end, all_day):
    start = local_to_utc(start)
    end = local_to_utc(end)
    if start > end:
        abort("start cannot be later than end")
    with db:
        db.execute("""
            INSERT INTO events (title, description, all_day, start, end)
            VALUES (?, ?, ?, ?, ?);
        """, (title, None, all_day, start, end))


@cli.command()
@click.option('-s', '--start', type=dateutil.parser.parse)
@click.option('-e', '--end', type=dateutil.parser.parse)
@click.option('-v', '--verbose', count=True)
@click.pass_obj
def show(db, start, end, verbose):
    start = local_to_utc(start)
    end = local_to_utc(end)
    # TODO: all_day == 1 needs a different query
    rows = db.execute("""
        SELECT id, title, start, end FROM events
        WHERE
            start < :start and end > :end
            OR start between :start and :end
            OR end between :start and :end
    """, {'start': start, 'end': end})

    if verbose:
        fmt = "{id:>7} {start} {end} {title}"
    else:
        fmt = "{start} {end} {title}"

    for id, title, start, end in rows:
        start = utc_to_local(start)
        end = utc_to_local(end)
        echo(fmt.format(**locals()))


@cli.command()
@click.option('--id', required=True, type=int)
@click.pass_obj
def delete(db, id):
    with db:
        rows = db.execute("""
            DELETE FROM events
            WHERE id = :id
        """, {'id': id})
    echo("deleted {} event(s)".format(rows.rowcount))


@cli.command()
@click.option('-t', '--title')
@click.option('-s', '--start', type=dateutil.parser.parse)
@click.option('-e', '--end', type=dateutil.parser.parse)
@click.option('--all-day/--no-all-day')
@click.option('--id', required=True, type=int)
@click.pass_obj
def update(db, title, start, end, all_day, id):

    params = {'id': id, 'title': title}

    if start and end:
        if start > end:
            abort("start cannot be later than end")
        params['start'] = local_to_utc(start)
        params['end'] = local_to_utc(end)
    elif start or end:
        abort("both start and end must be given")

    if all_day is not None:
        params['all_day'] = all_day

    with db:
        rows = db.execute("""
            UPDATE events
            SET {}
            WHERE id = :id
        """.format(', '.join('{0} = :{0}'.format(f) for f in params)), params)
    echo("updated {} event(s)".format(rows.rowcount))



if __name__ == '__main__':
    cli(auto_envvar_prefix=APP_NAME.upper())
