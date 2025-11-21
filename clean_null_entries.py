#!/usr/bin/env python3
"""
CAUTION: This script should ONLY be used in specific scenarios!

Null entries (activity_type='None') are INTENTIONAL and mark days with no activities.
They prevent unnecessary API calls to Fitbit.

ONLY delete null entries if:
1. You interrupted db_filler.py mid-run (incomplete processing)
2. You're starting fresh and want to reprocess everything
3. You know specific dates had runs but are marked as None

Do NOT delete null entries during normal operation!
"""
import sqlite3
import sys

conn = sqlite3.connect('cache.db')
cursor = conn.cursor()

# Find all null/pending entries (activity_type = 'None' or all fields NULL)
cursor.execute("""
    SELECT date, distance, duration, activity_type 
    FROM runs 
    WHERE activity_type = 'None' OR activity_type IS NULL
    ORDER BY date DESC
""")

null_entries = cursor.fetchall()

if not null_entries:
    print("No null entries found. Database is clean!")
else:
    print(f"Found {len(null_entries)} null/pending entries:")
    print()
    for date, distance, duration, activity_type in null_entries[:10]:
        print(f"  {date}: distance={distance}, duration={duration}, type={activity_type}")
    
    if len(null_entries) > 10:
        print(f"  ... and {len(null_entries) - 10} more")
    
    print()
    
    # Check for --force flag
    if '--force' in sys.argv:
        proceed = True
    else:
        try:
            response = input(f"Delete all {len(null_entries)} null entries? (yes/no): ")
            proceed = response.lower() == 'yes'
        except EOFError:
            print("No input available. Use --force flag to delete without prompt.")
            proceed = False
    
    if proceed:
        cursor.execute("""
            DELETE FROM runs 
            WHERE activity_type = 'None' OR activity_type IS NULL
        """)
        conn.commit()
        print(f"Deleted {cursor.rowcount} null entries")
    else:
        print("No changes made")

conn.close()

