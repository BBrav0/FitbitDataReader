#!/usr/bin/env python3
"""Verify the new parameters work correctly."""
import re

def elevation_gain_from_tcx(xml_text: str) -> float:
    """Updated algorithm with new parameters."""
    try:
        alts = [float(x) for x in re.findall(r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", xml_text or "")]
        if not alts or len(alts) < 2:
            return 0.0
        
        window_size = 30
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        threshold_meters = 10.0
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

# Test all 4 cases
test_cases = [
    ('tcx_2025-11-09.xml', 264.0, '42.2 mi - flat marathon'),
    ('tcx_2025-11-16.xml', 224.0, '7.4 mi - moderate'),
    ('tcx_2025-10-04.xml', 1147.0, '11.76 mi - very hilly'),
    ('tcx_2025-10-02.xml', 465.0, '2.14 mi - very hilly'),
]

print("="*80)
print("VERIFICATION OF UPDATED ALGORITHM (window=30, threshold=10.0m)")
print("="*80)

for filename, target, desc in test_cases:
    with open(filename, 'r', encoding='utf-8') as f:
        tcx = f.read()
    
    elev_m = elevation_gain_from_tcx(tcx)
    result = elev_m * 3.28084
    error = ((result - target) / target) * 100
    
    print(f"\n{desc}")
    print(f"  Calculated: {result:.2f} ft")
    print(f"  Target:     {target:.2f} ft")
    print(f"  Error:      {error:+.1f}%")

print("\n" + "="*80)

