import sqlite3 as sql


def backfill_from_existing(db_path: str = 'cache.db'):
    """Populate derived elevation fields using only existing DB values.
    - Ensures columns exist
    - Computes elev_gain_per_mile for rows that already have elev_gain_ft and distance
    - Does NOT call external APIs
    """
    con = sql.connect(db_path)
    cur = con.cursor()

    # Ensure columns exist
    cur.execute("PRAGMA table_info(runs)")
    cols = [row[1] for row in cur.fetchall()]
    if 'elev_gain_ft' not in cols:
        cur.execute("ALTER TABLE runs ADD COLUMN elev_gain_ft REAL")
    if 'elev_gain_per_mile' not in cols:
        cur.execute("ALTER TABLE runs ADD COLUMN elev_gain_per_mile REAL")
    con.commit()

    # Compute per-mile elevation where possible
    cur.execute(
        """
        SELECT date, distance, elev_gain_ft
        FROM runs
        WHERE has_run = 1 AND elev_gain_ft IS NOT NULL
        """
    )
    rows = cur.fetchall()
    updated = 0
    for date_str, distance, elev_gain_ft in rows:
        elev_per_mile = None
        try:
            if elev_gain_ft is not None and distance not in (None, 0):
                elev_per_mile = float(elev_gain_ft) / float(distance)
        except Exception:
            elev_per_mile = None
        cur.execute(
            "UPDATE runs SET elev_gain_per_mile = ? WHERE date = ?",
            (elev_per_mile, date_str),
        )
        updated += 1

    con.commit()
    con.close()
    print(f"Updated {updated} row(s) with elev_gain_per_mile based on existing elev_gain_ft and distance.")


if __name__ == '__main__':
    backfill_from_existing()

