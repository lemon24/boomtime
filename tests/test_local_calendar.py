from datetime import datetime

import pytest
import pytz

from boomtime.db import open_db
from boomtime.exceptions import MissingArgument, InvalidArgument
from boomtime.local_calendar import LocalCalendar


@pytest.fixture
def calendar():
    return LocalCalendar(open_db(':memory:'), pytz.timezone('Europe/Brussels'))


def test_add_event_exceptions(calendar):
    with pytest.raises(InvalidArgument):
        calendar.add_event('one', datetime(1900, 1, 1, 1), datetime(1900, 1, 2, 1), all_day=True)


def test_update_event_exceptions(calendar):
    calendar.add_event('one', datetime(1900, 1, 1), datetime(1900, 1, 2, 1))
    event_id = list(calendar.get_events(datetime(1900, 1, 1), datetime(1900, 1, 2)))[0].id
    with pytest.raises(InvalidArgument):
        calendar.update_event(event_id, start=datetime(1900, 1, 1, 1), end=datetime(1900, 1, 2, 1), all_day=True)

