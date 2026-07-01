"""
Character Location System
=========================

Provides helper functions for determining where characters are
located throughout the game world.

Character schedules are evaluated dynamically using the current
chapter and time of day, allowing NPCs to appear in different
locations as the story progresses.

Collaborates with
-----------------

• Characters
• Navigation
• World Map
• Dialogue
"""

init +1 python:    
    from collections import defaultdict

    def build_location_index():
        index = defaultdict(list)

        for char, rules in CHAR_SCHEDULES.items():
            for rule in rules:
                index[rule["location"]].append({
                    "char": char,
                    "tod": rule["tod"],
                    "chapter": rule["chapter"],
                })

        return index

    def get_char_location(cid, _tod = None, chapter = None):
        if _tod == None:
            _tod = tod
        if chapter == None:
            chapter = currentChapter

        for rule in CHAR_SCHEDULES.get(cid, []):
            if (
                _tod in rule["tod"]
            ) and (
                chapter in rule["chapter"]
            ):
                return rule["location"]

        return None

    def get_char_location_name(cid, _tod = None, chapter = None):
        if cid == "zero":
            return LOCATION_NAMES.get(f"{superLocation}_{navLocation}")

        if _tod == None:
            _tod = tod
        if chapter == None:
            chapter = currentChapter

        for rule in CHAR_SCHEDULES.get(cid, []):
            if (
                _tod in rule["tod"]
            ) and (
                chapter in rule["chapter"]
            ):
                return LOCATION_NAMES.get(rule["location"])

        return "Unknown"

    def get_chars_at(location = None, _tod = None, chapter = None):
        if location is None:
            location = f"{superLocation}_{navLocation}"
        if _tod == None:
            _tod = tod
        if chapter == None:
            chapter = currentChapter
        
        #Normalize input to list
        if isinstance(location, str):
            locations = [location]
        else:
            locations = list(location)

        result = []

        for loc in locations:
            for entry in CHAR_LOCATION_INDEX.get(loc, []):
                if (
                    _tod in entry["tod"]
                    and chapter in entry["chapter"]
                ):
                    result.append(entry["char"])

        return result

    def reverse_index_charlocations():
        global CHAR_LOCATION_INDEX
        CHAR_LOCATION_INDEX = build_location_index()

#################################### Data Stores - IMPORTANT: If a reference exists in these stores, then there HAS to be a corresponding image and label to navigate to.
default CHAR_LOCATION_INDEX = {}

define CHAR_SCHEDULES = {
    "nova": [
        {
            "location": "home_entranceisle2",
            "tod": {1},
            "chapter": {"1.1"},
        },
        {
            "location": "sr_parkrunestone",
            "tod": {2},
            "chapter": {"1.1"},
        },
        {
            "location": "home_study",
            "tod": {3},
            "chapter": {"1.1"},
        },
        {
            "location": "home_bath",
            "tod": {4},
            "chapter": {"1.1"},
        },
        {
            "location": "home_terraceleft",
            "tod": {5},
            "chapter": {"1.1"},
        },
        {
            "location": "home_novaroom",
            "tod": {6},
            "chapter": {"1.1"},
        },
    ],

    "yuki": [
        {
            "location": "home_shrine",
            "tod": {1},
            "chapter": {"1.1"},
        },
        {
            "location": "home_hubright",
            "tod": {2},
            "chapter": {"1.1"},
        },
        {
            "location": "sr_cafeoutdoor",
            "tod": {3},
            "chapter": {"1.1"},
        },
        {
            "location": "home_stonegarden2",
            "tod": {4},
            "chapter": {"1.1"},
        },
        {
            "location": "home_bath",
            "tod": {5},
            "chapter": {"1.1"},
        },
        {
            "location": "home_yukiroom",
            "tod": {6},
            "chapter": {"1.1"},
        },
    ],

    "alita": [
        {
            "location": "home_kitchen2",
            "tod": {1},
            "chapter": {"1.1"},
        },
        {
            "location": "home_bath",
            "tod": {2},
            "chapter": {"1.1"},
        },
        {
            "location": "home_gardenisle2",
            "tod": {3},
            "chapter": {"1.1"},
        },
        {
            "location": "nowhere",
            "tod": {4},
            "chapter": {"1.1"},
        },
        {
            "location": "home_hotspringgarden",
            "tod": {5},
            "chapter": {"1.1"},
        },
        {
            "location": "home_alitaroom",
            "tod": {6},
            "chapter": {"1.1"},
        },
    ],

    ########################## Side Chars #####################################
    "ella": [
        #TODO: 
        #{
        #    "location": "sr_cafeoutdoor",
        #    "tod": {1},
        #    "chapter": {"1.1"},
        #},
        {
            "location": "sr_cafeindoor",
            "tod": {1, 2, 3},
            "chapter": {"1.1"},
        },
    ],

    "nessa": [
        {
            "location": "sr_guildlobby",
            "tod": {1, 2, 3, 4},
            "chapter": {"1.1"},
        },
    ],

    "aria": [
        {
            "location": "sr_tavernindoor1",
            "tod": {2, 3, 4, 5},
            "chapter": {"1.1"},
        },
    ],

    "cyrus": [
        {
            "location": "sr_shoplobby",
            "tod": {1, 2, 3},
            "chapter": {"1.1"},
        },
    ],

    "lucan": [
        {
            "location": "sr_tavernindoor2",
            "tod": {2, 3, 4, 5},
            "chapter": {"1.1"},
        },
    ],

    "ezra": [
        {
            "location": "sr_guildfront",
            "tod": {4},
            "chapter": {"1.1"},
        },
    ],
}
