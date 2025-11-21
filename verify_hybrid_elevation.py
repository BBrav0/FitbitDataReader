#!/usr/bin/env python3
"""Verify that Strava elevations are being used correctly in the database."""
import sqlite3

conn = sqlite3.connect('cache.db')
cursor = conn.cursor()

# Our Strava-cached runs
strava_runs = {
    '2025-11-16': 224,
    '2025-11-09': 264,
    '2025-10-04': 1147,
    '2025-10-02': 172,
    '2025-10-19': 450,
    '2025-10-06': 437,
    '2025-11-18': 714,
}

print("="*80)
print("VERIFYING HYBRID STRAVA + ALGORITHM APPROACH")
print("="*80)
print()

print("STRAVA RUNS (should match perfectly):")
print("-" * 80)

strava_matched = 0
for date, expected in sorted(strava_runs.items()):
    cursor.execute("SELECT elev_gain FROM runs WHERE date = ?", (date,))
    result = cursor.fetchone()
    
    if result and result[0] is not None:
        actual = result[0]
        error = abs(actual - expected)
        
        if error < 5:
            print(f"{date}: {actual:.0f} ft = {expected:.0f} ft ✓ PERFECT")
            strava_matched += 1
        else:
            print(f"{date}: {actual:.0f} ft vs {expected:.0f} ft ✗ ERROR ({error:.0f} ft off)")
    else:
        print(f"{date}: NOT FOUND in database")

print()
print(f"Strava runs matched: {strava_matched}/7")

# Check a few non-Strava runs to see algorithm is working
print()
print("ALGORITHM RUNS (sample - will have ~50% error):")
print("-" * 80)

cursor.execute("""
    SELECT date, elev_gain 
    FROM runs 
    WHERE date NOT IN (?,?,?,?,?,?,?) 
    AND elev_gain IS NOT NULL 
    AND elev_gain > 0
    LIMIT 5
""", tuple(strava_runs.keys()))

algorithm_runs = cursor.fetchall()
for date, elev in algorithm_runs:
    print(f"{date}: {elev:.0f} ft (calculated from TCX)")

conn.close()

print()
print("="*80)
print("SUMMARY")
print("="*80)

if strava_matched == 7:
    print("SUCCESS! All 7 Strava runs match perfectly!")
    print("Hybrid approach is working correctly.")
    print()
    print("Results:")
    print("  - Strava runs: 0% error (perfect match)")
    print("  - Other runs: ~50% error (algorithm)")
    print("  - Overall: Much better than before!")
elif strava_matched > 0:
    print(f"PARTIAL: {strava_matched}/7 Strava runs match.")
    print(f"Check the {7 - strava_matched} mismatched runs.")
else:
    print("ERROR: No Strava runs matched!")
    print("The hybrid approach may not be working.")
    print("Check strava_activities_cache.json exists and has correct data.")

