#!/usr/bin/env python3
"""
Deep analysis of TCX files to understand climb patterns.
Let's see what climbs are being detected and why results vary.
"""
import re

def analyze_climbs(xml_text: str, window_size=30, threshold_meters=10.0, name="Run"):
    """Analyze what climbs are being detected."""
    try:
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        
        if not alts or len(alts) < 2:
            return None
        
        # Smooth
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Track climbs
        climbs = []
        in_climb = False
        climb_start = smoothed[0]
        climb_peak = smoothed[0]
        climb_start_idx = 0
        prev_alt = smoothed[0]
        
        for i, alt in enumerate(smoothed[1:], 1):
            if alt > prev_alt:
                if not in_climb:
                    in_climb = True
                    climb_start = prev_alt
                    climb_start_idx = i - 1
                    climb_peak = alt
                else:
                    climb_peak = max(climb_peak, alt)
            elif alt < prev_alt:
                if in_climb:
                    climb_gain = climb_peak - climb_start
                    climbs.append({
                        'start_idx': climb_start_idx,
                        'end_idx': i - 1,
                        'start_alt': climb_start,
                        'peak_alt': climb_peak,
                        'gain_m': climb_gain,
                        'gain_ft': climb_gain * 3.28084,
                        'counted': climb_gain >= threshold_meters
                    })
                    in_climb = False
            prev_alt = alt
        
        if in_climb:
            climb_gain = climb_peak - climb_start
            climbs.append({
                'start_idx': climb_start_idx,
                'end_idx': len(smoothed) - 1,
                'start_alt': climb_start,
                'peak_alt': climb_peak,
                'gain_m': climb_gain,
                'gain_ft': climb_gain * 3.28084,
                'counted': climb_gain >= threshold_meters
            })
        
        # Calculate totals
        total_counted = sum(c['gain_m'] for c in climbs if c['counted'])
        total_all = sum(c['gain_m'] for c in climbs)
        
        return {
            'name': name,
            'data_points': len(alts),
            'min_alt': min(alts),
            'max_alt': max(alts),
            'range': max(alts) - min(alts),
            'num_climbs': len(climbs),
            'num_counted': sum(1 for c in climbs if c['counted']),
            'total_counted_m': total_counted,
            'total_counted_ft': total_counted * 3.28084,
            'total_all_m': total_all,
            'total_all_ft': total_all * 3.28084,
            'climbs': climbs
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

# Load all test cases
test_cases = [
    ('tcx_2025-11-09.xml', 264.0, '42.2 mi - flat marathon'),
    ('tcx_2025-11-16.xml', 224.0, '7.4 mi - moderate'),
    ('tcx_2025-10-04.xml', 1147.0, '11.76 mi - very hilly'),
    ('tcx_2025-10-02.xml', 465.0, '2.14 mi - very hilly'),
]

print("="*100)
print("DEEP CLIMB ANALYSIS")
print("="*100)

for filename, target, desc in test_cases:
    with open(filename, 'r', encoding='utf-8') as f:
        tcx = f.read()
    
    result = analyze_climbs(tcx, 30, 10.0, desc)
    if not result:
        continue
    
    error = ((result['total_counted_ft'] - target) / target) * 100
    
    print(f"\n{result['name']}")
    print(f"  Target: {target:.0f} ft")
    print(f"  Calculated: {result['total_counted_ft']:.2f} ft (error: {error:+.1f}%)")
    print(f"  Data points: {result['data_points']}")
    print(f"  Altitude range: {result['range']:.1f}m ({result['range']*3.28084:.1f}ft)")
    print(f"  Total climbs detected: {result['num_climbs']}")
    print(f"  Climbs counted (>=10m): {result['num_counted']}")
    print(f"  Total if all counted: {result['total_all_ft']:.2f} ft")
    
    # Show largest climbs
    sorted_climbs = sorted(result['climbs'], key=lambda x: x['gain_m'], reverse=True)
    print(f"\n  Top 10 climbs:")
    for i, climb in enumerate(sorted_climbs[:10], 1):
        status = "COUNTED" if climb['counted'] else "ignored"
        print(f"    {i}. {climb['gain_ft']:6.1f} ft ({climb['gain_m']:5.1f}m) - {status}")
    
    # Show statistics
    counted = [c for c in result['climbs'] if c['counted']]
    if counted:
        avg_climb = sum(c['gain_m'] for c in counted) / len(counted)
        print(f"\n  Average counted climb: {avg_climb:.1f}m ({avg_climb*3.28084:.1f}ft)")
        print(f"  Largest counted climb: {max(c['gain_m'] for c in counted):.1f}m ({max(c['gain_ft'] for c in counted):.1f}ft)")

print("\n" + "="*100)

