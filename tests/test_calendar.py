from datetime import datetime
from collections import OrderedDict

import pytest
import pytz

from boomtime.db import open_db
from boomtime.exceptions import MissingArgument, InvalidArgument
from boomtime.calendar import Calendar
from boomtime.local_calendar import LocalCalendar


factories = {
    'Calendar': Calendar,
    'LocalCalendar': lambda db: LocalCalendar(db, pytz.timezone('Europe/Brussels')),
}
factories = OrderedDict(sorted(factories.items()))

@pytest.fixture(params=list(factories.values()), ids=list(factories))
def calendar(request):
    return request.param(open_db(':memory:'))


def test_everything(calendar):
    calendar.add_event('one', datetime(2017, 4, 1), datetime(2017, 4, 2))
    calendar.add_event('two', datetime(2017, 4, 3), datetime(2017, 4, 4), all_day=True)
    calendar.add_event('three', datetime(2017, 4, 5), datetime(2017, 4, 6), description='three')
    calendar.add_event('four', datetime(2017, 4, 7), datetime(2017, 4, 8))

    events = list(calendar.get_events(datetime(2017, 4, 1), datetime(2017, 4, 8)))

    calendar.delete_event(events[0].id)
    calendar.update_event(events[3].id, start=datetime(2017, 4, 1), end=datetime(2017, 4, 2), all_day=True)

    events = list(calendar.get_events(datetime(2017, 4, 1), datetime(2017, 4, 8)))
    one, two, three = events

    assert one.title == 'four'
    assert one.start == datetime(2017, 4, 1)
    assert one.end == datetime(2017, 4, 2)
    assert one.description is None
    assert one.all_day

    assert two.title == 'two'
    assert two.start == datetime(2017, 4, 3)
    assert two.end == datetime(2017, 4, 4)
    assert two.description is None
    assert two.all_day

    assert three.title == 'three'
    assert three.start == datetime(2017, 4, 5)
    assert three.end == datetime(2017, 4, 6)
    assert three.description == 'three'
    assert not three.all_day


def make_get_titles(calendar, datetime_fmt):
    def get_titles(start, end):
        start = datetime.strptime(start, datetime_fmt)
        end = datetime.strptime(end, datetime_fmt)
        return [e.title for e in calendar.get_events(start, end)]
    return get_titles


def test_get_event_boundaries(calendar):
    get_titles = make_get_titles(calendar, '%H:%M')

    calendar.add_event('one', datetime(1900, 1, 1, 0, 10), datetime(1900, 1, 1, 0, 20))

    assert get_titles('00:10', '00:20') == ['one']
    assert get_titles('00:11', '00:19') == ['one']
    assert get_titles('00:09', '00:21') == ['one']
    assert get_titles('00:10', '00:11') == ['one']
    assert get_titles('00:19', '00:20') == ['one']
    assert get_titles('00:09', '00:11') == ['one']
    assert get_titles('00:19', '00:21') == ['one']

    assert get_titles('00:09', '00:10') == []
    assert get_titles('00:20', '00:21') == []
    assert get_titles('00:08', '00:09') == []
    assert get_titles('00:21', '00:22') == []


def test_add_event_exceptions(calendar):
    calendar.add_event('one', datetime(1900, 1, 1), datetime(1900, 1, 2, 1))
    with pytest.raises(InvalidArgument):
        calendar.add_event('two', datetime(1900, 1, 1), datetime(1900, 1, 2, 1), all_day=True)
    calendar.add_event('two', datetime(1900, 1, 1), datetime(1900, 1, 2), all_day=True)


def test_update_event_exceptions(calendar):
    calendar.add_event('one', datetime(1900, 1, 1), datetime(1900, 1, 2, 1))
    event_id = list(calendar.get_events(datetime(1900, 1, 1), datetime(1900, 1, 2)))[0].id

    with pytest.raises(MissingArgument):
        calendar.update_event(event_id, start=datetime(1900, 1, 1))
    with pytest.raises(MissingArgument):
        calendar.update_event(event_id, end=datetime(1900, 1, 2))

    with pytest.raises(MissingArgument):
        calendar.update_event(event_id, start=datetime(1900, 1, 1), end=datetime(1900, 1, 2))
    with pytest.raises(MissingArgument):
        calendar.update_event(event_id, all_day=True)

    with pytest.raises(InvalidArgument):
        calendar.update_event(event_id, start=datetime(1900, 1, 1), end=datetime(1900, 1, 2, 1), all_day=True)
    calendar.update_event(event_id, start=datetime(1900, 1, 1), end=datetime(1900, 1, 2), all_day=True)

    calendar.update_event(event_id, all_day=False)

