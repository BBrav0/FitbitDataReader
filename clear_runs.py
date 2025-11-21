#!/usr/bin/env python3
"""
Clear all Run activities from cache.db to allow repopulation with corrected elevation.

This script deletes all entries where activity_type = 'Run' so that db_filler.py
can recalculate elevation using the improved algorithm.
"""
import sqlite3
import sys

def show_runs_to_delete():
    """Display runs that will be deleted."""
    con = sqlite3.connect("cache.db")
    cur = con.cursor()
    
    # Count runs to delete
    cur.execute("SELECT COUNT(*) FROM runs WHERE activity_type = 'Run'")
    count = cur.fetchone()[0]
    
    if count == 0:
        print("No Run activities found in database.")
        con.close()
        return 0
    
    print(f"Found {count} Run activities to delete:")
    print()
    
    # Show sample of runs
    cur.execute("""
        SELECT date, distance, elev_gain 
        FROM runs 
        WHERE activity_type = 'Run' 
        ORDER BY date DESC 
        LIMIT 10
    """)
    
    print("Sample (most recent 10):")
    print(f"{'Date':<12} {'Distance':<12} {'Elevation':<12}")
    print("-" * 40)
    for row in cur.fetchall():
        date, distance, elev = row
        dist_str = f"{distance:.2f} mi" if distance else "N/A"
        elev_str = f"{elev:.1f} ft" if elev else "N/A"
        print(f"{date:<12} {dist_str:<12} {elev_str:<12}")
    
    if count > 10:
        print(f"... and {count - 10} more")
    
    con.close()
    return count

def delete_runs():
    """Delete all Run activities from the database."""
    con = sqlite3.connect("cache.db")
    cur = con.cursor()
    
    # Delete all runs
    cur.execute("DELETE FROM runs WHERE activity_type = 'Run'")
    deleted = cur.rowcount
    
    con.commit()
    con.close()
    
    return deleted

def main():
    # Check for --force flag
    force = '--force' in sys.argv or '-f' in sys.argv
    
    print("="*60)
    print("CLEAR RUN ACTIVITIES FROM CACHE.DB")
    print("="*60)
    print()
    print("This will delete all Run activities so db_filler.py can")
    print("repopulate them with corrected elevation calculations.")
    print()
    
    # Show what will be deleted
    count = show_runs_to_delete()
    
    if count == 0:
        return
    
    print()
    print("="*60)
    
    # Ask for confirmation unless --force flag is used
    if not force:
        try:
            response = input("\nProceed with deletion? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("Deletion cancelled.")
                return
        except EOFError:
            print("\nERROR: Cannot read input. Use --force flag to skip confirmation.")
            print("Usage: python clear_runs.py --force")
            return
    else:
        print("\n--force flag detected, proceeding with deletion...")
    
    print("\nDeleting runs...")
    deleted = delete_runs()
    
    print(f"Successfully deleted {deleted} Run activities")
    print()
    print("You can now run db_filler.py to repopulate with corrected elevations.")
    print()

if __name__ == '__main__':
    main()

