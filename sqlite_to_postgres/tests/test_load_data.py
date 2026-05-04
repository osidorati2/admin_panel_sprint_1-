def test_counts(sqlite_conn, pg_conn):
    sqlite_count = sqlite_conn.execute("SELECT COUNT(*) FROM film_work").fetchone()[0]

    with pg_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM content.film_work")
        pg_count = cur.fetchone()[0]

    assert sqlite_count == pg_count


def test_sample_row(sqlite_conn, pg_conn):
    sqlite_row = sqlite_conn.execute(
        "SELECT id, title FROM film_work LIMIT 1"
    ).fetchone()

    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT id, title FROM content.film_work WHERE id = %s",
            (sqlite_row["id"],),
        )
        pg_row = cur.fetchone()

    assert sqlite_row["title"] == pg_row[1]


def test_relations(pg_conn):
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM content.person_film_work pfw
            JOIN content.person p ON p.id = pfw.person_id
        """)
        count = cur.fetchone()[0]

    assert count > 0