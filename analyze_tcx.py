#!/usr/bin/env python3
"""Analyze TCX files to understand data characteristics."""
import re

def analyze_tcx(xml_text, name):
    """Analyze TCX file characteristics."""
    alts = [float(x) for x in re.findall(r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", xml_text or "")]
    
    if not alts:
        print(f"{name}: No altitude data")
        return
    
    # Calculate statistics
    print(f"\n{name}:")
    print(f"  Data points: {len(alts)}")
    print(f"  Min altitude: {min(alts):.1f}m")
    print(f"  Max altitude: {max(alts):.1f}m")
    print(f"  Altitude range: {max(alts) - min(alts):.1f}m ({(max(alts) - min(alts)) * 3.28084:.1f}ft)")
    print(f"  Mean altitude: {sum(alts)/len(alts):.1f}m")
    
    # Calculate raw elevation gain (no smoothing, no filtering)
    raw_gain = sum(max(0, alts[i] - alts[i-1]) for i in range(1, len(alts)))
    print(f"  Raw gain (all positive deltas): {raw_gain:.1f}m ({raw_gain * 3.28084:.1f}ft)")
    
    # Calculate noise characteristics
    deltas = [alts[i] - alts[i-1] for i in range(1, len(alts))]
    abs_deltas = [abs(d) for d in deltas]
    print(f"  Mean absolute delta: {sum(abs_deltas)/len(abs_deltas):.3f}m")
    print(f"  Max single delta: {max(abs_deltas):.1f}m")
    
    # Look at delta distribution
    small_deltas = sum(1 for d in abs_deltas if d < 0.5)
    medium_deltas = sum(1 for d in abs_deltas if 0.5 <= d < 2.0)
    large_deltas = sum(1 for d in abs_deltas if d >= 2.0)
    print(f"  Delta distribution:")
    print(f"    < 0.5m: {small_deltas} ({100*small_deltas/len(deltas):.1f}%)")
    print(f"    0.5-2m: {medium_deltas} ({100*medium_deltas/len(deltas):.1f}%)")
    print(f"    >= 2m: {large_deltas} ({100*large_deltas/len(deltas):.1f}%)")
    
    # Test smoothing effects
    for window_size in [7, 13, 19, 25]:
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        smoothed_gain = sum(max(0, smoothed[i] - smoothed[i-1]) for i in range(1, len(smoothed)))
        print(f"  Smoothed gain (window={window_size}): {smoothed_gain:.1f}m ({smoothed_gain * 3.28084:.1f}ft)")

# Load TCX files
with open('tcx_2025-11-16.xml', 'r', encoding='utf-8') as f:
    tcx1 = f.read()

with open('tcx_2025-11-09.xml', 'r', encoding='utf-8') as f:
    tcx2 = f.read()

print("="*80)
print("TCX FILE ANALYSIS")
print("="*80)

analyze_tcx(tcx1, "2025-11-16 (Target: 224ft)")
analyze_tcx(tcx2, "2025-11-09 (Target: 264ft)")

print("\n" + "="*80)

