#!/usr/bin/env python3
"""Test different parameter combinations to find optimal settings."""
import re
import os

def elevation_gain_from_tcx(xml_text: str, window_size=13, min_delta=0.22, 
                            threshold_meters=10.0, reset_threshold=-0.8) -> float:
    """Calculate elevation gain from TCX content using configurable parameters."""
    try:
        # Extract all altitude values from TCX
        alts = [float(x) for x in re.findall(r"<AltitudeMeters>([-+]?[0-9]*\.?[0-9]+)</AltitudeMeters>", xml_text or "")]
        if not alts or len(alts) < 2:
            return 0.0
        
        # Apply smoothing
        smoothed = []
        for i in range(len(alts)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(alts), i + window_size // 2 + 1)
            window = alts[start_idx:end_idx]
            smoothed.append(sum(window) / len(window))
        
        # Calculate gain
        total_gain = 0.0
        current_climb_gain = 0.0
        current_climb_start = smoothed[0]
        prev_alt = smoothed[0]
        
        for alt in smoothed[1:]:
            delta = alt - prev_alt
            
            if abs(delta) > min_delta:
                if delta > 0:
                    current_climb_gain += delta
                elif delta < 0:
                    net_from_start = alt - current_climb_start
                    
                    if net_from_start < reset_threshold:
                        if current_climb_gain >= threshold_meters:
                            total_gain += current_climb_gain
                        
                        current_climb_gain = 0.0
                        current_climb_start = alt
            
            prev_alt = alt
        
        # Check final climb
        if current_climb_gain >= threshold_meters:
            total_gain += current_climb_gain
        
        return total_gain
    except Exception:
        return 0.0

def test_params(tcx_content, window_size, min_delta, threshold_meters, reset_threshold):
    """Test specific parameters and return elevation in feet."""
    elev_m = elevation_gain_from_tcx(tcx_content, window_size, min_delta, 
                                      threshold_meters, reset_threshold)
    return elev_m * 3.28084

def calculate_error(result1_ft, target1_ft, result2_ft, target2_ft):
    """Calculate total error percentage for both test cases."""
    error1_pct = abs((result1_ft - target1_ft) / target1_ft) * 100
    error2_pct = abs((result2_ft - target2_ft) / target2_ft) * 100
    return (error1_pct + error2_pct) / 2

# Load TCX files
with open('tcx_2025-11-16.xml', 'r', encoding='utf-8') as f:
    tcx1 = f.read()

with open('tcx_2025-11-09.xml', 'r', encoding='utf-8') as f:
    tcx2 = f.read()

# Target values from Strava
TARGET1 = 224.0  # feet
TARGET2 = 264.0  # feet

print("Testing parameter combinations...")
print("="*100)
print(f"{'Window':>8} {'MinDelta':>10} {'Threshold':>10} {'Reset':>8} | "
      f"{'11-16':>10} {'Error%':>8} | {'11-9':>10} {'Error%':>8} | {'Avg Err%':>10}")
print("="*100)

best_error = float('inf')
best_params = None

# Test different combinations
for window_size in [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]:
    for min_delta in [0.0, 0.1, 0.22, 0.5, 1.0]:
        for threshold_meters in [5.0, 7.0, 10.0, 12.0, 15.0]:
            for reset_threshold in [-0.5, -0.8, -1.0, -2.0, -3.0, -5.0]:
                result1 = test_params(tcx1, window_size, min_delta, threshold_meters, reset_threshold)
                result2 = test_params(tcx2, window_size, min_delta, threshold_meters, reset_threshold)
                
                avg_error = calculate_error(result1, TARGET1, result2, TARGET2)
                
                if avg_error < best_error:
                    best_error = avg_error
                    best_params = (window_size, min_delta, threshold_meters, reset_threshold)
                    
                    error1_pct = ((result1 - TARGET1) / TARGET1) * 100
                    error2_pct = ((result2 - TARGET2) / TARGET2) * 100
                    
                    print(f"{window_size:>8} {min_delta:>10.2f} {threshold_meters:>10.1f} {reset_threshold:>8.1f} | "
                          f"{result1:>10.2f} {error1_pct:>+7.1f}% | {result2:>10.2f} {error2_pct:>+7.1f}% | "
                          f"{avg_error:>9.1f}%")

print("="*100)
print(f"\nBest parameters found (avg error: {best_error:.1f}%):")
print(f"  window_size = {best_params[0]}")
print(f"  min_delta = {best_params[1]}")
print(f"  threshold_meters = {best_params[2]}")
print(f"  reset_threshold = {best_params[3]}")

# Test best parameters
result1 = test_params(tcx1, *best_params)
result2 = test_params(tcx2, *best_params)
print(f"\nResults with best parameters:")
print(f"  11-16: {result1:.2f} ft (target: {TARGET1:.2f} ft, error: {((result1-TARGET1)/TARGET1)*100:+.1f}%)")
print(f"  11-9: {result2:.2f} ft (target: {TARGET2:.2f} ft, error: {((result2-TARGET2)/TARGET2)*100:+.1f}%)")

