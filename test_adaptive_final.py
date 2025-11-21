#!/usr/bin/env python3
"""Test the final adaptive threshold implementation."""
import re

def elevation_gain_from_tcx_adaptive(xml_text: str) -> float:
    """Calculate elevation using NET gain with adaptive threshold."""
    try:
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        
        if not alts or len(alts) < 2:
            return 0.0
        
        # Smooth with window=30
        window_size = 30
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Adaptive threshold
        alt_range = max(alts) - min(alts)
        if alt_range < 50:
            threshold_meters = 8.0
        elif alt_range < 100:
            threshold_meters = 12.0
        else:
            threshold_meters = 15.0
        
        # Track climbs - NET method
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

# Test all cases
test_cases = [
    ('tcx_2025-11-09.xml', 264.0, '42.2 mi - flat'),
    ('tcx_2025-11-16.xml', 224.0, '7.4 mi - moderate'),
    ('tcx_2025-10-04.xml', 1147.0, '11.76 mi - very hilly'),
    ('tcx_2025-10-02.xml', 465.0, '2.14 mi - very hilly'),
]

print("="*80)
print("FINAL ADAPTIVE THRESHOLD IMPLEMENTATION")
print("="*80)

errors = []
for filename, target, desc in test_cases:
    with open(filename, 'r', encoding='utf-8') as f:
        tcx = f.read()
    
    elev_m = elevation_gain_from_tcx_adaptive(tcx)
    result = elev_m * 3.28084
    error = ((result - target) / target) * 100
    errors.append(abs(error))
    
    # Get altitude range to show threshold used
    alts = [float(x) for x in re.findall(
        r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", tcx)]
    alt_range = max(alts) - min(alts)
    
    if alt_range < 50:
        threshold = 8.0
    elif alt_range < 100:
        threshold = 12.0
    else:
        threshold = 15.0
    
    print(f"\n{desc}")
    print(f"  Altitude range: {alt_range:.1f}m -> Using threshold: {threshold:.1f}m")
    print(f"  Calculated: {result:.2f} ft")
    print(f"  Target:     {target:.2f} ft")
    print(f"  Error:      {error:+.1f}%")

avg_error = sum(errors) / len(errors)
print(f"\n{'='*80}")
print(f"Average error: {avg_error:.1f}%")
print(f"\nComparison to previous approaches:")
print(f"  Original algorithm (window=13, thresh=10m): ~45% avg error")
print(f"  Fixed threshold (window=30, thresh=10m): 33.5% avg error")
print(f"  Adaptive threshold (window=30, adaptive): {avg_error:.1f}% avg error")
print(f"\nImprovement: {45 - avg_error:.1f} percentage points better than original!")

