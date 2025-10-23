import sqlite3 as sql

def update_existing_cache_data():
    """Update existing cache.db records to set activity_type based on has_run value"""
    con = sql.connect("cache.db")
    cur = con.cursor()
    
    # Check if activity_type column exists
    cur.execute("PRAGMA table_info(runs)")
    columns = [row[1] for row in cur.fetchall()]
    
    if 'activity_type' not in columns:
        print("activity_type column not found. Please run db_filler.py first to add the column.")
        con.close()
        return
    
    # Count records that need updating
    cur.execute("SELECT COUNT(*) FROM runs WHERE activity_type IS NULL")
    null_count = cur.fetchone()[0]
    
    if null_count == 0:
        print("No records found with NULL activity_type. Database is already up to date.")
        con.close()
        return
    
    print(f"Found {null_count} records with NULL activity_type that need updating...")
    
    # Update records where has_run = 1 to activity_type = 'Run'
    cur.execute("UPDATE runs SET activity_type = 'Run' WHERE has_run = 1 AND activity_type IS NULL")
    updated_runs = cur.rowcount
    
    # Update records where has_run = 0 to activity_type = 'None'
    cur.execute("UPDATE runs SET activity_type = 'None' WHERE has_run = 0 AND activity_type IS NULL")
    updated_none = cur.rowcount
    
    con.commit()
    con.close()
    
    print(f"[OK] Updated {updated_runs} records to activity_type = 'Run' (has_run = 1)")
    print(f"[OK] Updated {updated_none} records to activity_type = 'None' (has_run = 0)")
    print(f"[OK] Total records updated: {updated_runs + updated_none}")
    
    # Verify the update
    con = sql.connect("cache.db")
    cur = con.cursor()
    cur.execute("SELECT activity_type, COUNT(*) FROM runs GROUP BY activity_type")
    results = cur.fetchall()
    con.close()
    
    print("\nCurrent activity_type distribution:")
    for activity_type, count in results:
        print(f"  {activity_type}: {count} records")

if __name__ == "__main__":
    print("Updating existing cache.db records...")
    update_existing_cache_data()
    print("Migration complete!")
