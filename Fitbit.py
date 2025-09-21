import fitbit
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')

if not all([CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN]):
    print("Error: Missing credentials in .env file")
    print("Please make sure your .env file contains:")
    print("CLIENT_ID=your_actual_client_id")
    print("CLIENT_SECRET=your_actual_client_secret") 
    print("ACCESS_TOKEN=your_actual_access_token")
    print("REFRESH_TOKEN=your_actual_refresh_token")
    exit(1)

auth_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET,
                          access_token=ACCESS_TOKEN,
                          refresh_token=REFRESH_TOKEN,
                          system='en_US')

# Date setup
today = date.today()
yesterday = today - timedelta(days=1)
week_ago = today - timedelta(days=7)

print("🏃‍♂️ FITBIT ACTIVITY LOG LIST")
print("=" * 50)
print(f"Today: {today}")
print(f"Yesterday: {yesterday}")
print(f"One week ago: {week_ago}")

try:
    print("\n1. Getting Logged Activities for September 20, 2025")
    print("-" * 50)
    
    # Focus on September 20, 2025
    target_date = date(2025, 9, 20)
    print(f"Target Date: {target_date}")
    
    try:
        # Get activities for September 20, 2025
        daily_activities = auth_client.activities(date=target_date)
        activities = daily_activities.get('activities', [])
        
        print(f"\nFound {len(activities)} logged activities on {target_date}")
        
        if activities:
            print("\n📋 DETAILED ACTIVITY LIST:")
            print("=" * 80)
            
            for activity in activities:
                if activity.get('activityParentName', 'N/A') == "Run":
                    print(f"\nActivity:")
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
            print(f"No activities found for {target_date}")
            
    except Exception as e:
        print(f"Error getting activities for {target_date}: {e}")
        print("This might be because the date is in the future or there's an API issue.")
    
except Exception as e:
    print(f"Error fetching activity log data: {e}")
    print("\nThis usually means:")
    print("1. Your access token is expired or invalid")
    print("2. You need to re-authorize your app")
    print("3. Check your .env file has the correct tokens")
    print("4. The activity scope may not be included in your token")