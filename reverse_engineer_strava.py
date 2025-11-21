#!/usr/bin/env python3
"""
Reverse-engineer Strava's elevation algorithm by testing parameters on their actual data.
"""
import json
import sys

# Load Strava streams
try:
    with open('strava_streams.json', 'r') as f:
        strava_data = json.load(f)
except FileNotFoundError:
    print("Error: strava_streams.json not found. Run strava_detailed_analysis.py first.")
    sys.exit(1)

def calculate_elevation_gain(altitudes, window_size=1, threshold_m=0.0, use_net_method=True):
    """
    Calculate elevation gain with configurable parameters.
    
    Args:
        altitudes: List of altitude values in meters
        window_size: Smoothing window size (1 = no smoothing)
        threshold_m: Minimum climb threshold in meters
        use_net_method: If True, use net elevation method (peak - start)
    """
    if not altitudes or len(altitudes) < 2:
        return 0.0
    
    # Apply smoothing if requested
    if window_size > 1:
        smoothed = []
        for i in range(len(altitudes)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(altitudes), i + window_size // 2 + 1)
            window = altitudes[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        altitudes = smoothed
    
    if use_net_method:
        # NET elevation method (what we're currently using)
        total_gain = 0.0
        current_climb_start_alt = altitudes[0]
        current_climb_peak_alt = altitudes[0]
        
        for alt in altitudes[1:]:
            if alt > current_climb_peak_alt:
                current_climb_peak_alt = alt
            elif alt < current_climb_start_alt:
                net_climb_gain = current_climb_peak_alt - current_climb_start_alt
                if net_climb_gain >= threshold_m:
                    total_gain += net_climb_gain
                current_climb_start_alt = alt
                current_climb_peak_alt = alt
        
        # Final climb
        net_climb_gain = current_climb_peak_alt - current_climb_start_alt
        if net_climb_gain >= threshold_m:
            total_gain += net_climb_gain
        
        return total_gain
    else:
        # Simple delta method
        total_gain = 0.0
        for i in range(len(altitudes) - 1):
            delta = altitudes[i+1] - altitudes[i]
            if delta > threshold_m:
                total_gain += delta
        return total_gain

print("="*80)
print("REVERSE-ENGINEERING STRAVA'S ELEVATION ALGORITHM")
print("="*80)
print()

# Test different parameter combinations
test_configs = [
    # No smoothing, various thresholds
    {'window': 1, 'threshold': 0.0, 'net': False, 'name': 'Raw (no filter)'},
    {'window': 1, 'threshold': 1.0, 'net': False, 'name': 'No smooth, 1m thresh'},
    {'window': 1, 'threshold': 2.0, 'net': False, 'name': 'No smooth, 2m thresh'},
    
    # Light smoothing
    {'window': 5, 'threshold': 1.0, 'net': False, 'name': 'Smooth-5, 1m thresh'},
    {'window': 10, 'threshold': 1.0, 'net': False, 'name': 'Smooth-10, 1m thresh'},
    
    # Our current method (NET)
    {'window': 30, 'threshold': 9.0, 'net': True, 'name': 'Our current (flat)'},
    {'window': 30, 'threshold': 14.0, 'net': True, 'name': 'Our current (hilly)'},
    
    # Try NET method with minimal smoothing (since Strava data is already clean)
    {'window': 5, 'threshold': 2.0, 'net': True, 'name': 'NET smooth-5, 2m'},
    {'window': 10, 'threshold': 2.0, 'net': True, 'name': 'NET smooth-10, 2m'},
    {'window': 15, 'threshold': 2.0, 'net': True, 'name': 'NET smooth-15, 2m'},
    {'window': 20, 'threshold': 2.0, 'net': True, 'name': 'NET smooth-20, 2m'},
]

print(f"Testing {len(test_configs)} configurations...")
print()

results = {}

for config in test_configs:
    config_name = config['name']
    results[config_name] = {}
    
    total_error = 0.0
    total_abs_error = 0.0
    count = 0
    
    for date in sorted(strava_data.keys()):
        data = strava_data[date]
        altitudes = data['altitude_data']
        strava_elev_m = data['strava_elevation_m']
        
        if not altitudes:
            continue
        
        calculated_m = calculate_elevation_gain(
            altitudes,
            window_size=config['window'],
            threshold_m=config['threshold'],
            use_net_method=config['net']
        )
        
        error_m = calculated_m - strava_elev_m
        error_pct = (error_m / strava_elev_m * 100) if strava_elev_m > 0 else 0
        
        results[config_name][date] = {
            'calculated_m': calculated_m,
            'strava_m': strava_elev_m,
            'error_m': error_m,
            'error_pct': error_pct
        }
        
        total_error += error_pct
        total_abs_error += abs(error_pct)
        count += 1
    
    avg_error = total_error / count if count > 0 else 0
    avg_abs_error = total_abs_error / count if count > 0 else 0
    
    results[config_name]['avg_error'] = avg_error
    results[config_name]['avg_abs_error'] = avg_abs_error

print("="*80)
print("RESULTS RANKED BY AVERAGE ABSOLUTE ERROR")
print("="*80)
print()

# Sort by average absolute error
sorted_configs = sorted(
    [(name, data['avg_abs_error']) for name, data in results.items()],
    key=lambda x: x[1]
)

for rank, (config_name, avg_abs_err) in enumerate(sorted_configs[:10], 1):
    config_results = results[config_name]
    avg_err = config_results['avg_error']
    
    print(f"{rank}. {config_name}")
    print(f"   Avg error: {avg_err:+.1f}% | Avg abs error: {avg_abs_err:.1f}%")
    
    # Show per-run results
    for date in sorted(strava_data.keys()):
        if date in config_results and date != 'avg_error' and date != 'avg_abs_error':
            r = config_results[date]
            calc_ft = r['calculated_m'] * 3.28084
            strava_ft = r['strava_m'] * 3.28084
            print(f"   {date}: {calc_ft:.0f} ft vs {strava_ft:.0f} ft ({r['error_pct']:+.1f}%)")
    print()

print("="*80)
print("DETAILED ANALYSIS OF BEST CONFIGURATION")
print("="*80)
print()

best_config_name = sorted_configs[0][0]
best_results = results[best_config_name]

print(f"Best: {best_config_name}")
print(f"Average absolute error: {best_results['avg_abs_error']:.1f}%")
print()

# Compare to our current algorithm's performance
print("="*80)
print("COMPARISON TO OUR CURRENT ALGORITHM")
print("="*80)
print()
print("Our current algorithm (adaptive thresholds) achieved ~21% avg error on TCX data.")
print("This test shows what's possible with Strava's cleaner, denser data.")
print()
print("Key differences between Strava streams and TCX data:")
print("  - Strava: ~1 point/second, very clean GPS")
print("  - TCX: Sparser data (~1 point/5-10 seconds), noisier GPS")
print()
print("Next steps:")
print("  1. The best parameters here may not work for TCX (different data density/quality)")
print("  2. We should test if reducing smoothing window helps (since we're over-smoothing)")
print("  3. Consider adjusting thresholds based on data point density")

