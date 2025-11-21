#!/usr/bin/env python3
"""Optimize the adaptive threshold ranges."""
import re

def elevation_with_adaptive_threshold(xml_text: str, range1, thresh1, thresh2, thresh3) -> float:
    """Test different adaptive threshold configurations."""
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
        
        # Adaptive threshold with configurable ranges
        alt_range = max(alts) - min(alts)
        if alt_range < range1:
            threshold_meters = thresh1
        elif alt_range < 100:
            threshold_meters = thresh2
        else:
            threshold_meters = thresh3
        
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

# Load test cases
test_cases = [
    ('tcx_2025-11-09.xml', 264.0, '11-09'),
    ('tcx_2025-11-16.xml', 224.0, '11-16'),
    ('tcx_2025-10-04.xml', 1147.0, '10-04'),
    ('tcx_2025-10-02.xml', 465.0, '10-02'),
]

tcx_data = {}
for filename, target, name in test_cases:
    with open(filename, 'r', encoding='utf-8') as f:
        tcx_data[name] = (f.read(), target)

print("Optimizing adaptive threshold ranges...")
print("="*90)
print(f"{'Range1':>7} {'Thresh1':>8} {'Thresh2':>8} {'Thresh3':>8} | "
      f"{'11-09':>8} {'11-16':>8} {'10-04':>8} {'10-02':>8} | {'Avg%':>7}")
print("="*90)

best_error = float('inf')
best_params = None

# Search for optimal configuration
for range1 in [60, 65, 70, 75, 80, 85, 90]:
    for thresh1 in [7.0, 8.0, 9.0, 10.0]:
        for thresh2 in [10.0, 11.0, 12.0, 13.0]:
            for thresh3 in [13.0, 14.0, 15.0, 16.0]:
                results = []
                errors = []
                
                for name, (tcx, target) in tcx_data.items():
                    elev_m = elevation_with_adaptive_threshold(tcx, range1, thresh1, thresh2, thresh3)
                    result = elev_m * 3.28084
                    error = abs((result - target) / target) * 100
                    results.append(result)
                    errors.append(error)
                
                avg_error = sum(errors) / len(errors)
                
                if avg_error < best_error:
                    best_error = avg_error
                    best_params = (range1, thresh1, thresh2, thresh3)
                    
                    print(f"{range1:>7} {thresh1:>8.1f} {thresh2:>8.1f} {thresh3:>8.1f} | ", end="")
                    for r in results:
                        print(f"{r:>8.1f} ", end="")
                    print(f"| {avg_error:>6.1f}%")

print("="*90)
print(f"\nBest configuration (avg error: {best_error:.1f}%):")
print(f"  if altitude_range < {best_params[0]}m: threshold = {best_params[1]:.1f}m")
print(f"  elif altitude_range < 100m: threshold = {best_params[2]:.1f}m")
print(f"  else: threshold = {best_params[3]:.1f}m")

# Test best configuration
print(f"\nDetailed results with best parameters:")
for name, (tcx, target) in tcx_data.items():
    elev_m = elevation_with_adaptive_threshold(tcx, *best_params)
    result = elev_m * 3.28084
    error = ((result - target) / target) * 100
    
    alts = [float(x) for x in re.findall(
        r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", tcx)]
    alt_range = max(alts) - min(alts)
    
    if alt_range < best_params[0]:
        thresh_used = best_params[1]
    elif alt_range < 100:
        thresh_used = best_params[2]
    else:
        thresh_used = best_params[3]
    
    print(f"  {name}: range={alt_range:.1f}m, thresh={thresh_used:.1f}m -> "
          f"{result:.1f}ft (target:{target:.0f}ft, error:{error:+.1f}%)")

