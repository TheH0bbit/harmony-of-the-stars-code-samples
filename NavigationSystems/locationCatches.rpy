"""
Location Event System
=====================

Evaluates location-specific gameplay events when the player enters
or interacts with a location.

Events can depend on factors such as:

• Story progression
• Time of day
• Character state
• Progression flags
• Special conditions

This allows locations to react dynamically to the current game
state without embedding progression logic directly into navigation.
"""

init python:
    def check_catches_location(_superLocation=None, _location=None, _tod=None, special=None):
        global navLocation

        if _superLocation is None:
            _superLocation = superLocation
        if _location is None:
            _location = navLocation
        if _tod is None:
            _tod = tod

        searchID = f"{_superLocation}_{_location}"
        
        if special:
            searchID = special

        rules = LOCATION_CATCHES.get(searchID)
        if not rules:
            return None

        for rule in rules:

            # TOD check
            if _tod not in rule.get("tod", {_tod}):
                continue

            trigger = rule.get("trigger", set()) #using tuples, sue me! trigger[0] holds the flags, trigger[1] holds the flags_container and trigger[2] holds the flags_identifier(unless STORY)
            bypass = rule.get("bypass", set())

            # trigger flags
            if trigger and trigger[1] == STORY:
                if not flags.story.has_any("", trigger[0]):
                    continue

            elif trigger and not flags.get(trigger[1]).has_any(trigger[2], trigger[0]):
                continue

            # bypass flags
            if bypass and bypass[1] == STORY:
                if flags.story.has_any("", bypass[0]):
                    continue

            elif bypass and flags.get(bypass[1]).has_any(bypass[2], bypass[0]):
                continue

            navLocation = prevNavLocation
            if not rule.get("target"):
                return "wrong_place"

            return rule.get("target")
        return None

    def check_blocks_superlocation(_superLocation=None, _tod=None):
        if _superLocation is None:
            _superLocation = superLocation
        if _tod is None:
            _tod = tod

        rules = SUPERLOCATION_BLOCKS.get(_superLocation)
        if not rules:
            return None

        for rule in rules:
            # TOD check
            if _tod not in rule.get("tod", {_tod}):
                continue

            trigger = rule.get("trigger", set()) #using tuples, sue me! trigger[0] holds the flags, trigger[1] holds the flags_container and trigger[2] holds the flags_identifier(unless STORY)
            bypass = rule.get("bypass", set())

            # trigger flags
            if trigger and trigger[1] == STORY:
                renpy.log(f"triggered potential Story catch: {trigger[0]}")
                if not flags.story.has_any("", trigger[0]):
                    renpy.log(f"not triggering: {trigger[0]}")
                    continue

            elif trigger and not flags.get(trigger[1]).has_any(trigger[2], trigger[0]):
                continue

            # bypass flags
            if bypass and bypass[1] == STORY:
                if flags.story.has_any("", bypass[0]):
                    continue

            elif bypass and flags.get(bypass[1]).has_any(bypass[2], bypass[0]):
                continue

            if not rule.get("target"):
                return "leave_blocked"

            return rule.get("target")
        return None





    #Special Catches when trying to ENTER locations, triggered if "flags" in flagsSuper, ignored if "bypass" in flagsSuper
    LOCATION_CATCHES = {
        #HOME
        "home_kitchen1": [
            {
                "bypass": ({"visited_mcroom",}, STORY),
                "target": "visit_mcroom",
            },
            {
                "bypass": ({"visited_novaroom",}, STORY),
                "target": "visit_novaroom",
            },

        ],
        "home_livingroom1": [
            {#TODO: catches should not trigger events, only block stuff... move and change this to charactersData later
                "bypass": ({"main1_3",}, STORY),
                "target": "prologue_final_1",
            },
        ],
        "home_livingroom2": [
            {#TODO: catches should not trigger events, only block stuff... move and change this to charactersData later
                "bypass": ({"main1_3",}, STORY),
                "target": "prologue_final_1",
            },
        ],
        "home_stonegarden1": [
            {
                "bypass": ({"visited_mcroom",}, STORY),
                "target": "visit_mcroom",
            },
            {
                "bypass": ({"visited_novaroom",}, STORY),
                "target": "visit_novaroom",
            },
        ],
        "home_mcroom": [
            {
                "bypass": ({"visited_mcroom",}, STORY),
                "target": "visiting_mcroom",
            },
        ],
        "home_novaroom": [
            {
                "bypass": ({"visited_mcroom",}, STORY),
                "target": "visit_mcroom",
            },
            {#TODO: catches should not trigger events, only block stuff... move and change this to charactersData later
                "bypass": ({"visited_novaroom",}, STORY),
                "target": "prologue_talknova_1",
            },
        ],

        "home_bath": [
            {
                "tod": {NIGHT},
                "trigger": None,
                "bypass": None,
                "target": "yuki_jump",
            },
            {
                "tod": {EVENING},
                "target": "nova_jump",
            },
        ],


        ############################# SOLSTICE RIDGE ###################################

        "sr_cafeindoor": [
            {
                "tod": {NOON, AFTERNOON},
                "trigger": ({"first_day",}, STORY), 
                "bypass": ({"meet_ella",}, CHAR, "ella"),
                "target": "first_meet_ella",
            },
            {
                "tod": {EVENING, NIGHT, MIDNIGHT},
                "target": "cafe_closed",
            },
        ],

        "sr_tavernindoor1": [
            {
                "trigger": ({"first_day",}, STORY),
                "bypass": ({"main2_2",}, STORY),
            },
            {
                "tod": {MIDNIGHT},
                "target": "tavern_closed",
            },

        ],
        "sr_tavernindoor2": [
            {
                "trigger": ({"first_day",}, STORY),
                "bypass": ({"main2_2",}, STORY),
            },
            {
                "tod": {MIDNIGHT},
                "target": "tavern_closed",
            },

        ],

        "sr_shoplobby": [
            {
                "trigger": ({"first_day",}, STORY),
                "bypass": ({"main2_1",}, STORY),
            },
            {
                "tod": {EVENING, NIGHT, MIDNIGHT},
                "target": "shop_closed",
            },
        ],

        "sr_guildlobby": [
            {
                "tod": {NIGHT, MIDNIGHT},
                "target": "guild_closed",
            },
        ],

        #Special Catches
        "sleep": [
            {
                "bypass": ({"main2_2",}, STORY),
                "target": "sleep_blocked",
            },
        ],
    }

    #Special Catches when trying to LEAVE super locations, triggered if "flags" in flagsSuper, ignored if "bypass" in flagsSuper
    SUPERLOCATION_BLOCKS = {
        "home": [
            {
                "bypass": ({"main1_3",}, STORY),
            },
        ],
        "sr": [
            {
                "trigger": ({"first_day",}, STORY),
                "bypass": ({"main2_1",}, STORY),
                "target": "first_day_guild",
            },
            {
                "trigger": ({"main2_1",}, STORY),
                "bypass": ({"main2_2",}, STORY),
                "target": "first_day_shop",
            },
        ],
    }

