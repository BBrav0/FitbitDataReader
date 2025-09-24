import fitbit
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv
import sqlite3 as sql
import time
import requests

def format_duration(ms):
    """Convert milliseconds to H:MM:SS string."""
    try:
        total_seconds = max(0, int(ms) // 1000)
    except Exception:
        return None
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}:{minutes:02d}:{seconds:02d}"

def format_pace(distance_miles, ms):
    """Compute average pace as HH:MM:SS string (zero-padded hours).
    Returns None if distance is invalid or ms is None.
    """
    if distance_miles is None or ms is None:
        return None
    try:
        distance = float(distance_miles)
        if distance <= 0:
            return None
        total_seconds = max(0, int(ms) // 1000)
        seconds_per_mile = int(round(total_seconds / distance))
        hours = seconds_per_mile // 3600
        minutes = (seconds_per_mile % 3600) // 60
        seconds = seconds_per_mile % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        return None

def elevation_gain_from_tcx(xml_text: str) -> float:
    """Sum positive altitude deltas from TCX content. Returns meters."""
    try:
        import re
        alts = [float(x) for x in re.findall(r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", xml_text or "")]
        if not alts:
            return 0.0
        gain = 0.0
        prev = alts[0]
        for a in alts[1:]:
            delta = a - prev
            if delta > 0:
                gain += delta
            prev = a
        return gain
    except Exception:
        return 0.0

def compute_elevation_gain_feet(activity: dict, access_token: str) -> float:
    """Get elevation gain in feet using API field if available, else TCX fallback."""
    elev_m = activity.get('elevationGain')
    try:
        if elev_m is not None:
            return float(elev_m) * 3.28084
    except Exception:
        pass
    # Fallback to TCX
    tcx_link = activity.get('tcxLink')
    log_id = activity.get('logId')
    tcx_xml = None
    try:
        if tcx_link:
            r = requests.get(tcx_link, headers={'Authorization': f'Bearer {access_token}'}, timeout=30)
            if r.status_code == 200:
                tcx_xml = r.text
        if tcx_xml is None and log_id:
            url = f"https://api.fitbit.com/1/user/-/activities/{log_id}.tcx"
            r = requests.get(url, headers={'Authorization': f'Bearer {access_token}'}, timeout=30)
            if r.status_code == 200:
                tcx_xml = r.text
    except Exception:
        tcx_xml = None
    elev_from_tcx_m = elevation_gain_from_tcx(tcx_xml) if tcx_xml else 0.0
    return elev_from_tcx_m * 3.28084

def cache_run(date_str, distance, duration, steps, minhr, maxhr, avghr, calories, resting_hr=0, elev_gain_ft=None, has_run=1):
    con = sql.connect("cache.db")
    cur = con.cursor()

    # Store duration as formatted H:MM:SS string from milliseconds
    formatted_duration = format_duration(duration) if duration is not None else None
    average_pace = format_pace(distance, duration)
    elev_gain_per_mile = None
    try:
        if elev_gain_ft is not None and distance not in (None, 0):
            elev_gain_per_mile = float(elev_gain_ft) / float(distance)
    except Exception:
        elev_gain_per_mile = None

    cur.execute("""
        INSERT OR REPLACE INTO runs (date, distance, duration, avg_pace, elev_gain_ft, elev_gain_per_mile, steps, minhr, maxhr, avghr, calories, resting_hr, has_run) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, distance, formatted_duration, average_pace, elev_gain_ft, elev_gain_per_mile, steps, minhr, maxhr, avghr, calories, resting_hr, has_run))

    con.commit()
    con.close()

def cache_no_run(date_str):
    """Insert a placeholder for a date with no runs to avoid future API calls."""
    con = sql.connect("cache.db")
    cur = con.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO runs (date, distance, duration, avg_pace, elev_gain_ft, elev_gain_per_mile, steps, minhr, maxhr, avghr, calories, resting_hr, has_run)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (date_str, None, None, None, None, None, None, None, None, None, None, None, 0),
    )
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
            duration TEXT,
            avg_pace TEXT,
            elev_gain_ft REAL,
            elev_gain_per_mile REAL,
            steps INTEGER,
            minhr INTEGER,
            maxhr INTEGER,
            avghr INTEGER,
            calories INTEGER,
            resting_hr INTEGER,
            has_run INTEGER
        )

""")

con.commit()
con.close()

# Ensure schema has has_run, avg_pace and elev_gain_ft columns for existing databases
try:
    con = sql.connect("cache.db")
    cur = con.cursor()
    cur.execute("PRAGMA table_info(runs)")
    columns = [row[1] for row in cur.fetchall()]
    if 'has_run' not in columns:
        cur.execute("ALTER TABLE runs ADD COLUMN has_run INTEGER")
        con.commit()
    if 'avg_pace' not in columns:
        cur.execute("ALTER TABLE runs ADD COLUMN avg_pace TEXT")
        con.commit()
    if 'elev_gain_ft' not in columns:
        cur.execute("ALTER TABLE runs ADD COLUMN elev_gain_ft REAL")
        con.commit()
    if 'elev_gain_per_mile' not in columns:
        cur.execute("ALTER TABLE runs ADD COLUMN elev_gain_per_mile REAL")
        con.commit()
    con.close()
except Exception as e:
    print(f"warning: could not ensure has_run column exists: {e}")

print("db ready")

# =======================


# ===== MAIN ========

# Set start date to February 20th of current year
current_year = date.today().year
start_date = date(2025, 2, 20)
curr = date.today()
request_count = 0

# Check if we have complete data for the current date
def date_is_complete(check_date):
    """Return True if the row exists and required fields are present.
    Rule: if has_run==0 it's complete; if has_run==1, require elev_gain_ft not NULL.
    """
    try:
        con = sql.connect("cache.db")
        cur = con.cursor()
        cur.execute("SELECT has_run, elev_gain_ft, elev_gain_per_mile FROM runs WHERE date = ?", (str(check_date),))
        row = cur.fetchone()
        con.close()
        if row is None:
            return False
        has_run_val, elev_gain_ft_val, elev_gain_per_mile_val = row
        if (has_run_val or 0) == 0:
            return True
        return (elev_gain_ft_val is not None) and (elev_gain_per_mile_val is not None)
    except Exception:
        return False

while curr >= start_date:
    # Check if date already exists in database; if so, skip API request and move on
    if date_is_complete(curr):
        print(f"✓ Data already complete for {curr} - skipping API")
        curr = curr - timedelta(1)
        continue
    
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
                    # Compute elevation gain in feet
                    elev_gain_ft = compute_elevation_gain_feet(activity, ACCESS_TOKEN)
                    
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
                    print(f"    Elevation Gain (ft): {elev_gain_ft:.1f}")
                    
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
                            activity.get('steps', 0), min_hr, max_hr, avg_hr, activity.get('calories', 0), resting_hr, elev_gain_ft, has_run=1)
                    break
        else:
            print(f"  No runs found for {curr}")
            # Cache a placeholder to avoid re-querying this date
            cache_no_run(str(curr))
            
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
            print("  Waiting 100 seconds before retry...")
            time.sleep(100)
            # Don't move to next date - retry the same date
            continue
        else:
            print(f"  ❌ Error getting activities for {curr}: {e}")
            # Move to previous day for other errors
            curr = curr - timedelta(1)

print(f"\nCompleted processing {request_count} API requests")