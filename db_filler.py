import fitbit
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv
import sqlite3 as sql
import time
import requests

def cache_run(date_str, distance, duration, steps, minhr, maxhr, avghr, calories, resting_hr=0):
    con = sql.connect("cache.db")
    cur = con.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO runs (date, distance, duration, steps, minhr, maxhr, avghr, calories, resting_hr) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, distance, duration, steps, minhr, maxhr, avghr, calories, resting_hr))

    con.commit()
    con.close()

def get_resting_heart_rate(date_str):
    """Get resting heart rate for a specific date"""
    try:
        # Get resting heart rate from Fitbit API using intraday time series
        resting_hr_data = auth_client.intraday_time_series('activities/heart', base_date=date_str, detail_level='1min')
        if resting_hr_data and 'activities-heart' in resting_hr_data:
            heart_data = resting_hr_data['activities-heart'][0]
            return heart_data.get('value', {}).get('restingHeartRate', 0)
        return 0
    except Exception as e:
        print(f"    Error getting resting heart rate: {e}")
        return 0

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

        CREATE TABLE IF NOT EXISTS runs (
            date TEXT PRIMARY KEY,
            distance REAL,
            duration INTEGER,
            steps INTEGER,
            minhr INTEGER,
            maxhr INTEGER,
            avghr INTEGER,
            calories INTEGER,
            resting_hr INTEGER
        )

