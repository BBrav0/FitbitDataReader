import sqlite3 as sql

def check_database_state():
    """Check the current state of the cache.db database"""
    con = sql.connect("cache.db")
    cur = con.cursor()
    
    # Check table structure
    cur.execute("PRAGMA table_info(runs)")
    columns = cur.fetchall()
    print("Table structure:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    print("\nActivity type distribution:")
    cur.execute("SELECT activity_type, COUNT(*) FROM runs GROUP BY activity_type")
    results = cur.fetchall()
    for activity_type, count in results:
        print(f"  {activity_type}: {count} records")
    
    print("\nHas_run distribution:")
    cur.execute("SELECT has_run, COUNT(*) FROM runs GROUP BY has_run")
    results = cur.fetchall()
    for has_run, count in results:
        print(f"  has_run = {has_run}: {count} records")
    
    print("\nCombined distribution (has_run vs activity_type):")
    cur.execute("SELECT has_run, activity_type, COUNT(*) FROM runs GROUP BY has_run, activity_type")
    results = cur.fetchall()
    for has_run, activity_type, count in results:
        print(f"  has_run = {has_run}, activity_type = {activity_type}: {count} records")
    
    con.close()

if __name__ == "__main__":
    check_database_state()
