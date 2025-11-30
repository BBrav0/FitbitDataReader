#!/usr/bin/env python3
"""
Download all TCX files from Fitbit for historical runs.
This script uses the same Fitbit API authentication as db_filler.py
to retrieve and save TCX files for all your past runs.
"""

import os
import sys
from pathlib import Path
from datetime import date, timedelta, datetime
import requests
import time
from dotenv import load_dotenv, find_dotenv
import traceback

# Load environment variables (same as get_tokens.py)
dotenv_path = find_dotenv()
if not dotenv_path:
    print("ERROR: .env file not found!")
    print("Please make sure you have a .env file in the project directory.")
    sys.exit(1)
load_dotenv(dotenv_path)

# Fitbit API credentials (same as db_filler.py)
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')

# Output directory for TCX files
OUTPUT_DIR = Path("fitbit_tcx_files")
OUTPUT_DIR.mkdir(exist_ok=True)

def get_activities_for_date(date_obj, access_token):
    """
    Get activities for a specific date using direct API call.
    This bypasses the buggy fitbit library.
    
    Args:
        date_obj: Date object
        access_token: Fitbit OAuth access token
    
    Returns:
        Dictionary with activities data, or None if error
    """
    date_str = date_obj.strftime("%Y-%m-%d")
    url = f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json"
    
    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            # Debug: print the actual response
            print(f"DEBUG - 401 Response: {response.text[:200]}")
            return {'error': f'Authentication failed (401) - {response.text[:100]}'}
        elif response.status_code == 429:
            return {'error': 'Rate limit exceeded'}
        else:
            return {'error': f'HTTP {response.status_code}: {response.text[:200]}'}
            
    except Exception as e:
        return {'error': str(e)}

def download_tcx(log_id, activity_date, activity_name, access_token):
    """
    Download a single TCX file from Fitbit.
    
    Args:
        log_id: Fitbit activity log ID
        activity_date: Date of the activity (for filename)
        activity_name: Name/type of activity (for filename)
        access_token: Fitbit OAuth access token
    
    Returns:
        True if successful, False otherwise
    """
    tcx_url = f"https://api.fitbit.com/1/user/-/activities/{log_id}.tcx"
    
    try:
        response = requests.get(
            tcx_url,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=30
        )
        
        if response.status_code == 200:
            # Create filename with date and activity type
            safe_name = activity_name.replace(' ', '_').replace('/', '_')
            filename = f"{activity_date}_{safe_name}_{log_id}.tcx"
            filepath = OUTPUT_DIR / filename
            
            # Save TCX file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"  ✓ Downloaded: {filename} ({len(response.text)} bytes)")
            return True
        else:
            print(f"  ✗ Failed to download (status {response.status_code})")
            return False
            
    except Exception as e:
        print(f"  ✗ Error downloading: {e}")
        return False

