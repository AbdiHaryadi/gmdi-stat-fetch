import datetime
import sys

from tqdm import tqdm

from utils import create_supabase_client

def insert_leaderboard_weekly(chosen_date):
    delete_all_leaderboard_weekly_stats_in_specific_date(chosen_date)
    player_rankable_map = fetch_player_rankable_map()

    previous_date = (
        datetime.date.strptime(chosen_date, "%Y-%m-%d")
        - datetime.timedelta(days=7)
    ).strftime("%Y-%m-%d")

    all_current_profile_data = fetch_all_profiles_in_specific_date(chosen_date)
    all_previous_profile_data = fetch_all_profiles_in_specific_date(previous_date)

    records = []
    for x in tqdm(all_current_profile_data):
        if not isinstance(x, dict):
            raise ValueError("Something is wrong with Supabase (registered_accounts)")

        if x["account_id"] not in player_rankable_map:
            continue

        for prev_x in all_previous_profile_data:
            if prev_x["account_id"] == x["account_id"]:  # type: ignore
                break
        else:
            continue

        records.append(init_leaderboard_weekly_stats_record(
            chosen_date,
            player_rankable_map[x["account_id"]],
            x,
            prev_x
        ))

    insert_all_leadeboard_weekly_stats_records_for_specific_date(records)

def insert_all_leadeboard_weekly_stats_records_for_specific_date(records):
    supabase = create_supabase_client()
    (
        supabase.table("leaderboard_weekly_stats")
        .insert(records)
        .execute()
    )

def diff_or_none_by_key(x, y, key):
    if x[key] is None or y[key] is None:
        return None

    return x[key] - y[key]

def init_leaderboard_weekly_stats_record(date, player_rankable, current_profile_record, previous_profile_record):
    return {
        "date": date,
        "account_id": current_profile_record["account_id"],
        "stars": diff_or_none_by_key(current_profile_record, previous_profile_record, "stars") if player_rankable else None,
        "moons": diff_or_none_by_key(current_profile_record, previous_profile_record, "moons") if player_rankable else None,
        "diamonds": diff_or_none_by_key(current_profile_record, previous_profile_record, "diamonds") if player_rankable else None,
        "user_coins": diff_or_none_by_key(current_profile_record, previous_profile_record, "user_coins") if player_rankable else None,
        "demons": diff_or_none_by_key(current_profile_record, previous_profile_record, "demons") if player_rankable else None,
        "creator_points": diff_or_none_by_key(current_profile_record, previous_profile_record, "creator_points"),
    }

def fetch_all_profiles_in_specific_date(chosen_date):
    result = (
        create_supabase_client()
            .table("profiles")
            .select("*")
            .eq("date", chosen_date)
            .execute()
            .data
    )
    if len(result) == 0:
        print(f"Warning: zero profiles found when looking for {chosen_date}")

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

def delete_all_leaderboard_weekly_stats_in_specific_date(chosen_date):
    supabase = create_supabase_client()
    (
        supabase.table("leaderboard_weekly_stats")
        .delete()
        .eq("date", chosen_date)
        .execute()
    )

if __name__ == "__main__":
    chosen_date = sys.argv[1]
    insert_leaderboard_weekly(chosen_date)
