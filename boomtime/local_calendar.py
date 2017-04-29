from .calendar import Calendar

import pytz


def local_to_utc(dt, tz):
    if not dt.tzinfo:
        return tz.localize(dt).astimezone(pytz.utc).replace(tzinfo=None)
    return dt.astimezone(pytz.utc).replace(tzinfo=None)

def utc_to_local(dt, tz):
    assert dt.tzinfo is None
    return pytz.utc.localize(dt).astimezone(tz).replace(tzinfo=None)


class LocalCalendar(Calendar):

    def __init__(self, db, tz):
        super().__init__(db)
        self.tz = tz

    def local_to_utc(self, dt):
        return local_to_utc(dt, self.tz)

    def utc_to_local(self, dt):
        return utc_to_local(dt, self.tz)

    def add_event(self, title, start, end, description=None, all_day=False):
        start = self.local_to_utc(start)
        end = self.local_to_utc(end)
        return super().add_event(title, start, end, description, all_day)

    def get_events(self, start, end):
        start = self.local_to_utc(start)
        end = self.local_to_utc(end)
        for event in super().get_events(start, end):
            event = event._replace(
                start=self.utc_to_local(event.start),
                end=self.utc_to_local(event.end))
            yield event

    def update_event(self, id, title=None, start=None, end=None, description=None, all_day=None):
        start = self.local_to_utc(start) if start else None
        end = self.local_to_utc(end) if end else None
        return super().update_event(id, title, start, end, description, all_day)

