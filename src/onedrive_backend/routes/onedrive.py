import traceback
import requests
import datetime
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from db.onedrive_db import (
    insert_credentials_to_db,
    update_credentials_to_db,
    get_connector_by_email_by_client_id,
    update_tokens_and_log,
    insert_log_entry,
    message_already_processed,
    does_it_exist
)
from routes.onedrive_subscribe import onedrive_subscription

onedrive_router = APIRouter()

# ✅ Corrected Scope Name
SCOPES = ["Files.ReadWrite.All", "offline_access", "User.Read"]

# ✅ Data models
class Credentials(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    app_id: str

class ExchangeRequest(BaseModel):
    auth_code: str
    client_id: str
    app_id: str

# ✅ Save or update credentials
@onedrive_router.post("/credentials")
def add_credentials(Input: Credentials):
    try:
        if does_it_exist(Input.client_id):
            update_credentials_to_db(Input)
            connector_id, *_ = get_connector_by_email_by_client_id(Input.client_id)
        else:
            connector_id = insert_credentials_to_db(Input)
        return JSONResponse(content={"connector_id": connector_id})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

# ✅ Token exchange & OneDrive subscription setup
@onedrive_router.post("/exchange-token")
def exchange_token(data: ExchangeRequest):
    try:
        connector_id, config, _, app_id = get_connector_by_email_by_client_id(data.client_id)
        print(connector_id)
        print(config)
        print(app_id)

        tenant_id = config["tenant_id"]
        client_id = config["client_id"]
        client_secret = config["client_secret"]

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        redirect_uri = f"http://localhost:5173/redirect/{data.app_id}"

        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": data.auth_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(SCOPES),
        }

        token_response = requests.post(token_url, data=payload)
        if token_response.status_code != 200:
            print(token_response.text)
            raise HTTPException(status_code=400, detail="Token exchange failed")

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        # ✅ Fetch OneDrive drive ID
        drive_info = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers={
            "Authorization": f"Bearer {access_token}"
        })
        if drive_info.status_code != 200:
            print(drive_info.text)
            raise HTTPException(status_code=400, detail="Failed to get OneDrive info")

        drive_id = drive_info.json().get("id")
        if not drive_id:
            raise HTTPException(status_code=400, detail="Drive ID missing in response")

        # ✅ Webhook setup
        notification_url = "https://6113-183-82-117-42.ngrok-free.app"  # Replace with actual
        subscription_id = onedrive_subscription(
            access_token=access_token,
            client_id=client_id,
            notification_url=notification_url,
            drive_id=drive_id
        )

        update_tokens_and_log(connector_id, access_token, refresh_token, subscription_id)
        return {"message": "Token exchanged and subscription created successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

# ✅ Webhook endpoint for validation & notifications
@onedrive_router.api_route("/webhook/onedrive/{client_id}", methods=["GET", "POST"])
async def handle_onedrive_notification(client_id: str, request: Request):
    try:
        # ✅ Handle Microsoft validation
        validation_token = request.query_params.get("validationToken")
        if validation_token:
            return PlainTextResponse(content=validation_token, status_code=200)

        body = await request.json()
        for item in body.get("value", []):
            resource = item.get("resource")
            if not resource:
                continue

            connector_id, config, access_token, app_id = get_connector_by_email_by_client_id(client_id)

            # ✅ Fetch file details from the resource
            file_resp = requests.get(f"https://graph.microsoft.com/v1.0/{resource}", headers={
                "Authorization": f"Bearer {access_token}"
            })

            if file_resp.status_code != 200:
                print(f"Failed to fetch resource {resource}: {file_resp.text}")
                continue

            file_data = file_resp.json()
            file_name = file_data.get("name")
            file_id = file_data.get("id")

            if not file_id:
                continue

            insert_log_entry(
                connector_id=connector_id,
                app_id=app_id,
                document_name=file_name,
                additional_info=json.dumps({"file_metadata": file_data}),
                status="file updated",
                message_id=file_id
            )

        return JSONResponse(content={"status": "OneDrive Event Processed"}, status_code=202)

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)
