import os
import csv
import io
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
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
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def load_table(self, table_name: str, batch_size: int = BATCH_SIZE) -> Generator[List[sqlite3.Row], None, None]:
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            yield rows


# ---------- POSTGRES SAVER ---------- #

class PostgresSaver:
    def __init__(self, conn: _connection):
        self.conn = conn

    def copy(self, table: str, columns: list[str], buffer: io.StringIO):
        try:
            with self.conn.cursor() as cur:
                with cur.copy(
                    f"COPY content.{table} ({', '.join(columns)}) FROM STDIN WITH CSV"
                ) as copy:
                    copy.write(buffer.getvalue())

            self.conn.commit()
            logging.info(f"{table}: loaded {buffer.getvalue().count(chr(10))} rows")

        except Exception:
            logging.exception(f"Error loading table {table}")
            self.conn.rollback()
            raise

    def build_buffer(self, rows, columns, transform):
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        for row in rows:
            row_dict = transform(dict(row))
            writer.writerow([row_dict.get(col) for col in columns])

        buffer.seek(0)
        return buffer

    # ---------- TRANSFORMS ---------- #

    def base_transform(self, row: dict):
        row["id"] = to_uuid(row["id"])

        if "created_at" in row:
            row["created"] = row.pop("created_at")

        if "updated_at" in row:
            row["modified"] = row.pop("updated_at")

        return row

    def transform_genre(self, row):
        return self.base_transform(row)

    def transform_person(self, row):
        return self.base_transform(row)

    def transform_film_work(self, row):
        row = self.base_transform(row)

        # гарантируем NOT NULL
        row["certificate"] = row.get("certificate") or ""

        return row

    def transform_genre_film_work(self, row):
        row["id"] = to_uuid(row["id"])
        row["genre_id"] = to_uuid(row["genre_id"])
        row["film_work_id"] = to_uuid(row["film_work_id"])

        if "created_at" in row:
            row["created"] = row.pop("created_at")

        return row

    def transform_person_film_work(self, row):
        row["id"] = to_uuid(row["id"])
        row["person_id"] = to_uuid(row["person_id"])
        row["film_work_id"] = to_uuid(row["film_work_id"])

        if "created_at" in row:
            row["created"] = row.pop("created_at")

        return row


# ---------- MAIN PIPELINE ---------- #

def load_from_sqlite(sqlite_conn: sqlite3.Connection, pg_conn: _connection):
    loader = SQLiteLoader(sqlite_conn)
    saver = PostgresSaver(pg_conn)

    try:
        # ---------- GENRE ---------- #
        for batch in loader.load_table("genre"):
            buffer = saver.build_buffer(
                batch,
                ["id", "name", "description", "created", "modified"],
                saver.transform_genre,
            )
            saver.copy("genre", ["id", "name", "description", "created", "modified"], buffer)

        # ---------- PERSON ---------- #
        for batch in loader.load_table("person"):
            buffer = saver.build_buffer(
                batch,
                ["id", "full_name", "created", "modified"],
                saver.transform_person,
            )
            saver.copy("person", ["id", "full_name", "created", "modified"], buffer)

        # ---------- FILM WORK ---------- #
        for batch in loader.load_table("film_work"):
            buffer = saver.build_buffer(
                batch,
                [
                    "id", "title", "description", "creation_date", "rating",
                    "type", "created", "modified", "file_path", "certificate"
                ],
                saver.transform_film_work,
            )
            saver.copy(
                "film_work",
                [
                    "id", "title", "description", "creation_date", "rating",
                    "type", "created", "modified", "file_path", "certificate"
                ],
                buffer,
            )

        # ---------- GENRE FILM WORK ---------- #
        for batch in loader.load_table("genre_film_work"):
            buffer = saver.build_buffer(
                batch,
                ["id", "genre_id", "film_work_id", "created"],
                saver.transform_genre_film_work,
            )
            saver.copy("genre_film_work", ["id", "genre_id", "film_work_id", "created"], buffer)

        # ---------- PERSON FILM WORK ---------- #
        for batch in loader.load_table("person_film_work"):
            buffer = saver.build_buffer(
                batch,
                ["id", "person_id", "film_work_id", "role", "created"],
                saver.transform_person_film_work,
            )
            saver.copy(
                "person_film_work",
                ["id", "person_id", "film_work_id", "role", "created"],
                buffer,
            )

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