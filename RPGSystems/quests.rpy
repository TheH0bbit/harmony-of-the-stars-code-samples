"""
Quest System
============

Implements the quest management framework used throughout
Harmony of the Stars.

Responsibilities
----------------

• Quest lifecycle management
• Stage progression
• Completion tracking
• Requirement validation
• Quest metadata access
• Integration with rewards and notifications

Architecture
------------

Quest definitions are stored separately from quest state.

Static quest information (titles, stages, rewards, descriptions,
etc.) is defined in QUEST_DEFS, while this module is responsible
for tracking each player's current progression.

Requirements are evaluated dynamically through other gameplay
systems such as inventory, character progression and global flags.

Collaborates with
-----------------

• Inventory
• Flag System
• Characters
• UI / Notifications
• Rewards

#Set containing all quest related flags
default quest_states = {}
default quests = QuestManager()

"""

init python:
    class QuestManager:
        def __init__(self):
            pass

        # Initializes a quest and creates its runtime state.
        def start(self, qid):
            if qid not in QUEST_DEFS:
                return

            if qid in quest_states:
                return

            quest_states[qid] = {
                "active": True,
                "stage": 0,
                "completed": False
            }

            add_popup_quest(qid, STARTED)


        def get_active_quests(self):
            return [(qid, state) for qid, state in quest_states.items() if state.get("active") and not state.get("completed")]

        def get_completed_quests(self):
            return [(qid, state) for qid, state in quest_states.items() if state.get("completed")]

        def get_title(self, qid):
            renpy.log(f"qid: {qid}")
            return QUEST_DEFS.get(qid).get("title")

        def get_name(self, qid):
            return QUEST_DEFS.get(qid).get("name")

        def get_type(self, qid):
            return QUEST_DEFS.get(qid).get("type")

        def get_type_string(self, qid):
            return QUESTTYPES[QUEST_DEFS.get(qid).get("type")]

        def get_bg(self, qid):
            return QUEST_DEFS.get(qid).get("bg")

        def get_bgslide(self, qid):
            return QUEST_DEFS.get(qid).get("bgslide")

        def get_icon(self, qid):
            return QUEST_DEFS.get(qid).get("icon")

        def get_char(self, qid):
            return QUEST_DEFS.get(qid).get("char")

        def get_description(self, qid):
            return QUEST_DEFS.get(qid).get("description")

        def get_hint(self, qid):
            if self.get_stage_data(qid) and self.get_stage_data(qid).get("tip"):
                return self.get_stage_data(qid).get("tip")
            return None

        def get_stage(self, qid):
            state = quest_states.get(qid)
            if not state:
                return None
            return state["stage"]

        def get_stage_data(self, qid):
            stage = self.get_stage(qid)
            state = quest_states.get(qid)
            if stage is None:
                return None
            if state["completed"]:
                return None
            
            return QUEST_DEFS[qid]["stages"][stage]

        def get_stage_data_completed(self, qid):          
            stage = self.get_stage(qid)
            if stage is None:
                return None
            return [stage_data for i, stage_data in enumerate(QUEST_DEFS[qid]["stages"]) if i < stage]

        def get_stage_data_full(self, qid):          
            return QUEST_DEFS[qid]["stages"]

        def check_requirements(self, req):
            if not req:
                return True
            
            # money
            if "money" in req:
                if mainInventory.money < req["money"]:
                    return False

            # items
            if "items" in req:
                for item, amount in req["items"]:
                    if not mainInventory.check_item_amount(item, amount):
                        return False

            # flags
            if "flags" in req:
                for f in req["flags"]:
                    if not flags.has_flag(f["category"], f["identifier"], f["flag"]):
                        return False

            if "levels" in req:
                for data in req["levels"]:
                    char = gc(data.get("char"))
                    if data.get("level") and char.get_level < data.get("level"):
                        return False
                    if data.get("clevel") and char.get_clevel < data.get("clevel"):
                        return False

            return True

        def check_stage_complete(self, qid):
            stage = self.get_stage_data(qid)
            if not stage:
                return False
            
            return self.check_requirements(stage.get("requirements"))

        def advance(self, qid):
            if qid not in quest_states:
                return
            
            reward = self.get_stage_data(qid).get("reward")
            if reward:
                reward.apply()

            state = quest_states[qid]
            state["stage"] += 1

            if state["stage"] >= len(QUEST_DEFS[qid]["stages"]):
                self.complete(qid)
            else:
                add_popup_quest(qid, UPDATED)

        def complete(self, qid):
            state = quest_states.get(qid)
            if not state:
                return

            add_popup_quest(qid, COMPLETED)

            state["completed"] = True
            state["active"] = False

        def check_updates(self):
            for qid, state in quest_states.items():
            
                if not state["active"]:
                    continue

                if self.check_stage_complete(qid):
                    self.advance(qid)


    #Static quest data, build to dynamic quest containers... need to adapt to update changes from changes to static data again
    QUEST_DEFS = {
        "main1": {
            "title": "Main Quest 1",
            "name": "Coming Home",
            "type": MAINQUEST,
            "bg": False,
            "bgslide": False,
            "icon": False,
            "char": None,
            "description": "You have finally returned home after three years... Time to get reacquainted with everything!",
            "stages": [
                {
                    "description": "Your old childhood room is right around the corner... what are you waiting for, let's go take a look!",
                    "tip": "Click on the middle door in the western hallway.",
                    "requirements": {
                        "text": "Go into your room.",
                        "flags": (
                            {
                                "category": STORY,
                                "identifier": "",
                                "flag": "visited_mcroom" #main1_1
                            },
                        ),
                    },
                },
                {
                    "description": "Check up on Nova in her new room and tell her that dinner is about to be ready!",
                    "tip": "Click on the furthest door in the western hallway.",
                    "requirements": {
                        "text": "Check up on Nova.",
                        "flags": (
                            {
                                "category": STORY,
                                "identifier": "",
                                "flag": "visited_novaroom" #main1_2
                            },
                        ),
                    },
                },
                {
                    "description": "Meet up with the others!",
                    "tip": "Be sure to check out the living room.",
                    "requirements": {
                        "text": "Meet up with the others in the Kitchen.",
                        "flags": (
                            {
                                "category": STORY,
                                "identifier": "",
                                "flag": "main1_3"
                            },
                        ),
                    },
                    "reward": Reward(
                        money=50,
                        flags=(
                            {"category": STORY, "identifier": "", "flag": "main1_done"},
                        ),
                    ),
                },
            ],
        },
        #First adventure
        "main2": {
            "title": "Main Quest 2",
            "name": "Your first adventure",
            "type": MAINQUEST,
            "bg": False,
            "bgslide": False,
            "icon": False,
            "char": None,
            "description": "You are about to embark on your first adventure together! Though you should probably prepare for it first.",
            "stages": [
                {
                    "description": "Go into town and register as an adventuring party at the local Adventurers Guild branch",
                    "tip": "Go to the townsquare by clicking the map icon or clicking the main entrance, then select townsquare. From there navigate to the Adventurers Guild, the big building opposite the townsquare.",
                    "requirements": {
                        "text": "Go into town and register as an adventuring party.",
                        "flags": (
                            {
                                "category": STORY,
                                "identifier": "",
                                "flag": "main2_1"
                            },
                        ),
                    },
                },
                {
                    "description": "You are now registered as adventurers! Though you need to get some equipment first.",
                    "tip": "Pay a visit to the Happy Packrat, located on the east side of the townsquare.",
                    "requirements": {
                        "text": "Visit the Happy Packrat",
                        "flags": (
                            {
                                "category": STORY,
                                "identifier": "",
                                "flag": "main2_2"
                            },
                        ),
                    },
                    "reward": Reward(
                        items = (("magicwand", 1), ("yukibow", 1) ),
                    ),
                },
                {
                    "description": "Finally, you are ready to embark on your first adventure! Open the Worldmap and set out on your journey into the Moonlit Woods. You might want to actually equip your weapons first though!",
                    "tip": "You can open the Worldmap by clicking on the bottom left square of the townmap menu. From there click on the area you wish to travel and select Journey.",
                    "requirements": {
                        "text": "Embark on your first adventure.",
                        "flags": (
                            {
                                "category": STORY,
                                "identifier": "",
                                "flag": "main2_3"
                            },
                        ),
                    },
                    "reward": Reward(
                        money=150,
                        flags=(
                            {"category": STORY, "identifier": "", "flag": "main2_done"},
                        ),
                    ),
                },
            ],
        },
        #Ceecee Meet
        "main3": {
            "title": "Main Quest 3",
            "name": "A Sticky Situation",
            "type": MAINQUEST,
            "bg": False,
            "bgslide": False,
            "icon": False,
            "char": None,
            "description": "You could have sworn you saw {b}something{/b} at the far side of the lake...",
            "stages": [
                {
                    "description": "Visit the lake from time to time during the day",
                    "tip": "Wait for a bit then go to the lake during the day!",
                    "requirements": {
                        "text": "Visit the Lake from time to time.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "ceecee",
                                "flag": "ceecee_meet_2" #given by event
                            },
                        ),
                    },
                },
                {
                    "description": "You definitely saw a blue girl in the lake this time, no doubt about it! Perhaps Yuki knows something about it?",
                    "tip": "Talk to Yuki about the girl in the lake!",
                    "requirements": {
                        "text": "Talk to Yuki.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "ceecee",
                                "flag": "ceecee_meet_3_pre1" #given by talk yuki, enables ceecee_meet_3 event
                            },
                        ),
                    },
                },
                {
                    "description": "You talked with Yuki, and she told you about the myth regarding that girl. You want to learn more about her, but for that you need her to trust you more. Yuki thought perhaps you could use some kind of gift to lure her closer and gain her trust then... Perhaps something sweet?",
                    "tip": "Buy a set of cupcakes at the Sweettooth Café, then visit the lake again during the day!",
                    "requirements": {
                        "text": "Buy a gift, then visit the lake again.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "ceecee",
                                "flag": "ceecee_meet_3" #given by event, enables talk with Yuki
                            },
                        ),
                    },

                },
                {
                    "description": "The cupcakes actually worked! The girl in the lake seemed to enjoy them, until sadly she was spooked away by a couple fellow adventurers arriving at the lake... but no matter! You should go tell Yuki all about it!",
                    "tip": "Talk to Yuki about what you learned!",
                    "requirements": {
                        "text": "Talk to Yuki.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "ceecee",
                                "flag": "ceecee_meet_4_pre1" #given by talk yuki, enables ceecee_meet_4
                            },
                        ),
                    },
                },
                {
                    "description": "You need to come up with some sort of plan on how to deal with this girls situation... ",
                    "tip": "Go on with your day-to-day, something will happen soon.",
                    "requirements": {
                        "text": "Go on with your day-to-day.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "ceecee",
                                "flag": "ceecee_meet_4" #given by event
                            },
                        ),
                    },
                    "reward": Reward(
                        money=100,
                        flags=(
                            {"category": STORY, "identifier": "", "flag": "main3_done"},
                        ),
                    ),
                },
            ],
        },
        #Solaria Meet
        "main4": {
            "title": "Main Quest 4",
            "name": "Shadow on the Walls",
            "type": MAINQUEST,
            "bg": False,
            "bgslide": False,
            "icon": False,
            "char": None,
            "description": "Something weird has happened. While you were casually walking through town, Nova was hit with a strange sensation, that we were being watched. Unsure what to make of this, you continue on with your day-to-day, but one thing is clear... {b}something{/b} fishy is going on.",
            "stages": [
                {
                    "description": "Keep going on with your day-to-day and visit the townsquare from time to time.",
                    "tip": "Wait for a bit then visit the townsquare during the day!",
                    "requirements": {
                        "text": "Visit the townsquare from time to time.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "solaria",
                                "flag": "solaria_meet_2" #given by event, enables talk
                            },
                        ),
                    },
                },
                {
                    "description": "The whole day you felt as if you were being watched... and even more importantly, you saw a human-shaped shadow cast on a wall, which could only have originated from the top of the nearby watchtower! Nova was right, someone is watching you... better go and talk to her.",
                    "tip": "Talk to Nova about your shadow!",
                    "requirements": {
                        "text": "Talk to Nova.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "solaria",
                                "flag": "solaria_meet_3_pre1" #given by talk nova, enables solaria_meet_3 event
                            },
                        ),
                    },
                },
                {
                    "description": "You talked with Nova about the stalker. Apparently Nova did not have an experience like the one from earlier again, so you came to the conclusion that the stalker is only after you? Though you can't imagine why... You told Nova that you would come up with some sort of plan to deal with this situation. Perhaps you can find something at the Happy Packrat that will help?",
                    "tip": "Buy a nettrap at the Happy Packrat, then visit the townsquare again in the evening!",
                    "requirements": {
                        "text": "Find a tool to help you stop the stalker and visit the townsquare in the evening.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "solaria",
                                "flag": "solaria_meet_3" #given by event, enables meet_4
                            },
                        ),
                    },
                },
                {
                    "description": "Your stalker is real... and apparently much more capable than you as well! They cut down the nettrap before it even hit them, which requires an incredible amount of skill! Our plan failed, so it's back to the drawing board for now...",
                    "tip": "Go on with your day-to-day, something will happen soon.",
                    "requirements": {
                        "text": "Go on with your day-to-day.",
                        "flags": (
                            {
                                "category": CHAR,
                                "identifier": "solaria",
                                "flag": "solaria_meet_4" #given by event
                            },
                        ),
                    },
                    "reward": Reward(
                        money=100,
                        flags=(
                            {"category": STORY, "identifier": "", "flag": "main4_done"},
                        ),
                    ),
                },
            ],
        },
        #First Super quest(Super Quests are the ones that gatekeep the next story part, requirements are often mainquest flags)
        "super1": {
            "title": "Chapter 1.1",
            "name": "~ Welcome to Solstice Ridge ~",
            "type": MAINQUEST,
            "bg": False,
            "bgslide": False,
            "icon": False,
            "char": None,
            "description": "You are finally back in Solstice Ridge... {b}Home{/b}. And your plan is clear, find our more about this Organization, and start out as adventurers! Perhaps you'll even meet some new faces along the way?)",
            "stages": [
                {
                    "description": "Lots of things to do, for now, try to finish off all available Main Quests and advance all Characters Adventurer and Relationship Levels!",
                    "tip": "If you are unsure what to do, just take a look at Mainquests 2, 3 and 4 and make sure all Characters have reached their required levels.",
                    "requirements": {
                        "flags": (
                            {
                                "text": "Complete Mainquest 2 - Your First Adventure",
                                "category": STORY,
                                "identifier": "",
                                "flag": "main2_done",
                            },
                            {
                                "text": "Complete Mainquest 3 - A Sticky Situation",
                                "category": STORY,
                                "identifier": "",
                                "flag": "main3_done",
                            },
                            {
                                "text": "Complete Mainquest 4 - Shadow on the Walls",
                                "category": STORY,
                                "identifier": "",
                                "flag": "main4_done",
                            },
                        ),
                        "levels": ( #levelrequirements that show and check required character Progress
                            {
                                "char": "zero",
                                "level": 7,
                            },                               
                            {
                                "char": "nova",
                                "clevel": 3,
                                "level": 7,
                            },                            
                            {
                                "char": "yuki",
                                "clevel": 3,
                                "level": 7,
                            },                            
                            {
                                "char": "alita",
                                "clevel": 3,
                            },
                        ),
                    },
                    "reward": Reward(
                        money=400,
                        items = (("starwand", 1), ("royalsword", 1), ("yukibow+", 1) ),
                        flags=(
                            {"category": STORY, "identifier": "", "flag": "super1_done"},
                        ),
                    ),
                },
            ],
        },
        "info1": {
            "title": "Info",
            "name": "Hope you enjoyed it!~",
            "type": MAINQUEST,
            "bg": False,
            "bgslide": False,
            "icon": False,
            "char": None,
            "description": "You reached the end of the current content(unless you haven't finished the current deepest level of the dungeon, but that is optional for now)",
            "stages": [
                {
                    "description": "Not much left to do now but wait for the next update!\nIf you want to talk about the game, give me feedback or just want to say hello, why don't you join the official Harmony of the Stars Discord server!\nA link can be found on the main menu.",
                    "tip": "If you want to ensure the future of Harmony of the Stars, then please consider supporting its development on Patreon or Subscribestar! #shameless plug, lol",
                    "requirements": {
                        "flags": (
                            {
                                "text": "This quest is unfinishable and will dissappear once there is more content past this.",
                                "category": STORY,
                                "identifier": "",
                                "flag": "good_luck_getting_this",
                            },

                        ),
                    },
                    "reward": Reward(
                        money=100000000,
                        flags=(
                            {"category": STORY, "identifier": "", "flag": "how_did_you_get_this???"},
                        ),
                    ),
                },
            ],
        },
    }

