import sqlite3

con = sqlite3.connect('cache.db')
cur = con.cursor()

print("November 2025 runs:")
cur.execute("SELECT date, distance, elev_gain FROM runs WHERE date LIKE '2025-11-%' AND distance > 0 ORDER BY date DESC")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} mi, {row[2]} ft")

print("\nSeptember 2025 runs:")
cur.execute("SELECT date, distance, elev_gain FROM runs WHERE date LIKE '2025-09-%' AND distance > 0 ORDER BY date DESC")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} mi, {row[2]} ft")

print("\nAll runs in database:")
cur.execute("SELECT date, distance, elev_gain FROM runs WHERE distance > 0 ORDER BY date DESC LIMIT 20")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} mi, {row[2]} ft")

con.close()
