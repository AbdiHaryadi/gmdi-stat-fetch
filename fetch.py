from datetime import datetime
import time
from zoneinfo import ZoneInfo

from tqdm import tqdm

from utils import (
    create_supabase_client,
    fetch_all_records,
    fetch_profile_from_gdbrowser_colon_with_account_id,
    fetch_profile_from_gdbrowser_colon_with_player_id,
    insert_profile_into_supabase,
    iter_fetchable_account_ids_and_player_ids
)

def iter_current_registered_account_ids_and_player_ids_without_profiles(date_str: str):
    existing_account_ids = set()
    for x in fetch_all_records(
        create_supabase_client().table("profiles")
        .select("account_id")
        .eq("date", date_str)
        .order("account_id")
    ):
        existing_account_ids.add(x["account_id"])

    for account_id, player_id in iter_fetchable_account_ids_and_player_ids():
        if account_id in existing_account_ids:
            continue

        yield account_id, player_id

def fetch_all_profiles():
    date_str = str(datetime.now(ZoneInfo("Asia/Jakarta")).date())
    account_player_id_tuple_list = [x for x in iter_current_registered_account_ids_and_player_ids_without_profiles(date_str)]
    print(f"Total:", len(account_player_id_tuple_list))

    for account_id, player_id in (pbar := tqdm(account_player_id_tuple_list)):
        pbar.set_description(f"Processing {account_id}")
        profile = fetch_profile_from_gdbrowser_colon_with_account_id(account_id)
        if int(profile["accountID"]) != account_id and player_id is not None:
            player_id = player_id
            profile = fetch_profile_from_gdbrowser_colon_with_player_id(player_id)

        if int(profile["accountID"]) != account_id:
            print(f"Warning: {account_id} is skipped because the profile has different account_id.")
        else:
            insert_profile_into_supabase(date_str, profile)
    
        time.sleep(1)

    return date_str

if __name__ == "__main__":
    fetch_all_profiles()
    print("Done!")
