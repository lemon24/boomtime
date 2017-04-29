import os.path
import datetime

import click
from click import echo
import dateutil.parser
import pytz
import tzlocal

from .db import open_db
from .calendar import Calendar, CalendarError


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


class LocalDatetimeParamType(click.ParamType):

    name = 'local datetime'

    def convert(self, value, param, ctx):
        try:
            dt = dateutil.parser.parse(value)
            if not dt.tzinfo:
                dt = local_to_utc(dt)
            else:
                dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
            return dt
        except ValueError:
            self.fail('%s is not a valid datetime' % value, param, ctx)


LOCAL_DATETIME = LocalDatetimeParamType()


@click.group()
@click.option('--db', default=get_default_db_path, type=click.Path(dir_okay=False))
@click.pass_context
def cli(ctx, db):
    ctx.obj = Calendar(open_db(db))


@cli.command()
@click.option('-t', '--title')
@click.option('-s', '--start', type=LOCAL_DATETIME)
@click.option('-e', '--end', type=LOCAL_DATETIME)
@click.option('--all-day/--no-all-day')
@click.pass_obj
def add(calendar, title, start, end, all_day):
    try:
        calendar.add_event(title, start, end, all_day)
    except CalendarError as e:
        abort(str(e))


@cli.command()
@click.option('-s', '--start', type=LOCAL_DATETIME)
@click.option('-e', '--end', type=LOCAL_DATETIME)
@click.option('-v', '--verbose', count=True)
@click.pass_obj
def show(calendar, start, end, verbose):
    if verbose:
        fmt = "{id:>7} {start} {end} {title}"
    else:
        fmt = "{start} {end} {title}"

    for event in calendar.get_events(start, end):
        args = {
            'id': event.id,
            'start': utc_to_local(event.start),
            'end': utc_to_local(event.end),
            'title': event.title,
        }
        echo(fmt.format(**args))


@cli.command()
@click.option('--id', required=True, type=int)
@click.pass_obj
def delete(calendar, id):
    count = calendar.delete_event(id)
    echo("deleted {} event(s)".format(count))


@cli.command()
@click.option('-t', '--title')
@click.option('-s', '--start', type=LOCAL_DATETIME)
@click.option('-e', '--end', type=LOCAL_DATETIME)
@click.option('--all-day/--no-all-day')
@click.option('--id', required=True, type=int)
@click.pass_obj
def update(calendar, title, start, end, all_day, id):
    try:
        count = calendar.update_event(id, title=title, start=start, end=end, all_day=all_day)
    except CalendarError as e:
        abort(str(e))
    echo("updated {} event(s)".format(count))



if __name__ == '__main__':
    cli(auto_envvar_prefix=APP_NAME.upper())
