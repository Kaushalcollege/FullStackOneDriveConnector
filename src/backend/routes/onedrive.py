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
    update_tokens_and_log,
    insert_log_entry,
    does_it_exist
)
from routes.onedrive_subscribe import onedrive_subscription

onedrive_router = APIRouter()

SCOPES = ["Files.ReadWrite.All", "offline_access", "User.Read"]

class Credentials(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    app_id: str

class ExchangeRequest(BaseModel):
    auth_code: str
    app_id: str


@onedrive_router.post("/credentials")
def add_credentials(Input: Credentials):
    try:
        if does_it_exist(Input.app_id):
            update_credentials_to_db(Input)
            connector_id, _ = get_connector_by_email(Input.email_id)
        else:
            connector_id = insert_credentials_to_db(Input)
        return JSONResponse(content={"connector_id": connector_id})
    except Exception as e:
        print(f"Error in /credentials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@onedrive_router.post("/exchange-token")
def exchange_token(data: ExchangeRequest):
    try:
        connector_id, config = get_connector_by_email(data.email_id)

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
            raise HTTPException(status_code=400, detail="Token exchange failed")

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        # Fetch drive ID for subscription
        drive_info = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers={
            "Authorization": f"Bearer {access_token}"
        })

        if drive_info.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get OneDrive info")

        drive_id = drive_info.json()["id"]

        notification_url = "https://3f6d-183-82-117-42.ngrok-free.app"
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


@onedrive_router.api_route("/webhook/onedrive/{client_id}", methods=["GET", "POST"])
async def handle_onedrive_notification(client_id: str, request: Request):
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        return PlainTextResponse(content=validation_token, status_code=200)

    try:
        body = await request.json()
        print("Received OneDrive notification: ", body)

        for item in body.get("value", []):
            resource = item.get("resource", "")
            if "root" not in resource:
                print(f"Skipping non-root event: {resource}")
                continue

            connector_id, config, access_token, app_id = get_connector_by_email_by_client_id(client_id)

            # Fetch file metadata (e.g., name, size, etc.)
            file_resp = requests.get(f"https://graph.microsoft.com/v1.0/{resource}", headers={
                "Authorization": f"Bearer {access_token}"
            })

            if file_resp.status_code != 200:
                print(f"Failed to fetch file metadata: {file_resp.text}")
                continue

            file_data = file_resp.json()
            file_name = file_data.get("name")
            file_size = file_data.get("size")

            insert_log_entry(
                connector_id=connector_id,
                app_id=app_id,
                document_name=file_name,
                additional_info=json.dumps({
                    "file_metadata": file_data
                }),
                status="file updated",
                message_id=file_data.get("id")  # Use file ID to avoid reprocessing
            )

        return JSONResponse(content={"status": "OneDrive Event Processed"}, status_code=202)
    except Exception as e:
        print(f"OneDrive webhook error: {e}")
        traceback.print_exc()
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)
