import json
import os

import requests
from supabase import Client, create_client

from dotenv import load_dotenv

def create_supabase_client():
    load_dotenv()
    supabase: Client = create_client(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
    )
    return supabase

def iter_current_registered_account_ids():
    supabase: Client = create_supabase_client()

    max_records_per_page = 1000
    first_index = 0
    stop = False
    while not stop:
        response = (
            supabase.table("registered_accounts")
            .select("id")
            .is_("unregistered_at", "null")
            .range(first_index, first_index + max_records_per_page - 1)
            .execute()
        )
        for x in response.data:
            if not isinstance(x, dict):
                raise ValueError("Something is wrong with Supabase (registered_accounts)")
            
            yield x["id"]

        if len(response.data) == max_records_per_page:
            first_index += max_records_per_page
        else:
            stop = True

def fetch_profile_from_gdbrowser_colon(account_id):
    req = request_get_until_not_error(f"https://gdbrowser.com/api/profile/{account_id}")
    result = req.text
    result = json.loads(result)
    assert isinstance(result, dict)
    return result

def request_get_until_not_error(url: str, minus_one_strategy: str = "repeat"):
    stop = False
    while not stop:
        try:
            req = requests.get(url, timeout=10)
        except requests.exceptions.ConnectTimeout:
            print("Connection timeout. Try again.")
            continue
        except requests.exceptions.ConnectionError:
            print("Connection error. Try again.")
            continue
        except requests.exceptions.ReadTimeout:
            print("Read Timeout. Try again.")
            continue

        if req.text == "-1" and minus_one_strategy == "repeat":
            print("-1 output. Try again.")
            continue

        stop = True
    
    return req

def get_and_warn_if_not_exists(x, key_path):
    keys = key_path.split(".")
    y = x
    for k in keys:
        y = y.get(k, "???")
        if y == "???":
            print(f"Warning: no value at {key_path}")
            y = None
            break
    
    return y
