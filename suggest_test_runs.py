#!/usr/bin/env python3
"""Suggest additional runs for testing the algorithm."""
import sqlite3

con = sqlite3.connect('cache.db')
cur = con.cursor()

# Get runs with various characteristics
cur.execute("""
    SELECT date, distance, elev_gain, elev_gain_per_mile
    FROM runs 
    WHERE activity_type = 'Run' AND distance > 0 AND elev_gain IS NOT NULL
    ORDER BY date DESC
""")

runs = cur.fetchall()
con.close()

# Our current test cases
tested = {'2025-11-09', '2025-11-16', '2025-10-04', '2025-10-02'}

print("="*80)
print("SUGGESTED ADDITIONAL TEST RUNS")
print("="*80)
print("\nLooking for diverse runs to validate the algorithm...")

# Categorize runs we haven't tested
flat_runs = []
moderate_runs = []
hilly_runs = []
very_hilly_runs = []

for date, distance, elev_gain, elev_per_mile in runs:
    if date in tested:
        continue
    
    if elev_per_mile is None:
        continue
        
    # Categorize by elevation per mile
    if elev_per_mile < 30:
        flat_runs.append((date, distance, elev_gain, elev_per_mile))
    elif elev_per_mile < 80:
        moderate_runs.append((date, distance, elev_gain, elev_per_mile))
    elif elev_per_mile < 150:
        hilly_runs.append((date, distance, elev_gain, elev_per_mile))
    else:
        very_hilly_runs.append((date, distance, elev_gain, elev_per_mile))

print("\n" + "="*80)
print("RECOMMENDED TEST RUNS (diverse terrain & distances)")
print("="*80)

suggestions = []

# Pick one from each category, preferring different distances
if flat_runs:
    # Pick a medium-long flat run
    flat_runs.sort(key=lambda x: x[1], reverse=True)
    for run in flat_runs:
        if 8 < run[1] < 15:  # Medium long run
            suggestions.append(('Flat/Easy', run))
            break
    if not suggestions:
        suggestions.append(('Flat/Easy', flat_runs[0]))

if moderate_runs:
    # Pick a short-medium moderate run
    moderate_runs.sort(key=lambda x: x[1])
    for run in moderate_runs:
        if 5 < run[1] < 10:
            suggestions.append(('Moderate Hills', run))
            break
    if len(suggestions) == 1:
        suggestions.append(('Moderate Hills', moderate_runs[0]))

if hilly_runs:
    # Pick a medium hilly run
    hilly_runs.sort(key=lambda x: x[1])
    for run in hilly_runs:
        if 6 < run[1] < 12:
            suggestions.append(('Hilly', run))
            break
    if len(suggestions) == 2:
        suggestions.append(('Hilly', hilly_runs[0]))

if very_hilly_runs and len(suggestions) < 4:
    # Pick a short very hilly run
    very_hilly_runs.sort(key=lambda x: x[1])
    for run in very_hilly_runs:
        if run[1] < 8:
            suggestions.append(('Very Hilly', run))
            break
    if len(suggestions) == 3 and very_hilly_runs:
        suggestions.append(('Very Hilly', very_hilly_runs[0]))

# Display suggestions
print("\nHere are 4 diverse runs to check in Strava:")
print()
for i, (category, (date, distance, elev_gain, elev_per_mile)) in enumerate(suggestions, 1):
    print(f"{i}. {date} - {category}")
    print(f"   Distance: {distance:.2f} miles")
    print(f"   Current calc: {elev_gain:.0f} ft ({elev_per_mile:.1f} ft/mile)")
    print()

print("="*80)
print("Please check these runs in Strava and provide their elevation values:")
print(f"  {suggestions[0][1][0]}: ____ ft")
print(f"  {suggestions[1][1][0]}: ____ ft")
print(f"  {suggestions[2][1][0]}: ____ ft")
print(f"  {suggestions[3][1][0]}: ____ ft")
print("="*80)

