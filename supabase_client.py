# supabase_client.py
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def supabase_get(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def supabase_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = httpx.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def supabase_upsert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict=telegram_id"
    response = httpx.post(url, headers={**headers, "Prefer": "resolution=merge-duplicates"}, json=data)
    response.raise_for_status()
    return response.json()
