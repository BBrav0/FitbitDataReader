"""
Fitbit OAuth2 Token Generator
This script will help you get your ACCESS_TOKEN and REFRESH_TOKEN
"""
import os
import webbrowser
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Fitbit app credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8080/'

if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: Please set CLIENT_ID and CLIENT_SECRET in your .env file")
    exit(1)

print("Fitbit OAuth2 Token Generator")
print("=" * 40)
print(f"Client ID: {CLIENT_ID}")
print(f"Redirect URI: {REDIRECT_URI}")
print()

# Step 1: Generate authorization URL
auth_url = f"https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight"

print("Step 1: Authorization")
print("Click the link below to authorize your app:")
print(auth_url)
print()

# Open browser automatically
print("Opening browser...")
webbrowser.open(auth_url)

print("After authorizing, you'll be redirected to a URL that looks like:")
print(f"{REDIRECT_URI}?code=YOUR_AUTHORIZATION_CODE")
print()
print("Copy the authorization code from the URL and paste it below:")

# Get authorization code from user
auth_code = input("Enter the authorization code: ").strip()

if not auth_code:
    print("No authorization code provided. Exiting.")
    exit(1)

print("\nStep 2: Getting tokens...")

# Step 2: Exchange authorization code for tokens
import requests
import base64

# Prepare the token request
token_url = "https://api.fitbit.com/oauth2/token"
headers = {
    'Authorization': f'Basic {base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()}',
    'Content-Type': 'application/x-www-form-urlencoded'
}

data = {
    'client_id': CLIENT_ID,
    'grant_type': 'authorization_code',
    'redirect_uri': REDIRECT_URI,
    'code': auth_code
}

try:
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    
    tokens = response.json()
    
    print("Success! Here are your tokens:")
    print("=" * 40)
    print(f"ACCESS_TOKEN={tokens['access_token']}")
    print(f"REFRESH_TOKEN={tokens['refresh_token']}")
    print()
    print("Add these to your .env file:")
    print("=" * 40)
    print(f"ACCESS_TOKEN={tokens['access_token']}")
    print(f"REFRESH_TOKEN={tokens['refresh_token']}")
    print()
    print("Your .env file should now look like:")
    print("=" * 40)
    print(f"CLIENT_ID={CLIENT_ID}")
    print(f"CLIENT_SECRET={CLIENT_SECRET}")
    print(f"ACCESS_TOKEN={tokens['access_token']}")
    print(f"REFRESH_TOKEN={tokens['refresh_token']}")
    
except requests.exceptions.RequestException as e:
    print(f"Error getting tokens: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response: {e.response.text}")
