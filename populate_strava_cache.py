#!/usr/bin/env python3
"""
Populate the Strava activities cache from existing strava_activities.json.
This avoids unnecessary API calls.
"""
import json

# Load existing Strava data
with open('strava_activities.json', 'r') as f:
    strava_activities = json.load(f)

# Convert to cache format (keyed by date)
cache = {}

for date_str, info in strava_activities.items():
    cache[date_str] = {
        'start_date_local': f'{date_str}T12:00:00Z',
        'elevation_ft': info['elevation_ft'],
        'elevation_m': info['elevation_m'],
        'activity_id': info['id']
    }

# Save cache
with open('strava_activities_cache.json', 'w') as f:
    json.dump(cache, f, indent=2)

print(f"Strava cache populated with {len(cache)} activities")

