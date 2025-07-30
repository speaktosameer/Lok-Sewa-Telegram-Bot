import os
from dotenv import load_dotenv
import httpx

# Load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Standard headers for Supabase REST API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Fetch all data from a table
def supabase_get(table: str):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# Insert new data into a table
def supabase_post(table: str, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = httpx.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Upsert (insert or update) user data
def supabase_upsert(table: str, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict=telegram_id"
    response = httpx.post(
        url,
        headers={**headers, "Prefer": "resolution=merge-duplicates"},
        json=[data]  # Must be a list for upsert
    )
    response.raise_for_status()
    return response.json()

# Update a record by ID (optional utility)
def supabase_patch(table: str, record_id: int, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{record_id}"
    response = httpx.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
