"""Run this with the code from Google: py exchange_code.py YOUR_CODE"""
import sys
import json
import pickle
import requests
import google.oauth2.credentials
from pathlib import Path

TOKEN_PATH = Path(__file__).parent.parent / "credentials" / "token.pkl"
CLIENT_SECRETS_PATH = Path(__file__).parent.parent / "credentials" / "oauth_client.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

if len(sys.argv) < 2:
    print("Usage: py exchange_code.py YOUR_CODE_HERE")
    sys.exit(1)

code = sys.argv[1].strip()
client_info = json.loads(CLIENT_SECRETS_PATH.read_text())["installed"]

resp = requests.post("https://oauth2.googleapis.com/token", data={
    "code": code,
    "client_id": client_info["client_id"],
    "client_secret": client_info["client_secret"],
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "grant_type": "authorization_code",
})

token_data = resp.json()
if "error" in token_data:
    print(f"Error: {token_data['error']} — {token_data.get('error_description', '')}")
    print("The code may have expired. Run get_auth_url.py again to get a fresh URL.")
    sys.exit(1)

creds = google.oauth2.credentials.Credentials(
    token=token_data["access_token"],
    refresh_token=token_data.get("refresh_token"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_info["client_id"],
    client_secret=client_info["client_secret"],
    scopes=SCOPES,
)

with open(TOKEN_PATH, "wb") as f:
    pickle.dump(creds, f)

print("Authentication successful! Token saved. Run ga4_client.py to sync data.")