label reached_current_end:
    if flags.story.has("", "info_quest_active"):
        return
    if flags.story.has("", "super1_done"):
        $ quests.start("info1")
        $ flags.story.set("", "info_quest_active")
    return

####################################### FULL ENTRY FOR OVERVIEW/COPY-PASTING! ####################################################
#        "main2": {
#            "title": "Main Quest 2",
#            "name": "Prepare for your first adventure!",
#            "type": MAINQUEST,
#            "bg": False,
#            "bgslide": True,
#            "icon": False,
#            "char": None,
#            "description": "You are about to embark on your first adventure together! Though you should probably prepare for it first.",
#            "stages": [
#                {
#                    "description": "Talk to Nova",
#                    "tip": "You can find her in her room.",
#                    "requirements": {
#                        "money": 100,
#                        "items": (("royalsword", 2), ("ironsword", 2)),
#                        "text": "Optional requirements text, if wanted.",
#                        "flags": (
#                            {
#                                "type": CHAR,
#                                "char": "nova",
#                                "flag": "exampleflag1"
#                            },
#                            {
#                                "type": LOC,
#                                "super": "home",
#                                "loc": "shrine",
#                                "flag": "exampleflag2"
#                            },
#                        ),
#                    },
#                    "reward": { #Note: each of these fields should be allowed to be empty
#                        "money": 100,
#                        "items": (("royalsword", 2), ("ironsword", 1)),
#                        "text": "Optional reward text, if wanted.",
#                        "flags": (
#                            {
#                                "type": "char",
#                                "char": "nova",
#                                "flag": "exampleflag1"
#                            },
#                            {
#                                "type": "loc",
#                                "super": "home",
#                                "loc": "shrine",
#                                "flag": "exampleflag2"
#                            },
#                        ),
#                        "target": "where to tell renpy to jump upon completion",
#                    },
#                },
#            ],
#        },