import sqlite3 as sql

def rename_elev_gain_ft_to_elev_gain():
    """
    Rename the elev_gain_ft column to elev_gain in the runs table while preserving all data.
    This function handles the column rename safely by creating a new table and copying data.
    """
    try:
        con = sql.connect("cache.db")
        cur = con.cursor()
        
        # Check if elev_gain_ft column exists
        cur.execute("PRAGMA table_info(runs)")
        columns = [row[1] for row in cur.fetchall()]
        
        if 'elev_gain_ft' not in columns:
            print("Column 'elev_gain_ft' does not exist. Nothing to rename.")
            con.close()
            return
        
        if 'elev_gain' in columns:
            print("Column 'elev_gain' already exists. Skipping rename.")
            con.close()
            return
        
        print("Starting column rename from 'elev_gain_ft' to 'elev_gain'...")
        
        # Start transaction
        cur.execute("BEGIN TRANSACTION")
        
        # Create new table with elev_gain instead of elev_gain_ft
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
                has_run INTEGER
            )
        """)
        
        # Copy all data from old table to new table, mapping elev_gain_ft to elev_gain
        cur.execute("""
            INSERT INTO runs_new (
                date, distance, duration, avg_pace, elev_gain, elev_gain_per_mile,
                steps, cadence, minhr, maxhr, avghr, calories, resting_hr, has_run
            )
            SELECT 
                date, distance, duration, avg_pace, elev_gain_ft, elev_gain_per_mile,
                steps, cadence, minhr, maxhr, avghr, calories, resting_hr, has_run
            FROM runs
        """)
        
        # Drop old table and rename new table
        cur.execute("DROP TABLE runs")
        cur.execute("ALTER TABLE runs_new RENAME TO runs")
        
        # Commit transaction
        con.commit()
        print("Successfully renamed 'elev_gain_ft' to 'elev_gain' while preserving all data.")
        
        # Verify the change
        cur.execute("PRAGMA table_info(runs)")
        columns_after = [row[1] for row in cur.fetchall()]
        if 'elev_gain' in columns_after and 'elev_gain_ft' not in columns_after:
            print("✓ Column rename verified successfully.")
        else:
            print("⚠ Warning: Column rename may not have completed correctly.")
            
    except Exception as e:
        print(f"Error during column rename: {e}")
        if 'con' in locals():
            con.rollback()
            print("Transaction rolled back due to error.")
    finally:
        if 'con' in locals():
            con.close()

if __name__ == "__main__":
    rename_elev_gain_ft_to_elev_gain()
