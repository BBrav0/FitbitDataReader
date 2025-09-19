import fitbit
import pandas as pd
from datetime import date

# You'll get these after the authorization step
# (The library helps you get these tokens)
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
ACCESS_TOKEN = ' https://api.fitbit.com/oauth2/token'
REFRESH_TOKEN =  'https://api.fitbit.com/oauth2/token'

# Authorize and create the client
auth_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET,
                          access_token=ACCESS_TOKEN,
                          refresh_token=REFRESH_TOKEN)

# --- Example: Fetch step data for today ---
today_str = str(date.today())
activity_data = auth_client.time_series('activities/steps', base_date=today_str, period='1d')

# The data comes back in JSON format
print(activity_data)
# {'activities-steps': [{'dateTime': '2025-09-18', 'value': '12345'}]}

# You can then easily put this data into a Pandas DataFrame
df = pd.DataFrame(activity_data['activities-steps'])
print(df)