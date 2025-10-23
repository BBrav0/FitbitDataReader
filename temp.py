import sqlite3 as sql

def migrate_remove_has_run_column():
    """
    Migration script to remove the has_run column from the cache.db database.
    This creates a new table without the has_run column, copies all data,
    drops the old table, and renames the new table.
    """
    print("Starting migration to remove has_run column...")
    
    try:
        con = sql.connect("cache.db")
        cur = con.cursor()
        
        # Check if has_run column exists
        cur.execute("PRAGMA table_info(runs)")
        columns = [row[1] for row in cur.fetchall()]
        
        if 'has_run' not in columns:
            print("has_run column not found. Migration not needed.")
            con.close()
            return
        
        print("has_run column found. Proceeding with migration...")
        
        # Start transaction
        cur.execute("BEGIN TRANSACTION")
        
        # Create new table without has_run column
        cur.execute("""
            CREATE TABLE runs_new (
                date TEXT PRIMARY KEY,
                distance REAL,
                duration TEXT,
                avg_pace TEXT,
                elev_gain REAL,
                elev_gain_per_mile REAL,
                steps INTEGER,
                cadence INTEGER,
                minhr INTEGER,
                maxhr INTEGER,
                avghr INTEGER,
                calories INTEGER,
                resting_hr INTEGER,
                activity_type TEXT
            )
        """)
        
        # Copy all data from old table to new table, excluding has_run column
        cur.execute("""
            INSERT INTO runs_new (
                date, distance, duration, avg_pace, elev_gain, elev_gain_per_mile,
                steps, cadence, minhr, maxhr, avghr, calories, resting_hr, activity_type
            )
            SELECT 
                date, distance, duration, avg_pace, elev_gain, elev_gain_per_mile,
                steps, cadence, minhr, maxhr, avghr, calories, resting_hr, activity_type
            FROM runs
        """)
        
        # Drop the old table
        cur.execute("DROP TABLE runs")
        
        # Rename new table to runs
        cur.execute("ALTER TABLE runs_new RENAME TO runs")
        
        # Commit transaction
        con.commit()
        con.close()
        
        print("Migration completed successfully!")
        print("has_run column has been removed from the database.")
        
        # Verify the migration
        con = sql.connect("cache.db")
        cur = con.cursor()
        cur.execute("PRAGMA table_info(runs)")
        columns = [row[1] for row in cur.fetchall()]
        con.close()
        
        print(f"Current table columns: {columns}")
        
        if 'has_run' in columns:
            print("ERROR: has_run column still exists after migration!")
        else:
            print("SUCCESS: has_run column successfully removed!")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        try:
            con.rollback()
            con.close()
        except:
            pass
        raise

if __name__ == "__main__":
    migrate_remove_has_run_column()
