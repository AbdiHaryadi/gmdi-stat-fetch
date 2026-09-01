import datetime
import sys

from tqdm import tqdm

from utils import create_supabase_client, fetch_all_records

def insert_leaderboard_monthly(year, month):
    delete_all_leaderboard_monthly_stats_in_specific_month(year, month)
    player_rankable_map = fetch_player_rankable_map()

    min_date = (
        datetime.date(year=year, month=month, day=1)
        - datetime.timedelta(days=1)
    ).strftime("%Y-%m-%d")
    if month == 12:
        max_date = (
            datetime.date(year=year+1, month=1, day=1)
            - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d")
    else:
        max_date = (
            datetime.date(year=year, month=month+1, day=1)
            - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d")

    all_profile_data = fetch_all_profiles_in_specific_range(min_date, max_date)
    record_map = {}

    records = []
    for x in tqdm(all_profile_data):
        if not isinstance(x, dict):
            raise ValueError("Something is wrong with Supabase (registered_accounts)")

        if x["account_id"] not in player_rankable_map:
            continue

        if x["account_id"] in record_map:
            prev_min_record, prev_max_record = record_map[x["account_id"]]
            if prev_min_record["date"] > x["date"]:
                new_min_record = x
            else:
                new_min_record = prev_min_record

            if prev_max_record["date"] < x["date"]:
                new_max_record = x
            else:
                new_max_record = prev_max_record
            record_map[x["account_id"]] = (new_min_record, new_max_record)
        else:
            record_map[x["account_id"]] = (x, x)

    for min_record, max_record in record_map.values():
        if min_record == max_record:
            continue

        records.append(init_leaderboard_monthly_stats_record(
            year,
            month,
            player_rankable_map[max_record["account_id"]],
            max_record,
            min_record
        ))

    insert_all_leadeboard_monthly_stats_records_for_specific_date(records)

def insert_all_leadeboard_monthly_stats_records_for_specific_date(records):
    supabase = create_supabase_client()
    (
        supabase.table("leaderboard_monthly_stats")
        .insert(records)
        .execute()
    )

def diff_or_none_by_key(x, y, key):
    if x[key] is None or y[key] is None:
        return None

    return x[key] - y[key]

def init_leaderboard_monthly_stats_record(year, month, player_rankable, current_profile_record, previous_profile_record):
    return {
        "year": year,
        "month": month,
        "account_id": current_profile_record["account_id"],
        "stars": diff_or_none_by_key(current_profile_record, previous_profile_record, "stars") if player_rankable else None,
        "moons": diff_or_none_by_key(current_profile_record, previous_profile_record, "moons") if player_rankable else None,
        "diamonds": diff_or_none_by_key(current_profile_record, previous_profile_record, "diamonds") if player_rankable else None,
        "user_coins": diff_or_none_by_key(current_profile_record, previous_profile_record, "user_coins") if player_rankable else None,
        "demons": diff_or_none_by_key(current_profile_record, previous_profile_record, "demons") if player_rankable else None,
        "creator_points": diff_or_none_by_key(current_profile_record, previous_profile_record, "creator_points"),
    }

def fetch_all_profiles_in_specific_range(min_date, max_date):
    result = []
    for x in fetch_all_records(
        create_supabase_client()
        .table("profiles")
        .select("*")
        .gte("date", min_date)
        .lte("date", max_date)
        .order("date")
        .order("account_id")
    ):
        result.append(x)
    
    if len(result) == 0:
        print(f"Warning: zero profiles found when looking for range {min_date} - {max_date}")

    return result

def fetch_player_rankable_map():
    return {
        x["id"]: x["player_rankable"]  # type: ignore
        for x in (
            create_supabase_client()
            .table("accounts")
            .select("*")
            .eq("ignored", False)
            .eq("community_banned", False)
            .execute()
            .data
        )
    }

def delete_all_leaderboard_monthly_stats_in_specific_month(year, month):
    supabase = create_supabase_client()
    (
        supabase.table("leaderboard_monthly_stats")
        .delete()
        .eq("year", year)
        .eq("month", month)
        .execute()
    )

if __name__ == "__main__":
    chosen_year = int(sys.argv[1])
    chosen_month = int(sys.argv[2])
    insert_leaderboard_monthly(chosen_year, chosen_month)
