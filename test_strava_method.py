#!/usr/bin/env python3
"""
Test alternative interpretations of Strava's method based on documentation.

Key quote from docs: "We smooth the data before calculating gain and depending 
on the resulting data, elevation changes may not be enough to pass a threshold 
that we use for determining whether or not you have gained elevation."

This suggests they might:
1. Apply threshold differently (not just climb height, but each delta?)
2. Filter based on climb characteristics (steepness, duration)
3. Have adaptive thresholds
"""
import re

def method_1_strict_threshold(xml_text: str, window_size=30, threshold_meters=10.0) -> float:
    """
    Only count climbs where EVERY positive delta exceeds a minimum.
    This would filter out gradual GPS drift.
    """
    try:
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        if not alts or len(alts) < 2:
            return 0.0
        
        # Smooth
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Track climbs - sum ONLY positive deltas that exceed threshold
        total_gain = 0.0
        prev_alt = smoothed[0]
        
        for alt in smoothed[1:]:
            delta = alt - prev_alt
            # Only count positive changes that exceed threshold
            if delta >= threshold_meters:
                total_gain += delta
            prev_alt = alt
        
        return total_gain
    except Exception:
        return 0.0

def method_2_reset_on_descent(xml_text: str, window_size=30, 
                               threshold_meters=10.0, reset_meters=5.0) -> float:
    """
    Track climbs but reset if descend by reset_meters from peak.
    This merges nearby climbs and filters GPS noise.
    """
    try:
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        if not alts or len(alts) < 2:
            return 0.0
        
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
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
            elif alt < prev_alt and in_climb:
                # Check if descended significantly from peak
                descent_from_peak = climb_peak - alt
                
                if descent_from_peak >= reset_meters:
                    # End climb
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

def method_3_adaptive_threshold(xml_text: str, window_size=30) -> float:
    """
    Use adaptive threshold based on run length/altitude range.
    Longer runs or bigger ranges might need higher thresholds.
    """
    try:
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        if not alts or len(alts) < 2:
            return 0.0
        
        # Calculate adaptive threshold
        alt_range = max(alts) - min(alts)
        # For low range (flat), use lower threshold
        # For high range (hilly), use higher threshold
        if alt_range < 50:  # Very flat
            threshold_meters = 8.0
        elif alt_range < 100:  # Moderate
            threshold_meters = 12.0
        else:  # Very hilly
            threshold_meters = 15.0
        
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
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

# Test all methods
test_cases = [
    ('tcx_2025-11-09.xml', 264.0, '42.2 mi - flat'),
    ('tcx_2025-11-16.xml', 224.0, '7.4 mi - moderate'),
    ('tcx_2025-10-04.xml', 1147.0, '11.76 mi - very hilly'),
    ('tcx_2025-10-02.xml', 465.0, '2.14 mi - very hilly'),
]

print("="*100)
print("TESTING ALTERNATIVE STRAVA METHODS")
print("="*100)

methods = [
    ("Current (NET, window=30, thresh=10m)", lambda tcx: method_2_reset_on_descent(tcx, 30, 10.0, 3.0)),
    ("Method 1: Strict threshold per delta", lambda tcx: method_1_strict_threshold(tcx, 30, 10.0)),
    ("Method 2: Reset on 5m descent", lambda tcx: method_2_reset_on_descent(tcx, 30, 10.0, 5.0)),
    ("Method 2: Reset on 8m descent", lambda tcx: method_2_reset_on_descent(tcx, 30, 10.0, 8.0)),
    ("Method 3: Adaptive threshold", method_3_adaptive_threshold),
]

for method_name, method_func in methods:
    print(f"\n{method_name}")
    print("-"*100)
    
    errors = []
    for filename, target, desc in test_cases:
        with open(filename, 'r', encoding='utf-8') as f:
            tcx = f.read()
        
        elev_m = method_func(tcx)
        result = elev_m * 3.28084
        error = ((result - target) / target) * 100
        errors.append(abs(error))
        
        print(f"  {desc:25s}: {result:7.1f} ft (target: {target:4.0f} ft, error: {error:+6.1f}%)")
    
    avg_error = sum(errors) / len(errors)
    print(f"  {'Average error':25s}: {avg_error:6.1f}%")

print("\n" + "="*100)

