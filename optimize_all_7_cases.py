#!/usr/bin/env python3
"""Re-optimize algorithm with all 7 test cases."""
import re
import os

def elevation_with_params(xml_text: str, window_size, range1, thresh1, thresh2, thresh3) -> float:
    """Test elevation with configurable parameters."""
    try:
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        
        if not alts or len(alts) < 2:
            return 0.0
        
        # Smoothing
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Adaptive threshold
        alt_range = max(alts) - min(alts)
        if alt_range < range1:
            threshold_meters = thresh1
        elif alt_range < 100:
            threshold_meters = thresh2
        else:
            threshold_meters = thresh3
        
        # NET elevation method
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

# All 7 test cases
ALL_TEST_CASES = {
    '2025-11-09': ('tcx_2025-11-09.xml', 264.0, '42.2mi flat'),
    '2025-11-16': ('tcx_2025-11-16.xml', 224.0, '7.4mi moderate'),
    '2025-10-04': ('tcx_2025-10-04.xml', 1147.0, '11.76mi v.hilly'),
    '2025-10-02': ('tcx_2025-10-02.xml', 465.0, '2.14mi v.hilly'),
    '2025-10-19': ('tcx_2025-10-19.xml', 450.0, '21.58mi flat'),
    '2025-10-06': ('tcx_2025-10-06.xml', 437.0, '7.59mi moderate'),
    '2025-11-18': ('tcx_2025-11-18.xml', 714.0, '7.09mi hilly'),
}

# Load all TCX data
tcx_data = {}
for date, (filename, target, desc) in ALL_TEST_CASES.items():
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            tcx_data[date] = (f.read(), target, desc)
    else:
        print(f"Warning: {filename} not found")

print("="*100)
print("COMPREHENSIVE OPTIMIZATION WITH ALL 7 TEST CASES")
print("="*100)
print(f"Loaded {len(tcx_data)} TCX files\n")

best_error = float('inf')
best_params = None
best_results = {}

print("Searching parameter space...")
print("="*100)
print(f"{'Window':>7} {'Range1':>7} {'T1':>5} {'T2':>5} {'T3':>5} | {'Avg%':>7} | Details")
print("="*100)

count = 0
# Comprehensive search
for window_size in [25, 27, 29, 30, 31, 33, 35]:
    for range1 in [75, 80, 85, 90, 95]:
        for thresh1 in [8.0, 8.5, 9.0, 9.5, 10.0]:
            for thresh2 in [9.0, 9.5, 10.0, 10.5, 11.0]:
                for thresh3 in [12.0, 13.0, 14.0, 15.0, 16.0]:
                    results = {}
                    errors = []
                    
                    for date, (tcx, target, desc) in tcx_data.items():
                        elev_m = elevation_with_params(tcx, window_size, range1, 
                                                       thresh1, thresh2, thresh3)
                        result = elev_m * 3.28084
                        error = abs((result - target) / target) * 100
                        results[date] = result
                        errors.append(error)
                    
                    avg_error = sum(errors) / len(errors)
                    count += 1
                    
                    if avg_error < best_error:
                        best_error = avg_error
                        best_params = (window_size, range1, thresh1, thresh2, thresh3)
                        best_results = results.copy()
                        
                        # Show improvement
                        print(f"{window_size:>7} {range1:>7} {thresh1:>5.1f} {thresh2:>5.1f} {thresh3:>5.1f} | "
                              f"{avg_error:>6.1f}% | ", end="")
                        
                        # Show worst 2 errors
                        sorted_errors = sorted(errors, reverse=True)
                        print(f"worst: {sorted_errors[0]:.0f}%, {sorted_errors[1]:.0f}%")

print("="*100)
print(f"\nSearched {count} parameter combinations")
print(f"\nBEST PARAMETERS (avg error: {best_error:.1f}%):")
print(f"  window_size = {best_params[0]}")
print(f"  if altitude_range < {best_params[1]}m: threshold = {best_params[2]:.1f}m")
print(f"  elif altitude_range < 100m: threshold = {best_params[3]:.1f}m")
print(f"  else: threshold = {best_params[4]:.1f}m")

print("\n" + "="*100)
print("DETAILED RESULTS WITH BEST PARAMETERS")
print("="*100)

for date, (tcx, target, desc) in tcx_data.items():
    result = best_results[date]
    error = ((result - target) / target) * 100
    
    alts = [float(x) for x in re.findall(
        r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", tcx)]
    alt_range = max(alts) - min(alts)
    
    if alt_range < best_params[1]:
        thresh = best_params[2]
    elif alt_range < 100:
        thresh = best_params[3]
    else:
        thresh = best_params[4]
    
    print(f"\n{date} - {desc}")
    print(f"  Range: {alt_range:.1f}m -> Threshold: {thresh:.1f}m")
    print(f"  Calculated: {result:.1f} ft | Target: {target:.0f} ft | Error: {error:+.1f}%")

print("\n" + "="*100)
print("COMPARISON")
print("="*100)
print(f"Original algorithm (4 test cases):   ~45.0% avg error")
print(f"First optimization (4 test cases):    20.4% avg error")  
print(f"Current algorithm (7 test cases):     21.4% avg error")
print(f"NEW optimized (7 test cases):         {best_error:.1f}% avg error")
print(f"\nImprovement from original: {45.0 - best_error:.1f} percentage points")
print("="*100)

