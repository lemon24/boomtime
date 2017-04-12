import os.path
import datetime

import click
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


if __name__ == '__main__':
    cli(auto_envvar_prefix=APP_NAME.upper())