def main():
    """Main function to download all historical TCX files."""
    print("Fitbit TCX Downloader [OPTIMIZED - Known Dates Only]")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print()
    
    # Verify credentials are loaded
    if not ACCESS_TOKEN:
        print("ERROR: ACCESS_TOKEN not found in .env file!")
        return
    
    # Hardcoded dates from runs_data.csv (starting from 2025-07-04)
    # Only checking dates that have runs to save API calls
    # Already downloaded: 2025-02-23 through 2025-06-30
    # Skipped treadmill: 2025-07-02
    run_dates = [
        "2025-07-04", "2025-07-07", "2025-07-09", "2025-07-21", "2025-07-23", "2025-07-24",
        "2025-07-26", "2025-07-28", "2025-07-30", "2025-07-31", "2025-08-02", "2025-08-04",
        "2025-08-06", "2025-08-07", "2025-08-09", "2025-08-11", "2025-08-13", "2025-08-14",
        "2025-08-16", "2025-08-21", "2025-08-23", "2025-08-24", "2025-08-27"
    ]
    
    dates_to_check = [datetime.strptime(d, "%Y-%m-%d").date() for d in run_dates]
    
    print(f"\nChecking {len(dates_to_check)} dates with known runs (from runs_data.csv)")
    print(f"Date range: {run_dates[0]} to {run_dates[-1]}")
    print("-" * 60)
    
    # Track statistics
    total_runs = 0
    successful_downloads = 0
    failed_downloads = 0
    api_requests = 0
    
    # Iterate through known run dates
    total_days = len(dates_to_check)
    days_processed = 0
    
    for current_date in dates_to_check:
        date_str = current_date.strftime("%Y-%m-%d")
        days_processed += 1
        
        # Show progress
        print(f"[{days_processed}/{total_days}] Checking {date_str}...", end=' ', flush=True)
        
        try:
            # Add delay between requests to respect rate limits (0.5s = ~120 requests/min)
            if api_requests > 0:
                time.sleep(0.5)
            
            # Fetch activities for this date using direct API call
            daily_activities = get_activities_for_date(current_date, ACCESS_TOKEN)
            api_requests += 1
            
            # Check for errors in response
            if daily_activities and 'error' in daily_activities:
                error_msg = daily_activities['error']
                if 'Authentication' in error_msg or 'token' in error_msg.lower():
                    print("AUTH ERROR!")
                    print("\n" + "!" * 60)
                    print("AUTHENTICATION ERROR")
                    print(f"Error: {error_msg}")
                    print("Your Fitbit tokens may have expired.")
                    print("Please run db_filler.py to refresh your tokens.")
                    print("!" * 60)
                    return
                elif 'Rate limit' in error_msg:
                    print("RATE LIMIT - waiting 100s...")
                    time.sleep(100)
                    continue
                else:
                    print(f"ERROR - {error_msg}")
                    continue
            
            # Get activities list (use .get() to safely handle missing key)
            activities = daily_activities.get('activities', []) if daily_activities else []
            
            # Filter for runs (both outdoor and treadmill) - use activityParentName like db_filler.py
            runs = [
                activity for activity in activities
                if activity.get('activityParentName') in ['Run', 'Treadmill run']
            ]
            
            if runs:
                print(f"Found {len(runs)} run(s)!")
                
                for activity in runs:
                    total_runs += 1
                    log_id = activity.get('logId')
                    activity_type = activity.get('activityParentName', 'Run')
                    distance = activity.get('distance', 0)
                    
                    print(f"  {activity_type} - {distance:.2f} miles (Log ID: {log_id})")
                    
                    if log_id:
                        # Only download outdoor runs (treadmill runs don't have GPS/TCX)
                        if activity_type == 'Run':
                            if download_tcx(log_id, date_str, activity_type, ACCESS_TOKEN):
                                successful_downloads += 1
                            else:
                                failed_downloads += 1
                            
                            # Rate limiting: sleep briefly between downloads
                            time.sleep(1)
                        else:
                            print(f"  ⊘ Skipped: {activity_type} (no GPS data)")
            else:
                # No runs found for this date
                print("No runs")
            
            # Periodic progress summary
            if days_processed % 15 == 0:
                print(f"\n--- Progress: {days_processed}/{total_days} dates checked, {total_runs} runs found, {successful_downloads} TCX downloaded ---\n")
            
        except requests.exceptions.Timeout:
            print("TIMEOUT - retrying in 5s...")
            time.sleep(5)
            continue
            
        except requests.exceptions.RequestException as e:
            print(f"NETWORK ERROR - {e}")
            print("  Waiting 30s...")
            time.sleep(30)
            # Don't move to next date - retry the same date
            continue
            
        except Exception as e:
            error_msg = str(e).lower()
            error_type = type(e).__name__
            
            # Check for rate limit errors
            is_rate_limit = (
                'retry-after' in error_msg or 
                'rate limit' in error_msg or 
                '429' in error_msg or
                'too many requests' in error_msg or
                'httptoomany' in error_type.lower()
            )
            
            if is_rate_limit:
                print(f"RATE LIMIT - waiting 100s...")
                time.sleep(100)
                # Don't move to next date - retry the same date
                continue
            
            # Handle token/auth errors
            elif 'token' in error_msg or 'auth' in error_msg or 'unauthorized' in error_msg:
                print(f"AUTH ERROR - {e}")
                print("\n" + "!" * 60)
                print("AUTHENTICATION ERROR")
                print("Your Fitbit tokens may have expired.")
                print("Please run db_filler.py to refresh your tokens.")
                print("!" * 60)
                return
            else:
                print(f"ERROR - {error_type}: {e}")
                # Continue to next date
                continue
    
    # Print summary
    print("\n" + "=" * 60)
    print("Download Summary:")
    print(f"  Total runs found: {total_runs}")
    print(f"  TCX files downloaded: {successful_downloads}")
    print(f"  Failed downloads: {failed_downloads}")
    print(f"  API requests made: {api_requests}")
    print(f"\nFiles saved to: {OUTPUT_DIR.absolute()}")
    print("=" * 60)

if __name__ == "__main__":
    main()
