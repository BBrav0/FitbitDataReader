import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

df = pd.read_json('runs.json')

df['date'] = pd.to_datetime(df['date'])

# Filter out null values for resting_hr
df_clean = df.dropna(subset=['resting_hr'])

# Create the scatter plot
plt.figure(figsize=(12, 6))
plt.scatter(df_clean['date'], df_clean['resting_hr'], alpha=0.6, label='Data Points')

# Convert dates to numeric values for trend line calculation
date_numeric = pd.to_numeric(df_clean['date'])

# Calculate trend line using linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(date_numeric, df_clean['resting_hr'])

# Create trend line
trend_line = slope * date_numeric + intercept

# Plot the trend line
plt.plot(df_clean['date'], trend_line, 'r-', linewidth=2, label=f'Trend Line (R² = {r_value**2:.3f})')

plt.xlabel('Date')
plt.ylabel('Resting Heart Rate')
plt.title('Resting Heart Rate Over Time with Trend Line')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

plt.show() 