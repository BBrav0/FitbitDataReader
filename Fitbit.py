import fitbit
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv
import sqlite3 as sql
import time
import requests

def cache_dailys(date_str, rhr):
    con = sql.connect("cache.db")
    cur = con.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO daily (date, rhr) 
        VALUES (?, ?)
    """, (date_str, rhr))

    con.commit()
    con.close()

# ===== ENVIRONNENTALS =======

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')

if not all([CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN]):
    print("fix your .env")
    exit(1)

# ============================

# ===== API SETUP =======

# Configure requests session with timeout
import requests
session = requests.Session()
session.timeout = 30  # 30 second timeout

auth_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET,
                          access_token=ACCESS_TOKEN,
                          refresh_token=REFRESH_TOKEN,
                          system='en_US',
                          requests_kwargs={'timeout': 30})

# =======================


# ===== SQL SETUP =======


con = sql.connect("cache.db")
cur = con.cursor()

cur.execute("""

        CREATE TABLE IF NOT EXISTS dailybase (
            date TEXT PRIMARY KEY,
            rhr INTEGER
        )

""")

cur.execute("""

        CREATE TABLE IF NOT EXISTS dailyruns (
            date TEXT PRIMARY KEY,
            distance REAL
            duration INTEGER
            steps INTEGER
            minhr INTEGER
            maxhr INTEGER
            avghr INTEGER
            calories INTEGER
        )

""")

con.commit()
con.close()

print("db ready")

# =======================


# ===== MAIN ========

curr = date.today()
history = 30
request_count = 0

while history > 0:
    print(f"Processing {curr} ({history} days remaining)...")
    
    try:
        # Add delay between requests to respect rate limits
        if request_count > 0:
            print("  Waiting 2 seconds before next request...")
            time.sleep(2)
        
        # Get activities for current date with timeout
        daily_activities = auth_client.activities(date=curr)
        activities = daily_activities.get('activities', [])
        request_count += 1
        
        if activities:
            for activity in activities:
                if activity.get('activityParentName', 'N/A') == "Run":
                    print(f"  ✓ Found run for {curr}")
                    date_str = str(curr)
                    print(f"    Run {date_str}:")
                    print(f"    Activity ID: {activity.get('activityId', 'N/A')}")
                    print(f"    Start Time: {activity.get('startTime', 'N/A')}")
                    print(f"    Duration: {activity.get('duration', 0)}")
                    print(f"    Distance: {round(activity.get('distance', 0), 2)} miles")
                    print(f"    Steps: {activity.get('steps', 0):,}")
                    print(f"    Calories: {activity.get('calories', 0)}")
                    print(f"    Log ID: {activity.get('logId', 'N/A')}")
                    print("-" * 50)
                    break
        else:
            print(f"  No runs found for {curr}")
            
    except requests.exceptions.Timeout:
        print(f"  ⚠ Timeout getting activities for {curr} - skipping")
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ Network error for {curr}: {e}")
        print("  Waiting 5 seconds before retry...")
        time.sleep(5)
    except Exception as e:
        print(f"  ❌ Error getting activities for {curr}: {e}")

    history -= 1
    curr = curr - timedelta(1)

print(f"\nCompleted processing {request_count} API requests")