""")

con.commit()
con.close()

print("db ready")

# =======================


# ===== MAIN ========

# Set start date to February 20th of current year
current_year = date.today().year
start_date = date(2025, 2, 20)
curr = date.today()
request_count = 0

# Check if we have data for the current date
def date_exists_in_db(check_date):
    """Check if a date already exists in the database"""
    try:
        con = sql.connect("cache.db")
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM runs WHERE date = ?", (str(check_date),))
        count = cur.fetchone()[0]
        con.close()
        return count > 0
    except:
        return False

while curr >= start_date:
    # Check if date already exists in database
    if date_exists_in_db(curr):
        print(f"✓ Data already exists for {curr} - all previous dates have been processed")
        print("Exiting program - no more data to fetch")
        break
    
    days_remaining = (curr - start_date).days + 1
    print(f"Processing {curr} ({days_remaining} days remaining)...")
    
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
                    # Skip runs with 0 distance
                    distance = activity.get('distance', 0)
                    if distance == 0:
                        print(f"  ⚠ Skipping run with 0 distance for {curr}")
                        continue
                        
                    print(f"  ✓ Found run for {curr}")
                    date_str = str(curr)
                    print(f"    Run {date_str}:")
                    print(f"    Activity ID: {activity.get('activityId', 'N/A')}")
                    print(f"    Start Time: {activity.get('startTime', 'N/A')}")
                    print(f"    Duration: {activity.get('duration', 0)}")
                    print(f"    Distance: {round(activity.get('distance', 0), 2)} miles")
                    print(f"    Steps: {activity.get('steps', 0)}")
                    print(f"    Calories: {activity.get('calories', 0)}")
                    # Try to get heart rate from TCX file
                    tcx_link = activity.get('tcxLink', '')
                    avg_hr = 0
                    max_hr = 0
                    min_hr = 0
                    
                    if tcx_link:
                        try:
                            import requests
                            tcx_response = requests.get(tcx_link, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
                            if tcx_response.status_code == 200:
                                tcx_content = tcx_response.text
                                # Parse TCX for heart rate data
                                import re
                                heart_rates = re.findall(r'<HeartRateBpm><Value>(\d+)</Value></HeartRateBpm>', tcx_content)
                                if heart_rates:
                                    heart_rates = [int(hr) for hr in heart_rates]
                                    avg_hr = sum(heart_rates) // len(heart_rates)
                                    max_hr = max(heart_rates)
                                    print(f"    Average HR: {avg_hr} (from TCX)")
                                    print(f"    Max HR: {max_hr} (from TCX)")
                                else:
                                    print(f"    Average HR: N/A (no heart rate data in TCX)")
                            else:
                                print(f"    Average HR: N/A (could not fetch TCX)")
                        except Exception as e:
                            print(f"    Average HR: N/A (error fetching TCX: {e})")
                    else:
                        print(f"    Average HR: N/A (no TCX link available)")
                    
                    print(f"    Log ID: {activity.get('logId', 'N/A')}")
                    print(f"    TCX Link: {activity.get('tcxLink', 'N/A')}")
                    
                    # Get resting heart rate for the day
                    resting_hr = get_resting_heart_rate(date_str)
                    print(f"    Resting HR: {resting_hr}")
                    
                    # Try to construct TCX URL manually if not available
                    log_id = activity.get('logId', 'N/A')
                    if log_id != 'N/A' and not activity.get('tcxLink'):
                        tcx_url = f"https://api.fitbit.com/1/user/-/activities/{log_id}.tcx"
                        print(f"    Constructed TCX URL: {tcx_url}")
                        
                        try:
                            # Try direct HTTP request with timeout
                            tcx_response = requests.get(tcx_url, headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}, timeout=10)
                            if tcx_response.status_code == 200:
                                tcx_content = tcx_response.text
                                print(f"    TCX file size: {len(tcx_content)} characters")
                                
                                # Parse TCX for heart rate data - try different patterns
                                import re
                                heart_rates = re.findall(r'<HeartRateBpm><Value>(\d+)</Value></HeartRateBpm>', tcx_content)
                                if not heart_rates:
                                    # Try alternative patterns
                                    heart_rates = re.findall(r'<HeartRateBpm>(\d+)</HeartRateBpm>', tcx_content)
                                if not heart_rates:
                                    heart_rates = re.findall(r'<Value>(\d+)</Value>', tcx_content)
                                
                                if heart_rates:
                                    heart_rates = [int(hr) for hr in heart_rates]
                                    avg_hr = sum(heart_rates) // len(heart_rates)
                                    max_hr = max(heart_rates)
                                    
                                    # Ignore first 2 minutes of heart rate data for min calculation
                                    # Assuming ~1 reading per second, first 2 minutes = ~120 readings
                                    first_two_minutes_readings = min(120, len(heart_rates))
                                    min_hr = min(heart_rates[first_two_minutes_readings:]) if len(heart_rates) > first_two_minutes_readings else min(heart_rates)
                                    
                                    print(f"    Average HR: {avg_hr} (from constructed TCX)")
                                    print(f"    Max HR: {max_hr} (from constructed TCX)")
                                    print(f"    Min HR: {min_hr} (from constructed TCX, ignoring first 2 minutes)")
                                    print(f"    Found {len(heart_rates)} heart rate readings")
                                else:
                                    print(f"    Average HR: N/A (no heart rate data in constructed TCX)")
                                    # Show first 500 characters of TCX to debug
                                    print(f"    TCX preview: {tcx_content[:500]}...")
                            else:
                                print(f"    Average HR: N/A (could not fetch constructed TCX: {tcx_response.status_code})")
                        except Exception as e:
                            print(f"    Average HR: N/A (error fetching constructed TCX: {e})")
                    
                    print("-" * 50)
                    # Cache the run data with heart rate info from TCX and resting HR
                    cache_run(date_str, activity.get('distance', 0), activity.get('duration', 0), 
                            activity.get('steps', 0), min_hr, max_hr, avg_hr, activity.get('calories', 0), resting_hr)
                    break
        else:
            print(f"  No runs found for {curr}")
            
        # Move to previous day after successful processing (regardless of runs found)
        curr = curr - timedelta(1)
        
    except requests.exceptions.Timeout:
        print(f"  ⚠ Timeout getting activities for {curr} - skipping")
        # Move to previous day
        curr = curr - timedelta(1)
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ Network error for {curr}: {e}")
        print("  Waiting 30 seconds before retry...")
        time.sleep(30)
        # Don't move to next date - retry the same date
        continue
    except Exception as e:
        error_msg = str(e)
        if 'retry-after' in error_msg.lower():
            print(f"  ⚠ Rate limit hit for {curr}: {e}")
            print("  Waiting 30 seconds before retry...")
            time.sleep(30)
            # Don't move to next date - retry the same date
            continue
        else:
            print(f"  ❌ Error getting activities for {curr}: {e}")
            # Move to previous day for other errors
            curr = curr - timedelta(1)

print(f"\nCompleted processing {request_count} API requests")