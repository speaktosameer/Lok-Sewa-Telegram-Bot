import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Headers for REST API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def log_response(response):
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

def supabase_get(table: str):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    response = httpx.get(url, headers=headers)
    log_response(response)
    response.raise_for_status()
    return response.json()

def supabase_post(table: str, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = httpx.post(url, headers=headers, json=data)
    log_response(response)
    response.raise_for_status()
    return response.json()

def supabase_upsert(table: str, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict=telegram_id"
    response = httpx.post(
        url,
        headers={**headers, "Prefer": "resolution=merge-duplicates"},
        json=[data]  # upsert expects a list of records
    )
    log_response(response)
    response.raise_for_status()
    if response.text.strip():
        return response.json()
    return {}

def supabase_patch(table: str, record_id: int, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}"
    response = httpx.patch(url, headers=headers, json=data)
    log_response(response)
    response.raise_for_status()
    return response.json()
