#!/usr/bin/env python3
"""Refined tuning around the best parameters."""
import re

def elevation_gain_net_method(xml_text: str, window_size=25, threshold_meters=10.0) -> float:
    """Calculate elevation using NET gain per climb."""
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
        
        # Track climbs
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

# Load TCX files
with open('tcx_2025-11-16.xml', 'r', encoding='utf-8') as f:
    tcx1 = f.read()

with open('tcx_2025-11-09.xml', 'r', encoding='utf-8') as f:
    tcx2 = f.read()

TARGET1 = 224.0
TARGET2 = 264.0

print("Refined parameter search around best values")
print("="*85)
print(f"{'Window':>8} {'Threshold':>10} | {'11-16':>10} {'Err%':>7} | {'11-9':>10} {'Err%':>7} | {'Avg%':>7}")
print("="*85)

best_error = float('inf')
best_params = None
best_results = None

# Refined search around window=7, threshold=8
for window_size in range(5, 13):  # 5-12
    for threshold_meters in [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0]:
        elev1_m = elevation_gain_net_method(tcx1, window_size, threshold_meters)
        elev2_m = elevation_gain_net_method(tcx2, window_size, threshold_meters)
        
        result1 = elev1_m * 3.28084
        result2 = elev2_m * 3.28084
        
        error1_pct = abs((result1 - TARGET1) / TARGET1) * 100
        error2_pct = abs((result2 - TARGET2) / TARGET2) * 100
        avg_error = (error1_pct + error2_pct) / 2
        
        if avg_error < best_error:
            best_error = avg_error
            best_params = (window_size, threshold_meters)
            best_results = (result1, result2)
            
            err1 = ((result1 - TARGET1) / TARGET1) * 100
            err2 = ((result2 - TARGET2) / TARGET2) * 100
            
            print(f"{window_size:>8} {threshold_meters:>10.1f} | "
                  f"{result1:>10.2f} {err1:>+6.1f}% | {result2:>10.2f} {err2:>+6.1f}% | "
                  f"{avg_error:>6.1f}%")

print("="*85)
print(f"\nBest parameters found (avg error: {best_error:.1f}%):")
print(f"  window_size = {best_params[0]}")
print(f"  threshold_meters = {best_params[1]:.1f}")

print(f"\nFinal results:")
print(f"  11-16: {best_results[0]:.2f} ft (target: {TARGET1:.2f} ft, "
      f"error: {((best_results[0]-TARGET1)/TARGET1)*100:+.1f}%)")
print(f"  11-9:  {best_results[1]:.2f} ft (target: {TARGET2:.2f} ft, "
      f"error: {((best_results[1]-TARGET2)/TARGET2)*100:+.1f}%)")

