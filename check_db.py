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
    
    print("\nRun vs Non-run distribution:")
    cur.execute("SELECT 
        CASE 
            WHEN activity_type IN ('Run', 'Treadmill run') THEN 'Run'
            ELSE 'No Run'
        END as run_status, 
        COUNT(*) 
    FROM runs GROUP BY run_status")
    results = cur.fetchall()
    for run_status, count in results:
        print(f"  {run_status}: {count} records")
    
    con.close()

if __name__ == "__main__":
    check_database_state()
