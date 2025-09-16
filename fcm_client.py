import time
import json
import jwt   # pip install PyJWT
import requests
from pathlib import Path

SERVICE_ACCOUNT_FILE = Path(__file__).parent / "chat-app-447709-firebase-adminsdk-fbsvc-3eea0fa517.json"

with open(SERVICE_ACCOUNT_FILE) as f:
    sa = json.load(f)

PRIVATE_KEY = sa["private_key"]
CLIENT_EMAIL = sa["client_email"]
PROJECT_ID = sa["project_id"]

# cache access token so we don't request on every call
_cached_token = None
_cached_exp = 0


def _get_access_token():
    global _cached_token, _cached_exp

    now = int(time.time())
    if _cached_token and now < _cached_exp - 60:  # still valid for >60s
        return _cached_token

    jwt_payload = {
        "iss": CLIENT_EMAIL,
        "scope": "https://www.googleapis.com/auth/firebase.messaging",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }
    jwt_token = jwt.encode(jwt_payload, PRIVATE_KEY, algorithm="RS256")

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token,
        },
    )
    resp.raise_for_status()
    token_data = resp.json()
    _cached_token = token_data["access_token"]
    _cached_exp = now + token_data["expires_in"]

    return _cached_token


def send_push(device_token: str, title: str, body: str, data: dict = None):
    """Send a push notification to a device via FCM v1"""
    access_token = _get_access_token()

    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    message = {
        "message": {
            "token": device_token,
            "notification": {
                "title": title,
                "body": body,
                "image": "https://markochat.com/assets/marko-splash.png",
            },
            "data": data
        }
    }

    resp = requests.post(url, headers=headers, json=message)
    return resp.status_code, resp.text