############################### CATCH LABELS ###############################
label cafe_closed:
    think "...The Sweet Tooth Café is closed..."
    think"...Guess I'll return tomorrow..."
    jump current_location

label shop_closed:
    think "...The Happy Packrat is closed..."
    think"...Guess I'll return tomorrow..."
    jump current_location

label guild_closed:
    think "...The Adventurers Guild is closed..."
    think"...Guess I'll return tomorrow..."
    jump current_location

label tavern_closed:
    think "...The Solstice & Equinox is closed..."
    think"...Guess I'll return tomorrow..."
    jump current_location

label sleep_blocked:
    think "I can't go to sleep yet... There's still things to do."
    jump current_location

label leave_blocked:
    think "I can't leave yet."
    jump current_location

label wrong_place:
    think "No, this isn't where I need to go right now..."
    jump current_location

label dungeon_late:
    think "...It's probably a little late to journey to a dungeon..."
    ""
###################

label first_day_guild:
    think "I can't leave yet, we need to go to the {b}Adventurers Guild{/b}!"
    jump current_location

label first_day_shop:
    think "Still can't leave, first we have to pay a visit to {b}The Happy Packrat{/b} and get ourselves a new sword!"
    jump current_location

label visit_mcroom:
    think "I should first check out my old room."
    jump current_location

label visit_novaroom:
    think "First I need to tell Nova that dinner is ready."
    jump current_location

label visiting_mcroom:
    #$ renpy.log("hit label visiting mcroom")
    $ set_current_location("home", "mcroom")
    call current_location_bgonly from _call_current_location_bgonly
    call close_all_screens from _call_close_all_screens
    pause(2)
    think "{=murmur}Wow..."
    think "My old room...{w=1} they really didn't change a thing."
    think "It's just like how I remember it."
    think "..."
    think "Thinking how many hours I spent in this room...{w=1} it really feels like home~"
    think "Mr. Dymond... {w=1}Yuki...{w=1} You really are the best!"
    $ flags.story.set("", "visited_mcroom")
    jump current_location

label first_meet_ella:
    think "...I want to say hi to Ella, but perhaps it would be smarter in the {b}morning{/b}, when there are less customers..."
    jump current_location