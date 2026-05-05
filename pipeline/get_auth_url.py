"""Run this first to get the login URL."""
import json
from pathlib import Path
from urllib.parse import urlencode

CLIENT_SECRETS_PATH = Path(__file__).parent.parent / "credentials" / "oauth_client.json"
client_info = json.loads(CLIENT_SECRETS_PATH.read_text())["installed"]

params = {
    "client_id": client_info["client_id"],
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "response_type": "code",
    "scope": "https://www.googleapis.com/auth/analytics.readonly",
    "access_type": "offline",
    "prompt": "consent",
}

auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)

print("\nOpen this URL in Firefox:\n")
print(auth_url)
print("\nAfter signing in and clicking Allow, copy the code.")
print("Then paste it back in the chat.\n")
