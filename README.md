# OneDrive Connector (FastAPI + PostgreSQL + React + Vite)

This full-stack project listens to OneDrive file change events using Microsoft Graph API webhooks, stores connector configs and tokens in PostgreSQL, and uploads file metadata or content to an external API.

It includes:

- Backend: FastAPI + PostgreSQL
- Frontend: React + Vite

## Prerequisites

- Python 3.10+
- PostgreSQL
- Ngrok (for local webhook testing)
- Microsoft 365 Work/School Account (not personal MSA)
- FastAPI
- Uvicorn
- httpx
- python-dotenv
- psycopg2-binary
- React + Vite

---

## Step 1: Register App in Azure Portal

1. Visit: [https://portal.azure.com](https://portal.azure.com)
2. Navigate to: **Azure Active Directory > App registrations > New registration**
3. Enter name (e.g., `OneDriveConnectorApp`)
4. Set redirect URI (for frontend auth handling)
5. Click **Register**

---

## Step 2: Generate Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add description + expiry (6 or 12 months)
4. Copy the `Value` (your `client_secret`) and store securely

---

## Step 3: API Permissions

1. Go to **API Permissions**
2. Click **Add a permission > Microsoft Graph**
3. Choose **Delegated permissions**
4. Add the following:

   - `Files.ReadWrite.All`
   - `offline_access`
   - `User.Read`

5. Click **Grant admin consent**

---

## Step 4: "frontend" workflow

1. The `frontend` folder uses React with Vite for a fast and modular SPA setup.
2. Inside the `Components` directory:

   - `RightSlideModal.jsx` collects client credentials and posts to `/credentials`
   - `AuthRedirect.jsx` handles OAuth2 redirect and posts the auth code to `/exchange-token`

3. Styling is handled by `RightSlideModal.css` and `FormField.css`
4. ESLint and HMR are configured for development.

---

## Step 5: "backend" workflow

1. The backend contains:

   - Directories: `routes`, `db`
   - Files: `main2.py`, `database.py`

2. `routes` includes:

   - `onedrive.py` for API endpoints
   - `subscribe.py` to create webhook subscriptions

3. `db` contains:

   - `onedrive_db.py` for all PostgreSQL logic using `psycopg2`

4. Models used:

```python
class Credentials(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str
    email_id: str
    app_id: str

class ExchangeRequest(BaseModel):
    auth_code: str
    email_id: str
    app_id: str
```

5. API routes:

```python
@onedrive_router.post("/credentials")
def add_credentials(input: Credentials)

@onedrive_router.post("/exchange-token")
def exchange_token(data: ExchangeRequest)

@onedrive_router.api_route("/webhook/notifications/{client_id}", methods=["GET", "POST"])
```

6. Database connection settings are in `database.py`
7. Subscriptions are initiated via `subscribe.py`

---
