from datetime import datetime
from zoneinfo import ZoneInfo

from tqdm import tqdm

from utils import (
    create_supabase_client,
    fetch_profile_from_gdbrowser_colon,
    insert_profile_into_supabase,
    iter_fetchable_account_ids
)

def iter_current_registered_account_ids_without_profiles(date_str: str):
    supabase = create_supabase_client()

    max_records_per_page = 1000
    first_index = 0
    stop = False

    existing_account_ids = set()
    while not stop:
        response = (
            supabase.table("profiles")
            .select("account_id")
            .eq("date", date_str)
            .range(first_index, first_index + max_records_per_page - 1)
            .execute()
        )
        for x in response.data:
            if not isinstance(x, dict):
                raise ValueError("Something is wrong with Supabase (registered_accounts)")
            
            existing_account_ids.add(x["account_id"])

        if len(response.data) == max_records_per_page:
            first_index += max_records_per_page
        else:
            stop = True

    for account_id in iter_fetchable_account_ids():
        if account_id in existing_account_ids:
            continue

        yield account_id

supabase = create_supabase_client()

date_str = str(datetime.now(ZoneInfo("Asia/Jakarta")).date())
account_id_list = [x for x in iter_current_registered_account_ids_without_profiles(date_str)]
print(f"Total:", len(account_id_list))

for account_id in (pbar := tqdm(account_id_list)):
    pbar.set_description(f"Processing {account_id}")
    profile = fetch_profile_from_gdbrowser_colon(account_id)
    insert_profile_into_supabase(date_str, profile)

print("Done!")
