#!/usr/bin/env python3
"""Sample mobile client flow for MuK REST + HR Hub attendance POST."""

import requests

BASE_URL = "https://your-hub-odoo.example.com"
DB_NAME = "hub_database_name"
CLIENT_ID = "oauth_client_id"
CLIENT_SECRET = "oauth_client_secret"

payload = {
    "employee_id": 42,
    "device_uuid": "e6fd8ef5-6d8e-4f72-99f5-9f5bb1dc8fd6",
    "faceio_id": "faceio_facial_id_from_authenticate",
    "lat": 24.7136,
    "long": 46.6753,
}


def fetch_oauth2_token():
    token_url = f"{BASE_URL}/api/v1/authentication/oauth2/token?db={DB_NAME}"
    response = requests.post(
        token_url,
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def post_attendance(token):
    endpoint = f"{BASE_URL}/api/v1/hr_hub/attendance?db={DB_NAME}"
    response = requests.post(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    access_token = fetch_oauth2_token()
    result = post_attendance(access_token)
    print(result)
