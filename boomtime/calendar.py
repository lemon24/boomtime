from collections import namedtuple


Event = namedtuple('Event', 'id title description all_day start end')


class CalendarError(Exception):

    pass


class Calendar:

    def __init__(self, db):
        self.db = db

    def add_event(self, title, start, end, description=None, all_day=False):
        if start > end:
            raise CalendarError("start cannot be later than end")
        with self.db:
            self.db.execute("""
                INSERT INTO events (title, description, all_day, start, end)
                VALUES (?, ?, ?, ?, ?);
            """, (title, description, all_day, start, end))

    def get_events(self, start, end):
        # TODO: all_day == 1 needs a different query

        rows = self.db.execute("""
            SELECT id, title, description, all_day, start, end
            FROM events
            WHERE
                start < :start and end > :end
                OR start between :start and :end
                OR end between :start and :end
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
                raise CalendarError("start cannot be later than end")
            params['start'] = start
            params['end'] = end
        elif start or end:
            raise CalendarError("both start and end must be given")
        if description is not None:
            params['description'] = description
        if all_day is not None:
            params['all_day'] = all_day

        with self.db:
            rows = self.db.execute("""
                UPDATE events
                SET {}
                WHERE id = :id
            """.format(', '.join('{0} = :{0}'.format(f) for f in params)), params)
        return rows.rowcount

