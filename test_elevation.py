#!/usr/bin/env python3
"""Test script for elevation calculation algorithm.

Downloads TCX files for test dates and compares results against Strava targets.
"""
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
if not ACCESS_TOKEN:
    print("Error: ACCESS_TOKEN not found in .env file")
    sys.exit(1)

# Test cases with Strava targets
# NOTE: Trying 2025 dates since db_filler.py starts from Feb 2025
TEST_CASES = {
    '2025-11-16': {
        'distance_miles': 4.62,
        'strava_elevation_ft': 224
    },
    '2025-11-09': {
        'distance_miles': 26.19,
        'strava_elevation_ft': 264
    }
}

def download_tcx_for_date(date_str, access_token):
    """Download TCX file for a specific date."""
    print(f"\nSearching for activity on {date_str}...")
    
    # Get activities for the date
    url = f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"  Error: API returned status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
            
        data = response.json()
        activities = data.get('activities', [])
        print(f"  Found {len(activities)} activities")
        
        # Find run activity
        run_activity = None
        for activity in activities:
            activity_type = activity.get('activityParentName')
            print(f"    Activity: {activity_type}, distance: {activity.get('distance', 0)} mi")
            if activity_type in ['Run', 'Treadmill run']:
                run_activity = activity
                break
        
        if not run_activity:
            print(f"  No run activity found on {date_str}")
            return None
        
        log_id = run_activity.get('logId')
        distance = run_activity.get('distance', 0)
        print(f"  Found run: {distance:.2f} miles (Log ID: {log_id})")
        
        # Download TCX
        tcx_url = f"https://api.fitbit.com/1/user/-/activities/{log_id}.tcx"
        tcx_response = requests.get(tcx_url, headers=headers, timeout=30)
        
        if tcx_response.status_code != 200:
            print(f"  Error: Could not download TCX (status {tcx_response.status_code})")
            return None
        
        tcx_content = tcx_response.text
        
        # Save to file
        filename = f"tcx_{date_str}.xml"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(tcx_content)
        
        print(f"  Saved to {filename}")
        return tcx_content
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

def elevation_gain_from_tcx(xml_text: str, params=None) -> float:
    """Calculate elevation gain from TCX content using configurable parameters.
    
    Args:
        xml_text: TCX XML content
        params: Dict with 'window_size', 'min_delta', 'threshold_meters', 'reset_threshold'
    
    Returns:
        Elevation gain in meters.
    """
    if params is None:
        params = {
            'window_size': 13,
            'min_delta': 0.22,
            'threshold_meters': 10.0,
            'reset_threshold': -0.8
        }
    
    try:
        # Extract all altitude values from TCX
        alts = [float(x) for x in re.findall(r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", xml_text or "")]
        if not alts or len(alts) < 2:
            return 0.0
        
        # Apply smoothing
        window_size = params['window_size']
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Filter and calculate gain
        min_delta = params['min_delta']
        threshold_meters = params['threshold_meters']
        reset_threshold = params['reset_threshold']
        
        total_gain = 0.0
        current_climb_gain = 0.0
        current_climb_start = smoothed[0]
        prev_alt = smoothed[0]
        
        for alt in smoothed[1:]:
            delta = alt - prev_alt
            
            if abs(delta) > min_delta:
                if delta > 0:
                    current_climb_gain += delta
                elif delta < 0:
                    net_from_start = alt - current_climb_start
                    
                    if net_from_start < reset_threshold:
                        if current_climb_gain >= threshold_meters:
                            total_gain += current_climb_gain
                        
                        current_climb_gain = 0.0
                        current_climb_start = alt
            
            prev_alt = alt
        
        # Check final climb
        if current_climb_gain >= threshold_meters:
            total_gain += current_climb_gain
        
        return total_gain
    except Exception as e:
        print(f"  Error in elevation calculation: {e}")
        return 0.0

def test_elevation_algorithm(tcx_content, date_str, params=None):
    """Test the elevation algorithm on TCX content."""
    target = TEST_CASES[date_str]
    
    # Calculate elevation in meters, convert to feet
    elev_m = elevation_gain_from_tcx(tcx_content, params)
    elev_ft = elev_m * 3.28084
    
    target_ft = target['strava_elevation_ft']
    error_ft = elev_ft - target_ft
    error_pct = (error_ft / target_ft) * 100 if target_ft > 0 else 0
    
    return {
        'date': date_str,
        'distance_miles': target['distance_miles'],
        'calculated_ft': elev_ft,
        'target_ft': target_ft,
        'error_ft': error_ft,
        'error_pct': error_pct
    }

def print_results(results_list):
    """Print test results in a formatted table."""
    print("\n" + "="*80)
    print("ELEVATION CALCULATION RESULTS")
    print("="*80)
    
    for result in results_list:
        print(f"\n{result['date']} ({result['distance_miles']:.2f} miles)")
        print(f"  Calculated: {result['calculated_ft']:.2f} ft")
        print(f"  Target:     {result['target_ft']:.2f} ft")
        print(f"  Error:      {result['error_ft']:+.2f} ft ({result['error_pct']:+.1f}%)")
    
    print("\n" + "="*80)

def main():
    """Main test function."""
    print("="*80)
    print("ELEVATION CALCULATION TEST")
    print("="*80)
    
    # Download or load TCX files
    tcx_data = {}
    for date_str in TEST_CASES.keys():
        filename = f"tcx_{date_str}.xml"
        
        # Check if file already exists
        if os.path.exists(filename):
            print(f"\nLoading existing {filename}...")
            with open(filename, 'r', encoding='utf-8') as f:
                tcx_data[date_str] = f.read()
        else:
            # Download from API
            tcx_content = download_tcx_for_date(date_str, ACCESS_TOKEN)
            if tcx_content:
                tcx_data[date_str] = tcx_content
            else:
                print(f"  Failed to download TCX for {date_str}")
    
    if not tcx_data:
        print("\nError: No TCX data available for testing")
        return
    
    # Test with current algorithm
    print("\n" + "="*80)
    print("TESTING WITH CURRENT ALGORITHM")
    print("="*80)
    
    results = []
    for date_str, tcx_content in tcx_data.items():
        result = test_elevation_algorithm(tcx_content, date_str)
        results.append(result)
    
    print_results(results)
    
    # Analyze TCX data
    print("\n" + "="*80)
    print("TCX DATA ANALYSIS")
    print("="*80)
    
    for date_str, tcx_content in tcx_data.items():
        alts = [float(x) for x in re.findall(r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", tcx_content)]
        if alts:
            print(f"\n{date_str}:")
            print(f"  Data points: {len(alts)}")
            print(f"  Min altitude: {min(alts):.1f}m")
            print(f"  Max altitude: {max(alts):.1f}m")
            print(f"  Altitude range: {max(alts) - min(alts):.1f}m")

if __name__ == '__main__':
    main()

