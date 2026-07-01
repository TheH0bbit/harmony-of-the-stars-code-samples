"""
Navigation System
=================

Controls movement between explorable locations.

Responsibilities
----------------

• Current location management
• Location transitions
• Navigation flow
• Triggering location events
• Quest update integration
• Scene loading

Architecture
------------

The navigation system acts as the central entry point whenever the
player moves to a new location.

After updating the current navigation state, it coordinates
location-specific events, quest updates, dialogue triggers and
screen transitions before handing control back to the player.

Collaborates with
-----------------

• World Map
• Quests
• Character Locations
• Location Events
• UI
"""

default navLocation = "giraffeexhibit"
default superLocation = "thefckingzoo"
default prevNavLocation = "thesavannahorhoweveryouwritethat"
default new_location = f"{superLocation}_{navLocation}" 
default last_location = f"{superLocation}_{navLocation}" #Only last location compared to new_location while hasn't been updated, can be used inbetween their two respective update events


init python:
    def set_current_location(superloc, loc = None):
        global superLocation, navLocation
        if not loc:
            superloc, loc = superloc.split("_", 1)
        superLocation = superloc
        navLocation = loc

label current_location:
    $ popupItemCounter = 0
    $ result = None
    $ new_location = f"{superLocation}_{navLocation}"
    $ result = check_location()
    $ last_location = f"{superLocation}_{navLocation}"
    $ quests.check_updates()
    call reached_current_end from _call_reached_current_end

    if result:
        jump expression result
    call show_vnmenus from _call_show_vnmenus_2
    show screen navi(f"s_{superLocation}_{navLocation}")
    scene expression f"gui/navigation/{superLocation}/bgs/{navLocation} ({tod}).webp" with dissolve
    ""

label current_location_bgonly:
    $ play_sounds_location()
    scene expression f"gui/navigation/{superLocation}/bgs/{navLocation} ({tod}).webp" with dissolve
    return

label char_jump:
    hide screen s_quicknav
    jump expression get_char_location(selectedChar)

transform nav_loc():
    alpha 0
    on idle:
        ease 0.1 alpha 0
    on hover:
        ease 0.1 alpha 0.65
    on replaced:
        ease 0.1 alpha 0


transform nav_alpha(a=0.55):
    alpha 0
    ease 0.1 alpha a
    on idle:
        ease 0.1 alpha a
    on hover:
        ease 0.1 alpha 1
    on replaced:
        ease 0.1 alpha 0

transform loc_popup:
    align (0.5, 0.1)
    alpha 0
    parallel:
        easein 0.8 alpha 1 zoom 1.1
    parallel:
        easein 2 yoffset 0
    parallel:
        pause 1.5
        easein 1 alpha 0 zoom 1
    on replaced:
        easein 0.1 alpha 0


screen navi(navLocation = "s_home_hub"):
    modal True
    tag nav

    on "show" action [  Function(renpy.choice_for_skipping),
                        #SetVariable("talkingstring",None),
                        #SetVariable("talkingGirl",None),
                        #SetVariable("_skipping",False),
                        #Function(Girls.softUpdateAll), #TODO
                        #Function(player.updateEvents)
                        ]
    on "hide" action [SetVariable("_skipping",True)]

    use expression navLocation #pass (hints)



#label update_location:
#    $ location_img = currLocation.lower()
#    if renpy.has_image(location_img, exact = True):
#        scene expression location_img
#    return

