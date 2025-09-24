import sqlite3 as sql


def fix_pending_has_run(db_path="cache.db"):
    con = sql.connect(db_path)
    cur = con.cursor()
    cur.execute("UPDATE runs SET has_run = 0 WHERE has_run = -1")
    changed = cur.rowcount
    con.commit()
    con.close()
    print(f"Updated has_run from -1 to 0 for {changed} rows")


if __name__ == "__main__":
    fix_pending_has_run()


