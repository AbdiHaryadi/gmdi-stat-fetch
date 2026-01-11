from datetime import datetime
from zoneinfo import ZoneInfo

from tqdm import tqdm

from utils import (
    create_supabase_client,
    fetch_profile_from_gdbrowser_colon,
    get_and_warn_if_not_exists,
    iter_current_registered_account_ids
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

    for account_id in iter_current_registered_account_ids():
        if account_id in existing_account_ids:
            continue

        yield account_id

supabase = create_supabase_client()

date_str = str(datetime.now(ZoneInfo("Asia/Jakarta")).date())
account_id_list = [x for x in iter_current_registered_account_ids_without_profiles(date_str)]
print(f"Total:", len(account_id_list))

for account_id in tqdm(account_id_list):
    print(f"Processing {account_id} ....")
    profile = fetch_profile_from_gdbrowser_colon(account_id)

    get = lambda kp: get_and_warn_if_not_exists(profile, kp)
    # Update User ID (Player ID)
    (
        supabase.table("accounts")
        .upsert({"id": account_id, "user_id": get("playerID")})
        .execute()
    )

    # Insert color if not exists.
    primary_color_id = get("col1")
    if primary_color_id is not None:
        (
            supabase.table("colors")
            .upsert({
                "id": primary_color_id,
                "red": get("col1RGB.r"),
                "green": get("col1RGB.g"),
                "blue": get("col1RGB.b"),
            })
            .execute()
        )

    secondary_color_id = get("col2")
    if secondary_color_id is not None:
        (
            supabase.table("colors")
            .upsert({
                "id": secondary_color_id,
                "red": get("col2RGB.r"),
                "green": get("col2RGB.g"),
                "blue": get("col2RGB.b"),
            })
            .execute()
        )

    glow_color_id = get("colG")
    if glow_color_id is not None:
        (
            supabase.table("colors")
            .upsert({
                "id": glow_color_id,
                "red": get("colGRGB.r"),
                "green": get("colGRGB.g"),
                "blue": get("colGRGB.b"),
            })
            .execute()
        )

    # Insert profiles
    (
        supabase.table("profiles")
        .insert({
            "date": date_str,
            "account_id": account_id,
            "username":
                get("username"),
            "global_rank":
                get("rank"),
            "stars":
                get("stars"),
            "moons":
                get("moons"),
            "diamonds":
                get("diamonds"),
            "secret_coins":
                get("coins"),
            "user_coins":
                get("userCoins"),
            "demons":
                get("demons"),
            "creator_points":
                get("cp"),
            "completed_classic_auto_levels":
                get("classicLevelsCompleted.auto"),
            "completed_classic_easy_levels":
                get("classicLevelsCompleted.easy"),
            "completed_classic_normal_levels":
                get("classicLevelsCompleted.normal"),
            "completed_classic_hard_levels":
                get("classicLevelsCompleted.hard"),
            "completed_classic_harder_levels":
                get("classicLevelsCompleted.harder"),
            "completed_classic_insane_levels":
                get("classicLevelsCompleted.insane"),
            "completed_classic_daily_levels":
                get("classicLevelsCompleted.daily"),
            "completed_classic_gauntlet_levels":
                get("classicLevelsCompleted.gauntlet"),
            "completed_platformer_auto_levels":
                get("platformerLevelsCompleted.auto"),
            "completed_platformer_easy_levels":
                get("platformerLevelsCompleted.easy"),
            "completed_platformer_normal_levels":
                get("platformerLevelsCompleted.normal"),
            "completed_platformer_hard_levels":
                get("platformerLevelsCompleted.hard"),
            "completed_platformer_harder_levels":
                get("platformerLevelsCompleted.harder"),
            "completed_platformer_insane_levels":
                get("platformerLevelsCompleted.insane"),
            "completed_platformer_daily_levels":
                get("platformerLevelsCompleted.daily"),
            "completed_classic_easy_demons":
                get("classicDemonsCompleted.easy"),
            "completed_classic_medium_demons":
                get("classicDemonsCompleted.medium"),
            "completed_classic_hard_demons":
                get("classicDemonsCompleted.hard"),
            "completed_classic_insane_demons":
                get("classicDemonsCompleted.insane"),
            "completed_classic_extreme_demons":
                get("classicDemonsCompleted.extreme"),
            "completed_classic_weekly_demons":
                get("classicDemonsCompleted.weekly"),
            "completed_classic_gauntlet_demons":
                get("classicDemonsCompleted.gauntlet"),
            "completed_platformer_easy_demons":
                get("platformerDemonsCompleted.easy"),
            "completed_platformer_medium_demons":
                get("platformerDemonsCompleted.medium"),
            "completed_platformer_hard_demons":
                get("platformerDemonsCompleted.hard"),
            "completed_platformer_insane_demons":
                get("platformerDemonsCompleted.insane"),
            "completed_platformer_extreme_demons":
                get("platformerDemonsCompleted.extreme"),
            "cube_id":
                get("icon"),
            "ship_id":
                get("ship"),
            "ball_id":
                get("ball"),
            "ufo_id":
                get("ufo"),
            "wave_id":
                get("wave"),
            "robot_id":
                get("robot"),
            "spider_id":
                get("spider"),
            "swing_id":
                get("swing"),
            "jetpack_id":
                get("jetpack"),
            "primary_color_id": primary_color_id,
            "secondary_color_id": secondary_color_id,
            "glow":
                get("glow"),
            "glow_color_id": glow_color_id,
            "death_effect_id":
                get("deathEffect"),
            "friend_request_permission":
                get("friendRequests"),
            "message_permission":
                get("messages"),
            "moderator_level":
                get("moderator"),
            "youtube_id":
                get("youtube"),
            "twitter_id":
                get("twitter"),
            "twitch_id":
                get("twitch"),
        })
        .execute()
    )

    print("Warning: early break for testing")
    break

print("Done!")
