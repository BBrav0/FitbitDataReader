#!/usr/bin/env python3
"""Focused parameter tuning based on Strava's methodology."""
import re

def elevation_gain_strava_method(xml_text: str, window_size=19, threshold_meters=10.0) -> float:
    """
    Calculate elevation gain using improved algorithm based on Strava's method.
    
    Key improvements:
    1. Heavier smoothing (larger window) for GPS data
    2. No min_delta filter - let smoothing handle noise
    3. Better climb tracking - reset on significant descent
    4. Count only climbs exceeding threshold
    """
    try:
        # Extract altitude values
        alts = [float(x) for x in re.findall(r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", xml_text or "")]
        if not alts or len(alts) < 2:
            return 0.0
        
        # Apply smoothing with larger window for GPS data
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Track climbs
        total_gain = 0.0
        in_climb = False
        climb_start_alt = smoothed[0]
        climb_gain = 0.0
        prev_alt = smoothed[0]
        
        for alt in smoothed[1:]:
            delta = alt - prev_alt
            
            if delta > 0:
                # Ascending
                if not in_climb:
                    # Start new climb
                    in_climb = True
                    climb_start_alt = prev_alt
                    climb_gain = delta
                else:
                    # Continue climb
                    climb_gain += delta
            elif delta < 0:
                # Descending
                if in_climb:
                    # Check if we've descended significantly below climb start
                    # Use 3m as threshold for significant descent
                    if alt < (climb_start_alt - 3.0):
                        # End climb, count if above threshold
                        if climb_gain >= threshold_meters:
                            total_gain += climb_gain
                        # Reset
                        in_climb = False
                        climb_gain = 0.0
            
            prev_alt = alt
        
        # Check final climb
        if in_climb and climb_gain >= threshold_meters:
            total_gain += climb_gain
        
        return total_gain
    except Exception:
        return 0.0

# Load TCX files
with open('tcx_2025-11-16.xml', 'r', encoding='utf-8') as f:
    tcx1 = f.read()

with open('tcx_2025-11-09.xml', 'r', encoding='utf-8') as f:
    tcx2 = f.read()

# Target values
TARGET1 = 224.0  # feet
TARGET2 = 264.0  # feet

print("Testing Strava-based algorithm with different parameters")
print("="*90)
print(f"{'Window':>8} {'Threshold':>10} | {'11-16':>10} {'Error%':>8} | {'11-9':>10} {'Error%':>8} | {'Avg Err%':>10}")
print("="*90)

best_error = float('inf')
best_params = None

# Test strategic combinations
for window_size in [13, 15, 17, 19, 21, 23, 25, 27, 29]:
    for threshold_meters in [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]:
        elev1_m = elevation_gain_strava_method(tcx1, window_size, threshold_meters)
        elev2_m = elevation_gain_strava_method(tcx2, window_size, threshold_meters)
        
        result1 = elev1_m * 3.28084
        result2 = elev2_m * 3.28084
        
        error1_pct = abs((result1 - TARGET1) / TARGET1) * 100
        error2_pct = abs((result2 - TARGET2) / TARGET2) * 100
        avg_error = (error1_pct + error2_pct) / 2
        
        if avg_error < best_error:
            best_error = avg_error
            best_params = (window_size, threshold_meters)
            
            error1_signed = ((result1 - TARGET1) / TARGET1) * 100
            error2_signed = ((result2 - TARGET2) / TARGET2) * 100
            
            print(f"{window_size:>8} {threshold_meters:>10.1f} | "
                  f"{result1:>10.2f} {error1_signed:>+7.1f}% | {result2:>10.2f} {error2_signed:>+7.1f}% | "
                  f"{avg_error:>9.1f}%")

print("="*90)
print(f"\nBest parameters (avg error: {best_error:.1f}%):")
print(f"  window_size = {best_params[0]}")
print(f"  threshold_meters = {best_params[1]}")

# Final test
elev1 = elevation_gain_strava_method(tcx1, *best_params) * 3.28084
elev2 = elevation_gain_strava_method(tcx2, *best_params) * 3.28084
print(f"\nFinal results:")
print(f"  11-16: {elev1:.2f} ft (target: {TARGET1:.2f} ft, error: {((elev1-TARGET1)/TARGET1)*100:+.1f}%)")
print(f"  11-9: {elev2:.2f} ft (target: {TARGET2:.2f} ft, error: {((elev2-TARGET2)/TARGET2)*100:+.1f}%)")

