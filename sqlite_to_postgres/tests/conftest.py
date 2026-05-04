import os

import pytest
import sqlite3
import psycopg
from dotenv import load_dotenv


@pytest.fixture
def sqlite_conn():
    conn = sqlite3.connect("sqlite_to_postgres/db.sqlite")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def pg_conn():
    load_dotenv()

    dsl = {
        "dbname": os.environ.get('DB_NAME'),
        "user": os.environ.get('DB_USER'),
        "password": os.environ.get('DB_PASSWORD'),
        "host": os.environ.get('DB_HOST', '127.0.0.1'),
        "port": os.environ.get('DB_PORT', 5432),
    }

    conn = psycopg.connect(**dsl)
    yield conn
    conn.close()