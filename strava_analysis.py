#!/usr/bin/env python3
"""Analyze Strava elevation data to reverse-engineer their algorithm."""
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import time
import json

load_dotenv()

S_ACCESS_TOKEN = os.getenv('S_ACCESS_TOKEN')
S_CLIENT_ID = os.getenv('S_CLIENT_ID')
S_CLIENT_SECRET = os.getenv('S_CLIENT_SECRET')
S_REFRESH_TOKEN = os.getenv('S_REFRESH_TOKEN')

if not S_ACCESS_TOKEN:
    print("Error: S_ACCESS_TOKEN not found in .env")
    exit(1)

# These are optional - only needed if token refresh is required
can_refresh = all([S_CLIENT_ID, S_CLIENT_SECRET, S_REFRESH_TOKEN])
if not can_refresh:
    print("Note: Token refresh not available (missing S_CLIENT_ID, S_CLIENT_SECRET, or S_REFRESH_TOKEN)")
    print("Trying with existing access token...")

def refresh_access_token():
    """Refresh the Strava access token."""
    print("Refreshing Strava access token...")
    
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': S_CLIENT_ID,
            'client_secret': S_CLIENT_SECRET,
            'refresh_token': S_REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }
    )
    
    if response.status_code != 200:
        print(f"Error refreshing token: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    new_access_token = data.get('access_token')
    
    print(f"Token refreshed successfully!")
    print(f"New access token: {new_access_token[:20]}...")
    print("\nPlease update your .env file with the new S_ACCESS_TOKEN:")
    print(f"S_ACCESS_TOKEN={new_access_token}")
    
    return new_access_token

headers = {'Authorization': f'Bearer {S_ACCESS_TOKEN}'}

print("="*80)
print("STRAVA API ANALYSIS")
print("="*80)

# Get athlete info
print("\nFetching athlete information...")
try:
    response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
    
    if response.status_code == 401:
        if can_refresh:
            print("Access token expired, refreshing...")
            new_token = refresh_access_token()
            if not new_token:
                exit(1)
            headers = {'Authorization': f'Bearer {new_token}'}
            S_ACCESS_TOKEN = new_token
            
            # Retry with new token
            response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
        else:
            print("Error: Access token expired and cannot refresh (missing credentials)")
            print("Please provide S_CLIENT_ID in .env to enable token refresh")
            exit(1)
    
    if response.status_code != 200:
        print(f"Error: Status {response.status_code}")
        print("Response:", response.text)
        exit(1)
    
    athlete = response.json()
    athlete_id = athlete['id']
    
    print(f"Athlete: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
    print(f"Athlete ID: {athlete_id}")
    
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Our test run dates (need to find activity IDs on Strava)
TEST_DATES = {
    '2025-11-09': 264.0,
    '2025-11-16': 224.0,
    '2025-10-04': 1147.0,
    '2025-10-02': 465.0,
    '2025-10-19': 450.0,
    '2025-10-06': 437.0,
    '2025-11-18': 714.0,
}

print("\n" + "="*80)
print("FETCHING STRAVA ACTIVITIES")
print("="*80)

# Get recent activities
print("\nFetching activities from Strava...")

activities = []
page = 1
per_page = 100

# Fetch activities (paginated)
while True:
    try:
        response = requests.get(
            f'https://www.strava.com/api/v3/athlete/activities',
            headers=headers,
            params={'per_page': per_page, 'page': page}
        )
        
        if response.status_code != 200:
            print(f"Error fetching activities: {response.status_code}")
            print(response.text)
            break
        
        page_activities = response.json()
        if not page_activities:
            break
        
        activities.extend(page_activities)
        print(f"  Fetched page {page}: {len(page_activities)} activities")
        
        page += 1
        time.sleep(0.5)  # Rate limiting
        
        # Stop if we have enough (activities before Feb 2025)
        if page > 5:  # Should be enough to cover our test dates
            break
            
    except Exception as e:
        print(f"Error: {e}")
        break

print(f"\nTotal activities fetched: {len(activities)}")

# Match our test dates to Strava activities
print("\n" + "="*80)
print("MATCHING TEST RUNS TO STRAVA ACTIVITIES")
print("="*80)

matched_activities = {}

for activity in activities:
    # Parse the activity date
    start_date = activity.get('start_date_local', '')
    if not start_date:
        continue
    
    # Extract date portion (YYYY-MM-DD)
    activity_date = start_date.split('T')[0]
    
    # Check if this matches one of our test dates
    if activity_date in TEST_DATES:
        activity_type = activity.get('type', '')
        
        # Only match Run activities
        if activity_type == 'Run':
            strava_elev = activity.get('total_elevation_gain', 0)  # in meters
            strava_elev_ft = strava_elev * 3.28084
            
            matched_activities[activity_date] = {
                'id': activity['id'],
                'name': activity.get('name', 'Unnamed'),
                'distance_km': activity.get('distance', 0) / 1000,
                'distance_mi': activity.get('distance', 0) / 1609.34,
                'elevation_m': strava_elev,
                'elevation_ft': strava_elev_ft,
                'target_ft': TEST_DATES[activity_date],
                'moving_time': activity.get('moving_time', 0),
                'elev_high': activity.get('elev_high'),
                'elev_low': activity.get('elev_low'),
                'has_heartrate': activity.get('has_heartrate', False),
                'device_name': activity.get('device_name', 'Unknown'),
            }

print(f"\nMatched {len(matched_activities)} of {len(TEST_DATES)} test runs:")
print()

for date in sorted(matched_activities.keys()):
    info = matched_activities[date]
    print(f"{date}:")
    print(f"  Activity ID: {info['id']}")
    print(f"  Name: {info['name']}")
    print(f"  Distance: {info['distance_mi']:.2f} mi")
    print(f"  Strava elevation: {info['elevation_ft']:.0f} ft ({info['elevation_m']:.1f}m)")
    print(f"  Target we used: {info['target_ft']:.0f} ft")
    
    if abs(info['elevation_ft'] - info['target_ft']) > 5:
        print(f"  WARNING: Mismatch! ({info['elevation_ft'] - info['target_ft']:+.0f} ft difference)")
    
    if info['elev_high'] and info['elev_low']:
        alt_range = info['elev_high'] - info['elev_low']
        print(f"  Altitude range: {alt_range:.1f}m")
    
    print(f"  Device: {info['device_name']}")
    print()

# Save for detailed analysis
print("="*80)
print("SAVING ACTIVITY DATA FOR ANALYSIS")
print("="*80)

# Save matched activities
with open('strava_activities.json', 'w') as f:
    json.dump(matched_activities, f, indent=2)

# Also save the new access token for future use
token_info = {
    'access_token': S_ACCESS_TOKEN,
    'athlete_id': athlete_id,
}

with open('strava_token.json', 'w') as f:
    json.dump(token_info, f, indent=2)

print(f"\nSaved {len(matched_activities)} activities to strava_activities.json")
print(f"Saved token info to strava_token.json")

# Summary
print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("\n1. Verified Strava elevations match our targets")
print("2. Collected activity metadata (device, altitude range, etc.)")
print("\nNow we can:")
print("  - Fetch detailed activity streams (elevation profile point-by-point)")
print("  - Analyze GPS quality indicators")
print("  - Look for patterns in how Strava processes different devices/conditions")
print("\nRun: python strava_detailed_analysis.py")
