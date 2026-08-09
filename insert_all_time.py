import sys

from tqdm import tqdm

from utils import create_supabase_client

def extreme_demons_from_profile_data(x):
    classic = x["completed_classic_extreme_demons"]
    if classic is None:
        classic = 0

    platformer = x["completed_platformer_extreme_demons"]
    if platformer is None:
        platformer = 0

    return classic + platformer

def insert_leaderboard_all_time(chosen_date):
    delete_all_leaderboard_all_time_stats_in_specific_date(chosen_date)
    player_rankable_map = fetch_player_rankable_map()

    all_profile_data = fetch_all_profiles_in_specific_date(chosen_date)
    if len(all_profile_data) == 0:
        print("Warning: zero profiles found")

    records = []
    for x in tqdm(all_profile_data):
        if not isinstance(x, dict):
            raise ValueError("Something is wrong with Supabase (registered_accounts)")

        if x["account_id"] not in player_rankable_map:
            continue

        records.append(init_leaderboard_all_time_stats_record(chosen_date, player_rankable_map, x))

    insert_all_leadeboard_all_time_stats_records_for_specific_date(records)

def insert_all_leadeboard_all_time_stats_records_for_specific_date(records):
    supabase = create_supabase_client()
    (
        supabase.table("leaderboard_all_time_stats")
        .insert(records)
        .execute()
    )

def init_leaderboard_all_time_stats_record(date, player_rankable_map, profile_record):
    return {
        "date": date,
        "account_id": profile_record["account_id"],
        "stars": profile_record["stars"] if player_rankable_map[profile_record["account_id"]] else None,
        "moons": profile_record["moons"] if player_rankable_map[profile_record["account_id"]] else None,
        "diamonds": profile_record["diamonds"] if player_rankable_map[profile_record["account_id"]] else None,
        "user_coins": profile_record["user_coins"] if player_rankable_map[profile_record["account_id"]] else None,
        "demons": profile_record["demons"] if player_rankable_map[profile_record["account_id"]] else None,
        "extreme_demons": (
            extreme_demons_from_profile_data(profile_record)
            if player_rankable_map[profile_record["account_id"]] else None
        ),
        "creator_points": profile_record["creator_points"],
    }

def fetch_all_profiles_in_specific_date(chosen_date):
    return (
        create_supabase_client()
            .table("profiles")
            .select("*")
            .eq("date", chosen_date)
            .execute()
            .data
    )

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

def delete_all_leaderboard_all_time_stats_in_specific_date(chosen_date):
    supabase = create_supabase_client()
    (
        supabase.table("leaderboard_all_time_stats")
        .delete()
        .eq("date", chosen_date)
        .execute()
    )

if __name__ == "__main__":
    chosen_date = sys.argv[1]
    insert_leaderboard_all_time(chosen_date)
