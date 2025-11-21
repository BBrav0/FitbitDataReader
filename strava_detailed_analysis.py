#!/usr/bin/env python3
"""Fetch detailed elevation streams from Strava and analyze their processing."""
import os
import requests
from dotenv import load_dotenv
import json
import time

load_dotenv()

S_ACCESS_TOKEN = os.getenv('S_ACCESS_TOKEN')

if not S_ACCESS_TOKEN:
    print("Error: S_ACCESS_TOKEN not found in .env")
    exit(1)

headers = {'Authorization': f'Bearer {S_ACCESS_TOKEN}'}

# Load matched activities
try:
    with open('strava_activities.json', 'r') as f:
        activities = json.load(f)
except FileNotFoundError:
    print("Error: strava_activities.json not found. Run strava_analysis.py first.")
    exit(1)

print("="*80)
print("FETCHING STRAVA ELEVATION STREAMS")
print("="*80)
print()

# Fetch elevation streams for each activity
detailed_data = {}

for date, info in sorted(activities.items()):
    activity_id = info['id']
    print(f"Fetching stream for {date} (Activity {activity_id})...")
    
    try:
        # Request elevation, time, distance, and latlng streams
        response = requests.get(
            f'https://www.strava.com/api/v3/activities/{activity_id}/streams',
            headers=headers,
            params={
                'keys': 'altitude,time,distance,latlng',
                'key_by_type': 'true'
            }
        )
        
        if response.status_code != 200:
            print(f"  Error: {response.status_code}")
            print(f"  {response.text}")
            continue
        
        streams = response.json()
        
        # Extract data
        altitude_data = streams.get('altitude', {}).get('data', [])
        time_data = streams.get('time', {}).get('data', [])
        distance_data = streams.get('distance', {}).get('data', [])
        latlng_data = streams.get('latlng', {}).get('data', [])
        
        detailed_data[date] = {
            'activity_id': activity_id,
            'name': info['name'],
            'distance_mi': info['distance_mi'],
            'strava_elevation_ft': info['elevation_ft'],
            'strava_elevation_m': info['elevation_m'],
            'target_ft': info['target_ft'],
            'altitude_range_m': info.get('elev_high', 0) - info.get('elev_low', 0) if info.get('elev_high') else None,
            'altitude_data': altitude_data,
            'time_data': time_data,
            'distance_data': distance_data,
            'latlng_data': latlng_data,
            'num_points': len(altitude_data),
        }
        
        print(f"  ✓ Got {len(altitude_data)} altitude points")
        
        time.sleep(0.5)  # Rate limiting
        
    except Exception as e:
        print(f"  Error: {e}")
        continue

print()
print("="*80)
print("SAVING DETAILED STREAM DATA")
print("="*80)

with open('strava_streams.json', 'w') as f:
    json.dump(detailed_data, f, indent=2)

print(f"\nSaved detailed streams for {len(detailed_data)} activities to strava_streams.json")

print()
print("="*80)
print("ANALYZING ELEVATION DATA")
print("="*80)
print()

# Analyze each activity's elevation profile
for date in sorted(detailed_data.keys()):
    data = detailed_data[date]
    altitudes = data['altitude_data']
    
    if not altitudes:
        continue
    
    print(f"{date} - {data['name']} ({data['distance_mi']:.2f} mi)")
    print(f"  Strava elevation: {data['strava_elevation_ft']:.0f} ft (target: {data['target_ft']:.0f} ft)")
    print(f"  Data points: {data['num_points']}")
    print(f"  Altitude range: {max(altitudes) - min(altitudes):.1f}m")
    
    # Calculate raw gain (summing all positive deltas)
    raw_gain = sum(max(0, altitudes[i+1] - altitudes[i]) for i in range(len(altitudes)-1))
    print(f"  Raw gain (no filtering): {raw_gain:.1f}m ({raw_gain * 3.28084:.0f} ft)")
    
    # Calculate noise level
    deltas = [altitudes[i+1] - altitudes[i] for i in range(len(altitudes)-1)]
    avg_delta = sum(abs(d) for d in deltas) / len(deltas)
    print(f"  Avg absolute delta: {avg_delta:.2f}m")
    
    # Sample spacing
    if len(data['time_data']) > 1:
        avg_time_spacing = sum(data['time_data'][i+1] - data['time_data'][i] for i in range(len(data['time_data'])-1)) / (len(data['time_data'])-1)
        print(f"  Avg time between points: {avg_time_spacing:.1f}s")
    
    if len(data['distance_data']) > 1:
        avg_dist_spacing = sum(data['distance_data'][i+1] - data['distance_data'][i] for i in range(len(data['distance_data'])-1)) / (len(data['distance_data'])-1)
        print(f"  Avg distance between points: {avg_dist_spacing:.1f}m")
    
    print()

print("="*80)
print("NEXT: REVERSE-ENGINEER STRAVA'S ALGORITHM")
print("="*80)
print()
print("Now that we have the raw altitude data, we can:")
print("1. Test different smoothing algorithms on Strava's actual data")
print("2. Analyze which combination of smoothing/thresholds reproduces Strava's results")
print("3. Apply those exact parameters to our Fitbit TCX data")
print()
print("Run: python reverse_engineer_strava.py")

