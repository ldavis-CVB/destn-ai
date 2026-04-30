"""
OAuth setup — opens a browser tab, you sign in, done.
Run directly:  python pipeline/oauth_setup.py
"""

import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
TOKEN_PATH = Path(__file__).parent.parent / "credentials" / "token.pkl"
CLIENT_SECRETS_PATH = Path(__file__).parent.parent / "credentials" / "oauth_client.json"


def get_oauth_credentials():
    # Return cached token if still valid
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
        if creds and creds.valid:
            print("Already authenticated!")
            return creds
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, "wb") as f:
                    pickle.dump(creds, f)
                print("Token refreshed.")
                return creds
            except Exception:
                pass  # fall through to re-auth

    # Open browser for fresh login — handles PKCE automatically
    print("Opening browser for Google sign-in...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_PATH), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)

    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)
    print("Authentication successful! Token saved.")
    return creds


if __name__ == "__main__":
    get_oauth_credentials()
