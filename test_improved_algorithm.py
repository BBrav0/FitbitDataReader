#!/usr/bin/env python3
"""Test improved elevation algorithm based on Strava's method."""
import re

def elevation_gain_improved(xml_text: str, window_size=25, threshold_meters=10.0, 
                           reset_descent=3.0) -> float:
    """
    Improved elevation gain calculation matching Strava's approach.
    
    Key principles from Strava docs:
    1. Heavy smoothing for GPS data (more than barometric)
    2. Track climbs - consecutive gains grouped together  
    3. Only count climbs that exceed threshold (10m for GPS)
    4. Reset climb when descending significantly from climb start
    """
    try:
        # Extract altitude values
        alts = [float(x) for x in re.findall(
            r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", 
            xml_text or "")]
        
        if not alts or len(alts) < 2:
            return 0.0
        
        # Heavy smoothing for GPS data
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Track climbs and only count those exceeding threshold
        total_gain = 0.0
        climb_start_alt = smoothed[0]
        climb_max_alt = smoothed[0]
        current_climb_gain = 0.0
        
        for i in range(1, len(smoothed)):
            alt = smoothed[i]
            prev_alt = smoothed[i-1]
            delta = alt - prev_alt
            
            if delta > 0:
                # Ascending - add to current climb
                current_climb_gain += delta
                climb_max_alt = max(climb_max_alt, alt)
                
            elif delta < 0:
                # Descending - check if we should end the climb
                # End climb if we descend below start point by reset_descent meters
                if alt < (climb_start_alt - reset_descent):
                    # Climb ended - count it if it exceeds threshold
                    if current_climb_gain >= threshold_meters:
                        total_gain += current_climb_gain
                    
                    # Start new potential climb from current point
                    climb_start_alt = alt
                    climb_max_alt = alt
                    current_climb_gain = 0.0
                else:
                    # Still in same climb zone, just descending temporarily
                    # Update climb_max if needed (shouldn't happen here since delta < 0)
                    pass
        
        # Check final climb
        if current_climb_gain >= threshold_meters:
            total_gain += current_climb_gain
        
        return total_gain
        
    except Exception as e:
        print(f"Error: {e}")
        return 0.0

# Load TCX files
with open('tcx_2025-11-16.xml', 'r', encoding='utf-8') as f:
    tcx1 = f.read()

with open('tcx_2025-11-09.xml', 'r', encoding='utf-8') as f:
    tcx2 = f.read()

# Targets
TARGET1 = 224.0
TARGET2 = 264.0

print("Testing improved algorithm with parameter sweep")
print("="*95)
print(f"{'Window':>8} {'Threshold':>10} {'Reset':>8} | {'11-16':>10} {'Err%':>7} | {'11-9':>10} {'Err%':>7} | {'Avg%':>7}")
print("="*95)

best_error = float('inf')
best_params = None
best_results = None

# Focused parameter search
for window_size in [15, 19, 23, 25, 27, 29, 31]:
    for threshold_meters in [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0]:
        for reset_descent in [2.0, 3.0, 4.0, 5.0]:
            elev1_m = elevation_gain_improved(tcx1, window_size, threshold_meters, reset_descent)
            elev2_m = elevation_gain_improved(tcx2, window_size, threshold_meters, reset_descent)
            
            result1 = elev1_m * 3.28084
            result2 = elev2_m * 3.28084
            
            error1_pct = abs((result1 - TARGET1) / TARGET1) * 100
            error2_pct = abs((result2 - TARGET2) / TARGET2) * 100
            avg_error = (error1_pct + error2_pct) / 2
            
            if avg_error < best_error:
                best_error = avg_error
                best_params = (window_size, threshold_meters, reset_descent)
                best_results = (result1, result2)
                
                err1 = ((result1 - TARGET1) / TARGET1) * 100
                err2 = ((result2 - TARGET2) / TARGET2) * 100
                
                print(f"{window_size:>8} {threshold_meters:>10.1f} {reset_descent:>8.1f} | "
                      f"{result1:>10.2f} {err1:>+6.1f}% | {result2:>10.2f} {err2:>+6.1f}% | "
                      f"{avg_error:>6.1f}%")

print("="*95)
print(f"\nBest parameters found (avg error: {best_error:.1f}%):")
print(f"  window_size = {best_params[0]}")
print(f"  threshold_meters = {best_params[1]:.1f}")
print(f"  reset_descent = {best_params[2]:.1f}")

print(f"\nFinal results:")
print(f"  11-16: {best_results[0]:.2f} ft (target: {TARGET1:.2f} ft, "
      f"error: {((best_results[0]-TARGET1)/TARGET1)*100:+.1f}%)")
print(f"  11-9:  {best_results[1]:.2f} ft (target: {TARGET2:.2f} ft, "
      f"error: {((best_results[1]-TARGET2)/TARGET2)*100:+.1f}%)")

