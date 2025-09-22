import fitbit
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv
import sqlite3

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

auth_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET,
                          access_token=ACCESS_TOKEN,
                          refresh_token=REFRESH_TOKEN,
                          system='en_US')

# =======================


# ===== DATE SETUP ========

curr = date.today()
history = 30
while history>0:


    try:
        # Get activities for current date
        daily_activities = auth_client.activities(date=curr)
        activities = daily_activities.get('activities', [])
        
        if activities:
            for activity in activities:
                if activity.get('activityParentName', 'N/A') == "Run":
                    date_str = str(curr)
                    print(f"\n  Run {date_str}:")
                    print(f"  Activity ID: {activity.get('activityId', 'N/A')}")
                    print(f"  Start Time: {activity.get('startTime', 'N/A')}")
                    print(f"  Duration: {activity.get('duration', 0)}")
                    print(f"  Distance: {round(activity.get('distance', 0), 2)} miles")
                    print(f"  Steps: {activity.get('steps', 0):,}")
                    print(f"  Calories: {activity.get('calories', 0)}")
                    print(f"  Log ID: {activity.get('logId', 'N/A')}")
                    print("-" * 80)
                    break
            
        else:
            print(f"No runs found for {curr}")
            
    except Exception as e:
        print(f"  Error getting activities for {curr}: {e}")


    history -=1
    curr = curr- timedelta(1)