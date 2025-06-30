import requests
import datetime

def onedrive_subscription(access_token: str, client_id: str, notification_url: str, drive_id: str):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    expiration_datetime = (datetime.datetime.utcnow() + datetime.timedelta(minutes=60)).isoformat() + "Z"

    payload = {
        "changeType": "updated",  # ✅ Valid value
        "notificationUrl": f"{notification_url}/webhook/onedrive/{client_id}",
        "resource": "/me/drive/root",
        "expirationDateTime": expiration_datetime,
        "clientState": "secretClientValue"
    }

    response = requests.post("https://graph.microsoft.com/v1.0/subscriptions", headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()["id"]
    else:
        print("❌ Subscription creation failed:")
        print("Request Payload:", payload)
        print("Response Status:", response.status_code)
        print("Response Body:", response.text)
        raise Exception(f"Failed to create OneDrive subscription: {response.text}")
