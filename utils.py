import json
import os

from dotenv import load_dotenv
import requests
from supabase import Client, create_client

def create_supabase_client():
    load_dotenv()
    supabase: Client = create_client(
        supabase_url=str(os.getenv("SUPABASE_URL")),
        supabase_key=str(os.getenv("SUPABASE_KEY")),
    )
    return supabase

def fetch_all_records(supabase_query_builder):
    """
    To make the result more deterministic,
    involve sorting in the query.
    """

    max_records_per_page = 1000
    first_index = 0
    stop = False
    while not stop:
        response = (
            supabase_query_builder
            .range(first_index, first_index + max_records_per_page - 1)
            .execute()
        )
        for x in response.data:
            if not isinstance(x, dict):
                raise ValueError("Something is wrong with Supabase (registered_accounts)")
            
            yield x

        if len(response.data) == max_records_per_page:
            first_index += max_records_per_page
        else:
            stop = True

def iter_fetchable_account_ids_and_player_ids():
    for x in fetch_all_records(
        create_supabase_client().table("accounts")
        .select("id", "player_id")
        .eq("ignored", False)
        .order("id")
    ):
        yield x["id"], x["player_id"]

def fetch_profile_from_gdbrowser_colon_with_account_id(account_id):
    req = request_get_until_not_error(f"https://gdbrowser.com/api/profile/{account_id}")
    result = req.text
    try:
        result = json.loads(result)
    except json.JSONDecodeError as e:
        print("Unexpected result:")
        print(result)
        raise e
    assert isinstance(result, dict)
    return result

def fetch_profile_from_gdbrowser_colon_with_player_id(player_id):
    req = request_get_until_not_error(f"https://gdbrowser.com/api/profile/{player_id}?player=true")
    result = req.text
    try:
        result = json.loads(result)
    except json.JSONDecodeError as e:
        print("Unexpected result:")
        print(result)
        raise e
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

def get_or_none(x, key_path, warn=True):
    keys = key_path.split(".")
    y = x
    for k in keys:
        if isinstance(y, dict):
            y = y.get(k, "???")
        else:
            y = "???"

        if y == "???":
            if warn:
                print(f"Warning: no value at {key_path}")
            
            y = None
            break
    
    return y

def insert_profile_into_supabase(date_str, profile):
    bulk_insert_profile_into_supabase([date_str], [profile])

def bulk_insert_profile_into_supabase(date_str_list, profile_list):
    supabase = create_supabase_client()

    n = len(date_str_list)
    assert n == len(profile_list)

    old_account_ids = set()
    old_color_ids = set()

    upsert_accounts_json_list = []
    upsert_colors_json_list = []
    insert_profiles_json_list = []

    for date_str, profile in zip(date_str_list, profile_list):
        get = lambda kp: get_or_none(profile, kp, warn=not any(
            kp.startswith(x) for x in [
            "classicLevelsCompleted",
            "platformerLevelsCompleted",
            "classicDemonsCompleted",
            "platformerDemonsCompleted",
        ]))
        account_id = get("accountID")
        
        # Update User ID (Player ID)
        if account_id not in old_account_ids:
            upsert_accounts_json_list.append(
                {"id": account_id, "player_id": get("playerID")}
            )
            old_account_ids.add(account_id)

        # Handle cube_id and color attributes (there are two scenario)
        icon_value = get("icon")
        if isinstance(icon_value, dict):
            print(f"Warning: rare profile structure, possibly hacker?")
            """
            Data example:
            "icon": {
                "icon": 1,
                "col1": 1,
                "col2": 1,
                "colG": 0,
                "glow": false
            },
            """

            cube_id = get("icon.icon")
            primary_color_id = get("icon.col1")
            secondary_color_id = get("icon.col2")
            glow_color_id = get("icon.colG")
            glow = get("icon.glow")

        else:
            cube_id = icon_value
            primary_color_id = get("col1")
            secondary_color_id = get("col2")
            glow_color_id = get("colG")
            glow = get("glow")

        # Insert color if not exists.
        if (
            primary_color_id is not None
            and primary_color_id not in old_color_ids
        ):
            upsert_colors_json_list.append({
                "id": primary_color_id,
                "red": get("col1RGB.r"),
                "green": get("col1RGB.g"),
                "blue": get("col1RGB.b"),
            })
            old_color_ids.add(primary_color_id)

        if (
            secondary_color_id is not None
            and secondary_color_id not in old_color_ids
        ):
            upsert_colors_json_list.append({
                "id": secondary_color_id,
                "red": get("col2RGB.r"),
                "green": get("col2RGB.g"),
                "blue": get("col2RGB.b"),
            })
            old_color_ids.add(secondary_color_id)

        if (
            glow_color_id is not None
            and glow_color_id not in old_color_ids
        ):
            if get("colGRGB") is not None:
                upsert_colors_json_list.append({
                    "id": glow_color_id,
                    "red": get("colGRGB.r"),
                    "green": get("colGRGB.g"),
                    "blue": get("colGRGB.b"),
                })
                old_color_ids.add(glow_color_id)

        # Insert profiles
        insert_profiles_json_list.append({
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
            "cube_id": cube_id,
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
            "glow": glow,
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
            "discord_id":
                get("discord"),
            "instagram_id":
                get("instagram"),
            "tiktok_id":
                get("tiktok"),
        })
    
    if len(upsert_accounts_json_list) > 0:
        (
            supabase.table("accounts")
            .upsert(upsert_accounts_json_list)
            .execute()
        )

    if len(upsert_colors_json_list) > 0:
        (
            supabase.table("colors")
            .upsert(upsert_colors_json_list)
            .execute()
        )

    (
        supabase.table("profiles")
        .insert(insert_profiles_json_list)
        .execute()
    )
    