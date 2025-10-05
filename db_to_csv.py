import sqlite3
import csv
import os

def export_runs_to_csv(db_path="cache.db", csv_path="runs_data.csv"):
    """
    Connects to the SQLite database, reads data from the 'runs' table,
    filters for records where has_run = 1, and writes them to a CSV file.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'")
        return

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get column names from the runs table, excluding has_run
        cursor.execute("PRAGMA table_info(runs)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info if col[1] != 'has_run']

        # Query to select all records where has_run is 1, excluding the has_run column
        query = "SELECT " + ", ".join([col for col in column_names]) + " FROM runs WHERE has_run = 1"
        cursor.execute(query)

        # Fetch all the records
        records = cursor.fetchall()

        if not records:
            print("No records found with has_run = 1.")
            return

        # Write the data to a CSV file
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write the header (column names)
            csv_writer.writerow(column_names)

            # Write the records
            csv_writer.writerows(records)

        print(f"Successfully exported {len(records)} records to '{csv_path}'")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Define the database and CSV file paths
    database_file = "cache.db"
    output_csv_file = "runs_data.csv"

    print(f"Attempting to export data from '{database_file}' to '{output_csv_file}'...")
    export_runs_to_csv(database_file, output_csv_file)
