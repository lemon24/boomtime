from collections import namedtuple

from .exceptions import MissingArgument, InvalidArgument


Event = namedtuple('Event', 'id title description all_day start end')


class Calendar:

    def __init__(self, db):
        self.db = db

    def __validate_start_end(self, start, end, all_day):
        if start is None or end is None or all_day is None:
            raise MissingArgument("start, end and all_day must all be given")
        if start > end:
            raise InvalidArgument("start cannot be later than end")

        # start and end must both be at midnight for all-day events.
        # Midnight is timezone-dependent, so here we can only ensure
        # they are an exact number of days apart.
        if all_day:
            d = end - start
            if d.seconds != 0 or d.microseconds != 0:
                raise InvalidArgument("start and end must be an exact number of days apart for all-day events")

    def add_event(self, title, start, end, description=None, all_day=False):
        self.__validate_start_end(start, end, all_day)

        with self.db:
            rows = self.db.execute("""
                INSERT INTO events (title, description, all_day, start, end)
                VALUES (?, ?, ?, ?, ?);
            """, (title, description, all_day, start, end))

        return rows.lastrowid

    def get_events(self, start, end):
        """Return the events in a time interval.

        start is inclusive, end is exclusive, i.e. an event is returned iff
        [start, end) & [event start, event end) != {}.

        Events are returned in chronological order.

        """
        rows = self.db.execute("""
            SELECT id, title, description, all_day, start, end
            FROM events
            WHERE
                start < :start and end > :end OR
                start >= :start and end <= :end OR
                start >= :start and start < :end OR
                end > :start and end <= :end
            ORDER BY start, end
        """, {'start': start, 'end': end})

        for row in rows:
            yield Event(*row)

    def delete_event(self, id):
        with self.db:
            rows = self.db.execute("""
                DELETE FROM events
                WHERE id = :id
            """, {'id': id})
        return rows.rowcount

    def update_event(self, id, title=None, start=None, end=None, description=None, all_day=None):
        params = {'id': id}

        # If start or end change or if all_day becomes true we need all of
        # (start, end, all_day) so we can validate them. We make them required
        # in these cases to avoid having to have a transaction that gets
        # missing stuff from the database, does the validation, and then
        # updates the event.
        if start is not None or end is not None or all_day:
            self.__validate_start_end(start, end, all_day)
            params['start'] = start
            params['end'] = end
            params['all_day'] = all_day

        if title is not None:
            params['title'] = title
        if description is not None:
            params['description'] = description

        with self.db:
            rows = self.db.execute("""
                UPDATE events
                SET {}
                WHERE id = :id
            """.format(', '.join('{0} = :{0}'.format(f) for f in params)), params)
        return rows.rowcount

