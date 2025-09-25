import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import sqlite3 as sql

# Import cache database as an array
def load_cache_data():
    """Load all data from cache.db into a pandas DataFrame"""
    con = sql.connect("cache.db")
    df = pd.read_sql_query("SELECT * FROM runs", con)
    con.close()
    return df

# Load the data
cache_data = load_cache_data()
print(f"Loaded {len(cache_data)} records from cache database")
print(f"Columns: {list(cache_data.columns)}")
print(f"Date range: {cache_data['date'].min()} to {cache_data['date'].max()}")

# Find the run with the highest heart rate range (maxhr - minhr)
# Method 1: Using pandas operations (more efficient)
cache_data['hr_range'] = cache_data['maxhr'] - cache_data['minhr']
max_hr_range_idx = cache_data['hr_range'].idxmax()
max_hr_range_run = cache_data.loc[max_hr_range_idx]

print(f"Date with highest HR range: {max_hr_range_run['date']}")
print(f"HR range: {max_hr_range_run['maxhr']} - {max_hr_range_run['minhr']} = {max_hr_range_run['hr_range']}")

# Method 2: Manual iteration (your original approach, but fixed)
temp = cache_data.iloc[0]  # Get first row properly
for index, run in cache_data.iterrows():  # Iterate over rows, not columns
    if run['maxhr'] - run['minhr'] > temp['maxhr'] - temp['minhr']:
        temp = run

print(f"Date with highest HR range (manual): {temp['date']}")
print(f"HR range (manual): {temp['maxhr']} - {temp['minhr']} = {temp['maxhr'] - temp['minhr']}")
