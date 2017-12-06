from collections import namedtuple

from .exceptions import MissingArgument, InvalidArgument


Event = namedtuple('Event', 'id title description all_day start end')


class Calendar:

    def __init__(self, db):
        self.db = db

    def add_event(self, title, start, end, description=None, all_day=False):
        if start > end:
            raise InvalidArgument("start cannot be later than end")

        # start and end must both be at midnight for all-day events.
        # Midnight is timezone-dependent, so we can only ensure that
        # they're an exact number of days apart.
        if all_day:
            d = end - start
            if d.seconds != 0 or d.microseconds != 0:
                raise InvalidArgument("start and end must be an exact number of days apart for all-day events")

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

        if title is not None:
            params['title'] = title

        if start and end:
            if start > end:
                raise InvalidArgument("start cannot be later than end")
            params['start'] = start
            params['end'] = end
            if all_day is None:
                raise MissingArgument("all_day must be given when updating start/end")
        elif start or end:
            raise MissingArgument("both start and end must be given")

        if description is not None:
            params['description'] = description

        if all_day is not None:

            # start and end must both be at midnight for all-day events.
            # Midnight is timezone-dependent, so we can only ensure that
            # they're an exact number of days apart.
            if all_day:

                # If start and end are not given, we need to get them from the
                # database, do the check, and then update the event, all in
                # a single transaction. This would complicate the code, so we
                # just make them required for now.
                if not (start and end):
                    raise MissingArgument("start and end must be given when enabling all_day")

                d = end - start
                if d.seconds != 0 or d.microseconds != 0:
                    raise InvalidArgument("start and end must be an exact number of days apart for all-day events")

            params['all_day'] = all_day

        with self.db:
            rows = self.db.execute("""
                UPDATE events
                SET {}
                WHERE id = :id
            """.format(', '.join('{0} = :{0}'.format(f) for f in params)), params)
        return rows.rowcount

