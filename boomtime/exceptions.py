

class CalendarError(Exception):

    pass


class MissingArgument(CalendarError, TypeError):

    pass


class InvalidArgument(CalendarError, ValueError):

    pass

