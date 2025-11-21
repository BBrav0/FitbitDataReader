#!/usr/bin/env python3
"""
Fine-tune elevation algorithm specifically for Strava's data characteristics.
Test various threshold and minimal smoothing approaches.
"""
import json
import sys

# Load Strava streams
try:
    with open('strava_streams.json', 'r') as f:
        strava_data = json.load(f)
except FileNotFoundError:
    print("Error: strava_streams.json not found.")
    sys.exit(1)

def calculate_with_simple_threshold(altitudes, threshold_m=0.0):
    """Simple: sum all positive deltas above threshold."""
    if len(altitudes) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(altitudes) - 1):
        delta = altitudes[i+1] - altitudes[i]
        if delta > threshold_m:
            total += delta
    return total

def calculate_with_min_climb(altitudes, min_climb_m=3.0):
    """
    Group consecutive gains into climbs, only count climbs >= min_climb_m.
    This is what Strava documentation suggests.
    """
    if len(altitudes) < 2:
        return 0.0
    
    total_gain = 0.0
    current_climb = 0.0
    
    for i in range(len(altitudes) - 1):
        delta = altitudes[i+1] - altitudes[i]
        if delta > 0:
            current_climb += delta
        else:
            # Descent - check if we had a significant climb
            if current_climb >= min_climb_m:
                total_gain += current_climb
            current_climb = 0.0
    
    # Don't forget final climb
    if current_climb >= min_climb_m:
        total_gain += current_climb
    
    return total_gain

def calculate_with_min_climb_and_reset(altitudes, min_climb_m=3.0, reset_threshold_m=2.0):
    """
    Track climbs, but only reset if descent exceeds reset_threshold_m.
    Small bumps don't end a climb.
    """
    if len(altitudes) < 2:
        return 0.0
    
    total_gain = 0.0
    climb_start_alt = altitudes[0]
    climb_peak_alt = altitudes[0]
    
    for alt in altitudes[1:]:
        if alt > climb_peak_alt:
            climb_peak_alt = alt
        elif climb_peak_alt - alt >= reset_threshold_m:
            # Significant descent - end climb
            net_gain = climb_peak_alt - climb_start_alt
            if net_gain >= min_climb_m:
                total_gain += net_gain
            climb_start_alt = alt
            climb_peak_alt = alt
    
    # Final climb
    net_gain = climb_peak_alt - climb_start_alt
    if net_gain >= min_climb_m:
        total_gain += net_gain
    
    return total_gain

print("="*80)
print("FINE-TUNING FOR STRAVA'S DATA")
print("="*80)
print()

# Test configurations
test_configs = []

# Method 1: Simple threshold on deltas
for thresh in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    test_configs.append({
        'method': 'simple_threshold',
        'threshold': thresh,
        'name': f'Delta > {thresh}m'
    })

# Method 2: Minimum climb threshold (Strava docs suggest 3m)
for min_climb in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
    test_configs.append({
        'method': 'min_climb',
        'min_climb': min_climb,
        'name': f'Min climb {min_climb}m'
    })

# Method 3: Min climb with reset threshold
for min_climb in [2.5, 3.0, 3.5]:
    for reset in [1.5, 2.0, 2.5]:
        test_configs.append({
            'method': 'min_climb_reset',
            'min_climb': min_climb,
            'reset': reset,
            'name': f'Climb {min_climb}m / Reset {reset}m'
        })

print(f"Testing {len(test_configs)} configurations...")
print()

results = []

for config in test_configs:
    total_error = 0.0
    total_abs_error = 0.0
    count = 0
    per_run_results = {}
    
    for date in sorted(strava_data.keys()):
        data = strava_data[date]
        altitudes = data['altitude_data']
        strava_elev_m = data['strava_elevation_m']
        
        if not altitudes:
            continue
        
        # Calculate using specified method
        if config['method'] == 'simple_threshold':
            calc_m = calculate_with_simple_threshold(altitudes, config['threshold'])
        elif config['method'] == 'min_climb':
            calc_m = calculate_with_min_climb(altitudes, config['min_climb'])
        elif config['method'] == 'min_climb_reset':
            calc_m = calculate_with_min_climb_and_reset(
                altitudes, config['min_climb'], config['reset']
            )
        
        error_m = calc_m - strava_elev_m
        error_pct = (error_m / strava_elev_m * 100) if strava_elev_m > 0 else 0
        
        per_run_results[date] = {
            'calc_m': calc_m,
            'strava_m': strava_elev_m,
            'error_pct': error_pct
        }
        
        total_error += error_pct
        total_abs_error += abs(error_pct)
        count += 1
    
    avg_error = total_error / count if count > 0 else 0
    avg_abs_error = total_abs_error / count if count > 0 else 0
    
    results.append({
        'name': config['name'],
        'config': config,
        'avg_error': avg_error,
        'avg_abs_error': avg_abs_error,
        'per_run': per_run_results
    })

# Sort by average absolute error
results.sort(key=lambda x: x['avg_abs_error'])

print("="*80)
print("TOP 15 CONFIGURATIONS")
print("="*80)
print()

for rank, result in enumerate(results[:15], 1):
    print(f"{rank}. {result['name']}")
    print(f"   Avg error: {result['avg_error']:+.1f}% | Avg abs error: {result['avg_abs_error']:.1f}%")
    
    # Show per-run
    for date in sorted(result['per_run'].keys()):
        r = result['per_run'][date]
        calc_ft = r['calc_m'] * 3.28084
        strava_ft = r['strava_m'] * 3.28084
        print(f"   {date}: {calc_ft:.0f} ft vs {strava_ft:.0f} ft ({r['error_pct']:+.1f}%)")
    print()

print("="*80)
print("ANALYSIS")
print("="*80)
print()
best = results[0]
print(f"Best configuration: {best['name']}")
print(f"Average absolute error: {best['avg_abs_error']:.1f}%")
print()
print("This shows what Strava is doing with their CLEAN, DENSE data.")
print("For our TCX data (noisier, sparser), we'll need different parameters.")
print()
print("Key insight: Strava uses a minimum climb threshold to filter out noise,")
print("not heavy smoothing. Their data is already smooth from device processing.")

