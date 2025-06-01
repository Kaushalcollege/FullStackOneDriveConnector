import traceback
from database import get_connection
import json
import datetime
import random
import string


def generate_connector_id():
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=14))
    return f"c_{random_part}"


def insert_credentials_to_db(Input):
    conn = get_connection()
    cursor = conn.cursor()
    connector_id = generate_connector_id()
    now = datetime.datetime.utcnow()

    config = {
        "tenant_id": Input.tenant_id,
        "client_id": Input.client_id,
        "client_secret": Input.client_secret
    }

    empty_token = {
        "access_token": None,
        "refresh_token": None
    }

    cursor.execute(
        """
        INSERT INTO connector (connector_id, type, app_id, config, created_date, updated_date, token)
        VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s::jsonb)
        """,
        (
            connector_id,
            "onedrive",
            Input.app_id,
            json.dumps(config),
            now,
            now,
            json.dumps(empty_token)
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

    return connector_id


def get_connector_by_client_id(client_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT connector_id, config, token, app_id FROM connector WHERE config ->> 'client_id' = %s",
        (client_id,)
    )

    row = cursor.fetchone()
    if not row:
        raise Exception("Connector not found for client_id")

    cursor.close()
    conn.close()

    connector_id = row["connector_id"]
    config_json = row["config"]
    token_json = row["token"]
    app_id = row["app_id"]

    access_token = token_json.get("access_token")

    return connector_id, config_json, access_token, app_id


def update_tokens_and_log(connector_id, access_token, refresh_token, subscription_id):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.utcnow()

    cursor.execute(
        """
        UPDATE connector
        SET token = %s::jsonb, updated_date = %s
        WHERE connector_id = %s
        """,
        (
            json.dumps({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "subscription_id": subscription_id
            }),
            now,
            connector_id
        )
    )

    conn.commit()
    cursor.close()
    conn.close()


def insert_log_entry(connector_id, app_id, document_name, additional_info, status, message_id=None):
    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
            INSERT INTO connector_log (
                connector_id, app_id, document_name, additional_info, status, created_date, updated_date, message_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        now = datetime.datetime.utcnow()
        cur.execute(query, (
            connector_id,
            app_id,
            document_name,
            additional_info,
            status,
            now,
            now,
            message_id
        ))
        conn.commit()
        print(f"Inserted log for {document_name} (message_id={message_id})")
    except Exception as e:
        print(f"Error inserting log: {e}")
        traceback.print_exc()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def message_already_processed(message_id: str) -> bool:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM connector_log WHERE message_id = %s LIMIT 1", (message_id,))
        exists = cur.fetchone() is not None
        return exists
    except Exception as e:
        print(f"Error checking message_id {message_id}: {e}")
        traceback.print_exc()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def does_it_exist(client_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM connector WHERE config ->> 'client_id' = %s",
        (client_id,)
    )
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists


def update_credentials_to_db(Input):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.utcnow()

    updated_config = {
        "tenant_id": Input.tenant_id,
        "client_id": Input.client_id,
        "client_secret": Input.client_secret
    }

    cursor.execute(
        """
        UPDATE connector
        SET config = %s::jsonb,
            updated_date = %s
        WHERE config ->> 'client_id' = %s
        """,
        (
            json.dumps(updated_config),
            now,
            Input.client_id
        )
    )
    conn.commit()
    cursor.close()
    conn.close()
