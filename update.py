"""
Update script that runs the Fitbit data update pipeline:
1. get_tokens.py - Get/refresh OAuth tokens
2. db_filler.py - Fetch and cache run data from Fitbit API
3. db_to_csv.py - Export cached data to CSV
"""
import subprocess
import sys

def run_script(script_name):
    """Run a Python script and return True if successful."""
    print(f"\n{'='*60}")
    print(f"Running {script_name}...")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True
        )
        print(f"\n✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {script_name} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n✗ Error: {script_name} not found")
        return False

if __name__ == "__main__":
    scripts = [
        "get_tokens.py",
        "db_filler.py",
        "db_to_csv.py"
    ]
    
    print("Starting Fitbit data update pipeline...")
    
    for script in scripts:
        success = run_script(script)
        if not success:
            print(f"\nPipeline stopped due to failure in {script}")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print("All scripts completed successfully!")
    print(f"{'='*60}")

