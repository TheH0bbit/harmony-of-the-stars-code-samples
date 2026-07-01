"""
Location Definitions
====================

Contains shared location metadata used throughout the project.

Locations are grouped into logical collections representing
regions, buildings and gameplay areas. These groupings simplify
navigation, progression checks and gameplay queries elsewhere
in the project.
"""

init python:
    LOCATIONS_HOME_INSIDE = {"alitaroom", "bath", "dojo", "entrance", "hallwayleft", "hallwayright", "hotspringgarden", "hotspringmain", "shrine", "insignias1", "insignias2", "insignias3", "kitchen1", "kitchen2", "kitchen3", "livingroom1", "livingroom2", "mcroom", "novaroom", "spareroom",  "stonegarden1", "stonegarden2", "study", "yukiroom",}
    LOCATIONS_HOME_OUTSIDE = {"hub", "hubleft", "hubright", "corridorright", "corridorleft", "entranceisle1", "entranceisle2", "frontdoor", "frontgate", "connectorleft", "connectorright", "gardenisle1", "gardenisle2", "gardenisle3", "terraceleft", "stonefigures", "terraceright",}
    LOCATIONS_HOME = LOCATIONS_HOME_INSIDE | LOCATIONS_HOME_OUTSIDE

    LOCATIONS_SR_OUTSIDE = {"cafefront", "guildfront", "knot1", "knot2", "knot3", "parkarch", "parkpicnicarea", "parkrunestone", "tavernfront", "shopfront", "vionestatuefront",}
    LOCATIONS_SR_INSIDE = {"cafeindoor", "cafeoutdoor", "guildlobby", "guildlobbyleft", "guildlobbyright", "shopaisles", "shoplobby", "tavernindoor1", "tavernindoor2",}
    LOCATIONS_SR = LOCATIONS_SR_OUTSIDE | LOCATIONS_SR_INSIDE

    LOCATIONS_SROUTER_LAKE = {"lakeentrance", "lakemain", "lakeback", "lakeview"}
    LOCATIONS_SROUTER_RIDGE = {"ridgepath1", "ridgepath2", "ridgeshrinefront", "ridgeshrinemiddle", "ridgeshrineviewwest", "ridgeshrinevieweast", "ridgeshrineviewnorth"}


    #Lookup of audio at location
    def get_location_audio(superloc, loc, _tod):
        music_rules = LOCATION_MUSIC.get(superloc, [])
        ambience_rules = LOCATION_AMBIENCE.get(superloc, [])
        sfx_rules = LOCATION_SFX.get(superloc, [])
        music = None
        ambience = None
        sfx = None

        result = []

        #TODO: Same Routine 3 Times, modularize in Future!
        for rule in music_rules:
            if rule.get("default"):
                music = rule.get("music")
                continue

            if (
                loc in rule.get("locations", set())
                and _tod in rule.get("tod", {_tod})
            ):
                music = rule.get("music")
                break

        for rule in ambience_rules:
            if rule.get("default"):
                ambience = rule.get("ambience")
                continue

            if (
                loc in rule.get("locations", set())
                and _tod in rule.get("tod", {_tod})
            ):
                ambience = rule.get("ambience")
                break

        for rule in sfx_rules:
            if rule.get("default"):
                sfx = rule.get("sfx")
                continue

            if (
                loc in rule.get("locations", set())
                and _tod in rule.get("tod", {_tod})
            ):
                sfx = rule.get("sfx")
                break

        footsteps = get_footsteps(superloc, loc)

        #1st slot music, 2nd ambience, 3rd footsteps, 4th other sfx
        result.append(music)
        result.append(ambience)
        result.append(footsteps)
        result.append(sfx)

        return result

    def play_sounds_location(_superLocation=None, _location=None, _tod=None):
    
        if _superLocation is None:
            _superLocation = superLocation
        if _location is None:
            _location = navLocation
        if _tod is None:
            _tod = tod

        audio = get_location_audio(_superLocation, _location, _tod)

        if not audio:
            return
   
        if audio[0]:
            track, volume = audio[0]
            play_music(track, volume=volume, tod_sensitive=_tod)
               
        else:
            stop_music()

        if audio[1]:
            wanted = []
            for i, entry in enumerate(audio[1]):
                ambience, volume = entry
                play_ambience(ambience, volume=volume, channel = i, tod_sensitive=_tod)
                wanted.append(ambience)
            ambience_remove_unwanted(wanted_tracks = wanted)

        if audio[2] and audio[2] is not "none" and not last_location == new_location:
            global tempstring
            tempstring = _location
            play_footsteps(audio[2], "1", delay = 0.35, shuffle = True, channeloffset = 10, volume = 0.25)

        #if audio[3]:
        #    for i, entry in enumerate(audio[3]):
        #        sfx, volume = entry
        #        play_sfx(sfx, volume=volume, channel = i)
    
        return

    #Better lookuptable for Footsteps(original for easier authoring, this one for lookup), Run once during startup
    FOOTSTEPS_LOOKUP = {}

    def build_footstep_lookup():
        global FOOTSTEPS_LOOKUP
        lookup = {}

        for superloc, materials in FOOTSTEPS.items():
            for material, locations in materials.items():

                for loc in locations:
                    lookup[(superloc, loc)] = material

        FOOTSTEPS_LOOKUP = lookup

    def get_footsteps(superloc, loc):
        return FOOTSTEPS_LOOKUP.get(
            (superloc, loc),
            FOOTSTEP_DEFAULT.get(superloc)
        )

    ############################ MUSIC ################################
    LOCATION_MUSIC = {
        #HOME
        "home": [
            #{
            #    "locations": LOCATIONS_HOME_OUTSIDE,
            #    "music": ("home", 0.5),
            #},

            {
                "locations": {"hotspringgarden", "hotspringmain",},
                "music": ("onsen", 1),
            },

            # fallback rule
            {
                "default": True,
                "music": ("home", 1),
            }
        ],

        "sr": [
            # fallback rule
            {
                "locations": ("cafeindoor", "cafeoutdoor",),
                "music": ("HappyAvocado", 1),
            },
            {
                "locations": ("tavernindoor1", "tavernindoor2",),
                "music": ("tavern", 1),
            },
            {
                "locations": ("guildlobby", "guildlobbyleft", "guildlobbyright", ),
                "music": ("guild", 1),
            },
            {
                "default": True,
                "music": ("sr", 1),
            },
        ],
        "srouter": [
            {
                "locations": LOCATIONS_SROUTER_LAKE,
                "music": ("lake", 1),
            },
            {
                "locations": LOCATIONS_SROUTER_RIDGE,
                "tod": {NIGHT, MIDNIGHT},
                "music": ("night1", 1),
            },
            {
                "locations": LOCATIONS_SROUTER_RIDGE,
                "music": ("morningtwilight", 1),
            },

            # fallback rule
            {
                "default": True,
                "music": ("morningtwilight", 1),
            }
        ],

    }

    ############################ AMBIENCE ################################
    LOCATION_AMBIENCE = {
        #HOME
        "home": [
            {
                "locations": LOCATIONS_HOME_OUTSIDE,
                "ambience": (("nature_rustle", 0.2),),
            },
            {
                "locations": {"hotspringgarden", "hotspringmain",},
                "ambience": (("water_noises1", 0.15),),
            },

            # fallback rule
            {
                "default": True,
                "ambience": ((None, 0.5),),
            }
        ],

        "sr": [
            # fallback rule
            {
                "default": True,
                "ambience": ((None, 0.5),),
            }
        ],

        "srouter": [
            {
                "locations": LOCATIONS_SROUTER_RIDGE,
                "tod": {NIGHT, MIDNIGHT},
                "ambience": ((None, 0.3),),
            },
            {
                "locations": LOCATIONS_SROUTER_LAKE,
                "tod": {NIGHT, MIDNIGHT},
                "ambience": (("crickets", 0.4),),
            },
            {
                "locations": ("ridgeshrinemiddle", "ridgeshrinevieweast", "ridgeshrineviewwest", "ridgeshrineviewnorth",),
                "ambience": (("wind_medium", 0.5), ("nature_rustle", 0.2)),
            },
            {
                "locations": LOCATIONS_SROUTER_RIDGE,
                "ambience": (("nature_rustle", 0.5),),
            },
            {
                "locations": LOCATIONS_SROUTER_LAKE,
                "ambience": (("lake", 0.5),),
            },

            # fallback rule
            {
                "default": True,
                "ambience": ((None, 0.7),),
            }
        ],

    }

    ############################ OTHER SFX(NOT FOOTSTEPS, DEFAULT = NOTHING) ################################
    LOCATION_SFX = {
        #STILL USABLE, BUT ENTERING/LEAVING SOUNDS ARE NOW PART OF INTERACTABLES, TO MAKE WORK AGAIN UPDATE VALUES AND UNCOMMENT PLAY FUNCTINO ABOVE
        "home": [

            {
                "locations": {"alitaroom", "dojo", "hallwayright", "hallwayleft", "spareroom"},
                "sfx": (("slidingdoor", 2),),
            },

            {
                "locations": {"dojo"},
                "sfx": (("door_open1", 2),),
            },

            {
                "locations": {"cafeindoor"},
                "sfx": (("door_open1", 2),),
            },
        ]
    }

    ############################ FOOTSTEPS + DEFAULT TABLE ################################
    FOOTSTEP_DEFAULT = {
        "home": "soft",
        "sr": "stone",
        "srouter": "grass"
    }

    FOOTSTEPS = {

        "home": {
            #Homedefault is soft
            "sand": {"hub", "hubleft", "hubright", "stonefigures", "entranceisle2", "entranceisle1"},

            "wood": {"terraceright", "corridorright", "connectorright", "terraceleft", "corridorleft", "connectorleft", "hotspringmain", "hotspringgarden", "dojo", "study", "kitchen1", "kitchen2", "novaroom", "stonegarden1", "stonegarden2",},

            "stone": {"frontgate", "shrine", "frontdoor", }, 

            "none": {"insignias1", "insignias2", "insignias3", "bath", },
        },

        "sr": {
            "grass": {"parkarch", "parkpicnicarea", "parkrunestone", },

            "wood": {"cafeindoor", "tavernindoor1", "tavernindoor2", "shoplobby", "shopaisles", },

            "tile": {"cafeoutdoor", },
        },

        "srouter": {
            "dirt": {"ridgepath1", "ridgepath2", "ridgeshrinefront",},

            "wood": {"ridgeshrinemiddle", "ridgeshrinevieweast", "ridgeshrineviewnorth", "ridgeshrineviewwest"},
        }


    }

    LOCATION_NAMES = {
        # HOME
        "home_hub": "Home",
        "home_frontdoor": "Front Door",
        "home_hubleft": "Hub Left",
        "home_corridorleft": "Left Corridor",
        "home_terraceleft": "Left Terrace",
        "home_connectorleft": "Connector Left",
        "home_shrine": "Shrine",
        "home_insignias1": "Sacred Aspects",
        "home_insignias2": "Earthly Aspects",
        "home_insignias3": "Demonic Aspects",
        "home_bath": "Bath",
        "home_hotspringmain": "Hotspring Entrance",
        "home_hotspringgarden": "Hotspring",
        "home_hubright": "Hub Right",
        "home_stonefigures": "Stone Figures",
        "home_corridorright": "Right Corridor",
        "home_terraceright": "Garden Terrace",
        "home_gardenisle3": "Garden Isle",
        "home_gardenisle2": "Garden Isle",
        "home_gardenisle1": "Garden Isle",
        "home_entranceisle1": "Entrance Isle 1",
        "home_entranceisle2": "Entrance Isle 2",
        "home_frontgate": "Home",
        "home_connectorright": "Connector Right",
        "home_alitaroom": "Alita's Room",
        "home_entrance": "Entrance",
        "home_dojo": "Dojo",
        "home_study": "Study",
        "home_hallwayright": "Right Hallway",
        "home_spareroom": "Spare Room",
        "home_stonegarden2": "Stone Garden",
        "home_stonegarden1": "Stone Garden",
        "home_livingroom1": "Living Room",
        "home_livingroom2": "Living Room",
        "home_kitchen1": "Kitchen",
        "home_kitchen2": "Kitchen",
        "home_hallwayleft": "Left Hallway",
        "home_yukiroom": "Yuki's Room",
        "home_novaroom": "Nova's Room",
        "home_mcroom": "My Room",

        # SR (Town)
        "sr_knot1": "Town Square",
        "sr_knot2": "Plaza",
        "sr_knot3": "Passage",
        "sr_vionestatuefront": "Plaza Statue",
        "sr_vionestatueview": "Statue of Vione",
        "sr_shopfront": "Front of Shop",
        "sr_shoplobby": "The Happy Packrat",
        "sr_shopaisles": "The Happy Packrat - Aisles",
        "sr_guildfront": "Front of Guild",
        "sr_guildlobby": "Solstice Ridge Adventurers' Guild",
        "sr_guildlobbyleft": "",
        "sr_guildlobbyright": "",
        "sr_tavernfront": "Front of Tavern",
        "sr_cafefront": "Front of Café",
        "sr_cafeindoor": "Sweet Tooth Café",
        "sr_cafeoutdoor": "Sweet Tooth Café - Terrace",
        "sr_tavernindoor1": "The Solstice & Equinox",
        "sr_tavernindoor2": "The Solstice & Equinox - Bar",
        "sr_parkarch": "Dawnview Park",
        "sr_parkrunestone": "Dawnview Park - Runestone",
        "sr_parkpicnicarea": "Dawnview Park - Picnic Area",

        # SROUTER
        "srouter_lakeentrance": "Lake Entrance",
        "srouter_lakemain": "Lake",
        "srouter_lakeback": "Lake Back Area",
        "srouter_lakeview": "Lake View",
        "srouter_ridgepath1": "Path To Ridge",
        "srouter_ridgepath2": "Path To Ridge",
        "srouter_ridgeshrinefront": "The Solstice Ridge",
        "srouter_ridgeshrinemiddle": "Solstice Ridge Shrine",
        "srouter_ridgeshrineviewnorth": "Ridge View North",
        "srouter_ridgeshrinevieweast": "Ridge View East",
        "srouter_ridgeshrineviewwest": "Ridge View West",
    }