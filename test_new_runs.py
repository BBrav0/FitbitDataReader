#!/usr/bin/env python3
"""Test the algorithm against the new validation runs."""
import requests
import os
from dotenv import load_dotenv
import re

load_dotenv()
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# New test cases from Strava
NEW_TEST_CASES = {
    '2025-10-19': {'distance': 21.58, 'strava_elevation': 450.0, 'desc': 'Long flat/easy'},
    '2025-10-06': {'distance': 7.59, 'strava_elevation': 437.0, 'desc': 'Moderate hills'},
    '2025-11-18': {'distance': 7.09, 'strava_elevation': 714.0, 'desc': 'Hilly'},
}

def elevation_gain_from_tcx(xml_text: str) -> float:
    """Current adaptive algorithm."""
    try:
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        
        if not alts or len(alts) < 2:
            return 0.0
        
        window_size = 30
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Adaptive threshold
        alt_range = max(alts) - min(alts)
        if alt_range < 85:
            threshold_meters = 9.0
        elif alt_range < 100:
            threshold_meters = 10.0
        else:
            threshold_meters = 14.0
        
        total_gain = 0.0
        in_climb = False
        climb_start = smoothed[0]
        climb_peak = smoothed[0]
        prev_alt = smoothed[0]
        
        for alt in smoothed[1:]:
            if alt > prev_alt:
                if not in_climb:
                    in_climb = True
                    climb_start = prev_alt
                    climb_peak = alt
                else:
                    climb_peak = max(climb_peak, alt)
            elif alt < prev_alt:
                if in_climb:
                    climb_gain = climb_peak - climb_start
                    if climb_gain >= threshold_meters:
                        total_gain += climb_gain
                    in_climb = False
            prev_alt = alt
        
        if in_climb:
            climb_gain = climb_peak - climb_start
            if climb_gain >= threshold_meters:
                total_gain += climb_gain
        
        return total_gain
    except Exception:
        return 0.0

print("="*80)
print("DOWNLOADING TCX FILES FOR NEW TEST RUNS")
print("="*80)

headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

for date in NEW_TEST_CASES.keys():
    print(f"\nFetching {date}...")
    
    try:
        url = f"https://api.fitbit.com/1/user/-/activities/date/{date}.json"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"  Error: status {response.status_code}")
            continue
        
        data = response.json()
        activities = data.get('activities', [])
        
        run_activity = None
        for activity in activities:
            if activity.get('activityParentName') == 'Run':
                run_activity = activity
                break
        
        if not run_activity:
            print(f"  No run found")
            continue
        
        log_id = run_activity.get('logId')
        distance = run_activity.get('distance', 0)
        print(f"  Found: {distance:.2f} miles (Log ID: {log_id})")
        
        # Download TCX
        tcx_url = f"https://api.fitbit.com/1/user/-/activities/{log_id}.tcx"
        tcx_response = requests.get(tcx_url, headers=headers, timeout=30)
        
        if tcx_response.status_code != 200:
            print(f"  Error downloading TCX: {tcx_response.status_code}")
            continue
        
        filename = f"tcx_{date}.xml"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(tcx_response.text)
        
        print(f"  Saved to {filename}")
        
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "="*80)
print("TESTING CURRENT ALGORITHM")
print("="*80)

# Test with current algorithm
all_results = []

for date, info in NEW_TEST_CASES.items():
    filename = f"tcx_{date}.xml"
    
    if not os.path.exists(filename):
        print(f"\n{date}: TCX file not available")
        continue
    
    with open(filename, 'r', encoding='utf-8') as f:
        tcx = f.read()
    
    # Get altitude range
    alts = [float(x) for x in re.findall(
        r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", tcx)]
    alt_range = max(alts) - min(alts)
    
    # Determine threshold
    if alt_range < 85:
        thresh = 9.0
    elif alt_range < 100:
        thresh = 10.0
    else:
        thresh = 14.0
    
    elev_m = elevation_gain_from_tcx(tcx)
    result = elev_m * 3.28084
    target = info['strava_elevation']
    error = ((result - target) / target) * 100
    
    print(f"\n{date} - {info['desc']} ({info['distance']:.2f} mi)")
    print(f"  Altitude range: {alt_range:.1f}m -> Threshold: {thresh:.1f}m")
    print(f"  Calculated: {result:.2f} ft")
    print(f"  Strava:     {target:.2f} ft")
    print(f"  Error:      {error:+.1f}%")
    
    all_results.append((date, result, target, abs(error)))

# Combined results with original 4 test cases
print("\n" + "="*80)
print("COMBINED RESULTS (All 7 Test Cases)")
print("="*80)

original_cases = [
    ('2025-11-09', 278.35, 264.0, 5.4),
    ('2025-11-16', 374.48, 224.0, 67.2),
    ('2025-10-04', 1195.31, 1147.0, 4.2),
    ('2025-10-02', 443.41, 465.0, 4.6),
]

all_errors = [e for _, _, _, e in original_cases] + [e for _, _, _, e in all_results]
avg_error = sum(all_errors) / len(all_errors)

print(f"\nOriginal 4 test cases: {sum([e for _, _, _, e in original_cases]) / 4:.1f}% avg error")
print(f"New 3 test cases: {sum([e for _, _, _, e in all_results]) / len(all_results):.1f}% avg error")
print(f"\nCombined average error across all 7 runs: {avg_error:.1f}%")

# Show if validation improves or worsens the result
if avg_error > 20.4:
    print(f"\nValidation reveals algorithm may not be as robust as expected (+{avg_error - 20.4:.1f}% points)")
else:
    print(f"\nValidation confirms algorithm robustness!")

