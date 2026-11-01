import psycopg
from psycopg.rows import dict_row
from . import settings as s


def connect():
    return psycopg.connect(s.DB_URL, row_factory=dict_row)


def migrate():
    with connect() as c:
        c.execute((s.PROJECT / "backend/migrations/001_initial.sql").read_text())


def one(sql, args=()):
    with connect() as c:
        return c.execute(sql, args).fetchone()


def all_rows(sql, args=()):
    with connect() as c:
        return c.execute(sql, args).fetchall()
