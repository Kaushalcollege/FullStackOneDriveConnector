import requests
import datetime

def onedrive_subscription(access_token: str, client_id: str, notification_url: str, drive_id: str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    expiration_datetime = (datetime.datetime.utcnow() + datetime.timedelta(minutes=60)).isoformat() + "Z"

    payload = {
        "changeType": "updated,created",
        "notificationUrl": f"{notification_url}/webhook/onedrive/{client_id}",
        "resource": f"/drives/{drive_id}/root",
        "expirationDateTime": expiration_datetime,
        "clientState": "secretClientValue"
    }

    response = requests.post("https://graph.microsoft.com/v1.0/subscriptions", headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()["id"]
    else:
        raise Exception(f"Failed to create OneDrive subscription: {response.text}")
