import sqlite3
from contextlib import contextmanager


@contextmanager
def ddl_transaction(db):
    """Automatically commit/rollback transactions containing DDL statements.

    Usage:

        with ddl_transaction(db):
            db.execute(...)
            db.execute(...)

    Note: This does not work with executescript().

    Works around https://bugs.python.org/issue10740. Normally, one would
    expect to be able to use DDL statements in a transaction like so:

        with db:
            db.execute(ddl_statement)
            db.execute(other_statement)

    However, the sqlite3 transaction handling triggers an implicit commit if
    the first execute() is a DDL statement, which will prevent it from being
    rolled back if another statement following it fails.

    https://docs.python.org/3.5/library/sqlite3.html#controlling-transactions

    """
    isolation_level = db.isolation_level
    try:
        db.isolation_level = None
        db.execute("BEGIN;")
        yield db
        db.execute("COMMIT;")
    except Exception:
        db.execute("ROLLBACK;")
        raise
    finally:
        db.isolation_level = isolation_level


VERSION = 1


class InvalidVersion(Exception):
    pass


def get_version(db):
    version_exists = db.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'version';
    """).fetchone() is not None
    if not version_exists:
        return None
    version, = db.execute("SELECT MAX(version) FROM version;").fetchone()
    return version


def create_db(db):
    with ddl_transaction(db):
        db.execute("""
            CREATE TABLE version (
                version INTEGER NOT NULL
            );
        """)
        db.execute("""
            CREATE TABLE events (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                all_day INTEGER,
                start TIMESTAMP NOT NULL,
                end TIMESTAMP NOT NULL
            );
        """)
        db.execute("INSERT INTO version VALUES (?);", (VERSION, ))


def open_db(path):
    db = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    version = get_version(db)
    if version is None:
        create_db(db)
    elif version != VERSION:
        raise InvalidVersion("invalid version: {}".format(version))
    return db


if __name__ == '__main__':

    db = open_db('db.sqlite')
    db.execute("DROP TABLE version;")
    # python3 -m boomtime.db; echo '.schema' | sqlite3 db.sqlite
