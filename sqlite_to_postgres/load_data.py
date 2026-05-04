import os
import csv
import io
import logging
import sqlite3
from typing import Generator, List
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from psycopg import connection as _connection


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

BATCH_SIZE = 1000


# ---------- HELPERS ---------- #

def to_uuid(value):
    if isinstance(value, UUID):
        return value
    return UUID(value)


def truncate_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE content.person_film_work,
                           content.genre_film_work,
                           content.film_work,
                           content.person,
                           content.genre
            CASCADE;
        """)
    conn.commit()


# ---------- SQLITE LOADER ---------- #

class SQLiteLoader:
    def __init__(self, conn):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def load(self, table: str, batch_size: int = BATCH_SIZE):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")

        batch_num = 0

        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break

            batch_num += 1
            logging.info(f"{table}: loaded batch {batch_num} ({len(batch)} rows)")

            yield batch


GENRE_UPSERT = """
INSERT INTO content.genre (id, name, description, created, modified)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
name = EXCLUDED.name,
description = EXCLUDED.description,
modified = EXCLUDED.modified;
"""

PERSON_UPSERT = """
INSERT INTO content.person (id, full_name, created, modified)
VALUES (%s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
full_name = EXCLUDED.full_name,
modified = EXCLUDED.modified;
"""

FILMWORK_UPSERT = """
INSERT INTO content.film_work (
    id, title, description, creation_date,
    rating, type, created, modified,
    file_path, certificate
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT (id) DO UPDATE SET
title = EXCLUDED.title,
description = EXCLUDED.description,
creation_date = EXCLUDED.creation_date,
rating = EXCLUDED.rating,
type = EXCLUDED.type,
modified = EXCLUDED.modified,
file_path = EXCLUDED.file_path,
certificate = EXCLUDED.certificate;
"""

GENRE_FILM_UPSERT = """
INSERT INTO content.genre_film_work (id, genre_id, film_work_id, created)
VALUES (%s,%s,%s,%s)
ON CONFLICT (id) DO NOTHING;
"""

PERSON_FILM_UPSERT = """
INSERT INTO content.person_film_work (id, person_id, film_work_id, role, created)
VALUES (%s,%s,%s,%s,%s)
ON CONFLICT (id) DO NOTHING;
"""

def transform_base(row: dict):
    row["id"] = to_uuid(row["id"])

    if "created_at" in row:
        row["created"] = row.pop("created_at")

    if "updated_at" in row:
        row["modified"] = row.pop("updated_at")

    return row

# ---------- POSTGRES SAVER ---------- #

class PostgresSaver:
    def __init__(self, conn):
        self.conn = conn

    def execute_batch(self, query: str, data: list[tuple], table_name: str):
        try:
            with self.conn.cursor() as cur:
                cur.executemany(query, data)

            self.conn.commit()

            logging.info(f"{table_name}: inserted {len(data)} rows")

        except Exception:
            logging.exception(f"{table_name}: failed batch insert")
            self.conn.rollback()
            raise


# ---------- MAIN PIPELINE ---------- #
def load_from_sqlite(sqlite_conn, pg_conn):
    loader = SQLiteLoader(sqlite_conn)
    saver = PostgresSaver(pg_conn)

    logging.info("Migration started")

    try:
        # ---------- GENRE ---------- #
        logging.info("Starting genre migration")

        for batch in loader.load("genre"):
            data = [
                (r["id"], r["name"], r["description"], r["created"], r["modified"])
                for r in (transform_base(dict(x)) for x in batch)
            ]
            saver.execute_batch(GENRE_UPSERT, data, "genre")

        logging.info("Genre migration finished")

        # ---------- PERSON ---------- #
        logging.info("Starting person migration")

        for batch in loader.load("person"):
            data = [
                (r["id"], r["full_name"], r["created"], r["modified"])
                for r in (transform_base(dict(x)) for x in batch)
            ]
            saver.execute_batch(PERSON_UPSERT, data, "person")

        logging.info("Person migration finished")

        # ---------- FILM WORK ---------- #
        logging.info("Starting film_work migration")

        for batch in loader.load("film_work"):
            data = []
            for raw in batch:
                r = transform_base(dict(raw))

                data.append((
                    r["id"],
                    r["title"],
                    r.get("description"),
                    r.get("creation_date"),
                    r.get("rating"),
                    r["type"],
                    r["created"],
                    r["modified"],
                    r.get("file_path"),
                    r.get("certificate") or "",
                ))

            saver.execute_batch(FILMWORK_UPSERT, data, "film_work")

        logging.info("Film_work migration finished")

        logging.info("Migration completed successfully")

    except Exception:
        logging.exception("Migration failed")
        pg_conn.rollback()
        raise


# ---------- ENTRY POINT ---------- #

if __name__ == "__main__":
    load_dotenv()

    dsl = {
        "dbname": os.environ.get('DB_NAME'),
        "user": os.environ.get('DB_USER'),
        "password": os.environ.get('DB_PASSWORD'),
        "host": os.environ.get('DB_HOST', '127.0.0.1'),
        "port": os.environ.get('DB_PORT', 5432),
    }

    with sqlite3.connect("db.sqlite") as sqlite_conn, psycopg.connect(**dsl) as pg_conn:
        truncate_tables(pg_conn)
        load_from_sqlite(sqlite_conn, pg_conn)