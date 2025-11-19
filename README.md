# Fitbit Data Reader

A personal Python project for fetching, storing, and analyzing running data from the Fitbit API. This tool retrieves detailed run metrics including distance, pace, elevation gain, heart rate data, cadence, and more, storing them in a local SQLite database for analysis and export.

## Features

- **OAuth2 Authentication**: Automatic token management with refresh capabilities
- **Comprehensive Data Collection**: Fetches run data including:
  - Distance, duration, and average pace
  - Elevation gain (from API or TCX files)
  - Heart rate metrics (min, max, average, resting)
  - Steps and cadence
  - Calories burned
  - Activity type (outdoor runs, treadmill runs)
- **SQLite Database**: Local caching to minimize API calls and enable offline analysis
- **CSV Export**: Export filtered run data to CSV for external analysis
- **TCX File Processing**: Extracts detailed heart rate data from Fitbit TCX files
- **Treadmill Run Support**: Manual data entry for treadmill runs with elevation calculation

## Project Structure

- `get_tokens.py` - OAuth2 token management and refresh
- `db_filler.py` - Main script to fetch and cache run data from Fitbit API
- `db_to_csv.py` - Export cached run data to CSV format
- `update.py` - Pipeline script that runs all components in sequence
- `cache.db` - SQLite database storing run data
- `runs_data.csv` - Exported CSV file with filtered run records

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Fitbit API credentials:
   ```
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   ACCESS_TOKEN=your_access_token
   REFRESH_TOKEN=your_refresh_token
   ```

3. Run the update pipeline:
   ```bash
   python update.py
   ```

   Or run individual scripts:
   - `python get_tokens.py` - Refresh/obtain OAuth tokens
   - `python db_filler.py` - Fetch and cache data
   - `python db_to_csv.py` - Export to CSV

## Migration Notice

**This project is being migrated to use the Garmin API instead of Fitbit.** The new implementation is being developed in a separate repository. This repository will remain available for historical reference and for users who need to access Fitbit data.

## Requirements

- Python 3.x
- fitbit
- pandas
- python-dotenv
- requests
- matplotlib
- scipy

## License

Personal project - use at your own discretion.
