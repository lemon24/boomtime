import os.path
import datetime

import click
from click import echo
import dateutil.parser
import tzlocal

from .db import open_db
from .calendar import CalendarError
from .local_calendar import LocalCalendar


APP_NAME = 'boomtime'

def get_default_db_path():
    return os.path.join(click.get_app_dir(APP_NAME), 'db')

def abort(message, *args, **kwargs):
    raise click.ClickException(message.format(*args, **kwargs))


class DatetimeParamType(click.ParamType):

    name = 'datetime'

    def convert(self, value, param, ctx):
        try:
            return dateutil.parser.parse(value)
        except ValueError:
            self.fail('%s is not a valid datetime' % value, param, ctx)

DATETIME = DatetimeParamType()


@click.group()
@click.option('--db', default=get_default_db_path, type=click.Path(dir_okay=False))
@click.pass_context
def cli(ctx, db):
    ctx.obj = LocalCalendar(open_db(db), tzlocal.get_localzone())


@cli.command()
@click.option('-t', '--title')
@click.option('-s', '--start', type=DATETIME)
@click.option('-e', '--end', type=DATETIME)
@click.option('--all-day/--no-all-day')
@click.pass_obj
def add(calendar, title, start, end, all_day):
    try:
        calendar.add_event(title, start, end, all_day=all_day)
    except CalendarError as e:
        abort(str(e))


@cli.command()
@click.option('-s', '--start', type=DATETIME)
@click.option('-e', '--end', type=DATETIME)
@click.option('-v', '--verbose', count=True)
@click.pass_obj
def show(calendar, start, end, verbose):
    if verbose:
        fmt = "{id:>7} {start} {end} {title}"
    else:
        fmt = "{start} {end} {title}"
    for event in calendar.get_events(start, end):
        echo(fmt.format(**event._asdict()))


@cli.command()
@click.option('--id', required=True, type=int)
@click.pass_obj
def delete(calendar, id):
    count = calendar.delete_event(id)
    echo("deleted {} event(s)".format(count))


@cli.command()
@click.option('-t', '--title')
@click.option('-s', '--start', type=DATETIME)
@click.option('-e', '--end', type=DATETIME)
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
