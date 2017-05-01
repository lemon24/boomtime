from datetime import datetime

import pytest
import pytz

from boomtime.db import open_db
from boomtime.calendar import Calendar
from boomtime.local_calendar import LocalCalendar


@pytest.mark.parametrize('make_calendar', [
    Calendar,
    lambda db: LocalCalendar(db, pytz.timezone('Europe/Brussels')),
])
def test_everything(make_calendar):
    calendar = make_calendar(open_db(':memory:'))

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

