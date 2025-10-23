import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import sqlite3 as sql

# Import cache database as an array
def load_cache_data():
    """Load all data from cache.db into a pandas DataFrame, filtering for activity_type in ('Run', 'Treadmill run')"""
    con = sql.connect("cache.db")
    # Get all column names
    cursor = con.cursor()
    cursor.execute("PRAGMA table_info(runs)")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]
    
    # Query to select only records where activity_type indicates a run
    query = "SELECT " + ", ".join(column_names) + " FROM runs WHERE activity_type IN ('Run', 'Treadmill run')"
    df = pd.read_sql_query(query, con)
    con.close()
    return df

cache_data = load_cache_data()
print(f"Loaded {len(cache_data)} records from cache database")
print(f"Columns: {list(cache_data.columns)}")
print(f"Date range: {cache_data['date'].min()} to {cache_data['date'].max()}")

# Convert date column to datetime
cache_data['date'] = pd.to_datetime(cache_data['date'])

# Group data by week (Monday to Sunday) and calculate total distance per week
def get_week_start(date):
    """Get the Monday of the week for a given date"""
    return date - pd.Timedelta(days=date.weekday())

# Add week start column
cache_data['week_start'] = cache_data['date'].apply(get_week_start)

# Group by week and sum distance
weekly_distance = cache_data.groupby('week_start')['distance'].sum().reset_index()
weekly_distance = weekly_distance.sort_values('week_start')

# Create week labels (Week 1, Week 2, etc.)
weekly_distance['week_label'] = [f'Week {i+1}' for i in range(len(weekly_distance))]

# Create the bar graph
plt.figure(figsize=(12, 6))
bars = plt.bar(weekly_distance['week_label'], weekly_distance['distance'], 
               color='skyblue', edgecolor='navy', alpha=0.7)

# Customize the plot
plt.title('Total Distance per Week (Monday to Sunday)', fontsize=16, fontweight='bold')
plt.xlabel('Week', fontsize=12)
plt.ylabel('Total Distance (miles)', fontsize=12)
plt.xticks(rotation=45, ha='right')

# Add value labels on top of bars
for bar, distance in zip(bars, weekly_distance['distance']):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
             f'{distance:.1f}', ha='center', va='bottom', fontsize=9)

# Add grid for better readability
plt.grid(axis='y', alpha=0.3)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Show the plot
plt.show()

print(f"\nWeekly Distance Summary:")
print(f"Total weeks: {len(weekly_distance)}")
print(f"Average distance per week: {weekly_distance['distance'].mean():.2f} miles")
print(f"Highest weekly distance: {weekly_distance['distance'].max():.2f} miles")
print(f"Lowest weekly distance: {weekly_distance['distance'].min():.2f} miles")

