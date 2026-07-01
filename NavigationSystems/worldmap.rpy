"""
World Map System
================

Implements the interactive world map used for navigation and exploration.

Responsibilities
----------------

• World map state
• Camera movement and zoom
• Dragging and panning
• Map mode switching
• Region and town selection
• Navigation state
• World map UI interaction

Architecture
------------

The world map maintains its own runtime state independent of the
navigation system. It is responsible for presenting the game world,
while actual location transitions are handled by the navigation
framework.

The map supports multiple presentation modes (RPG, lore, regional,
etc.) while sharing a common camera and interaction model.

Collaborates with
-----------------

• Navigation
• Location Information
• Character Locations
• Quests
• UI
"""

init python:

    #TODO: Way too many Global variables, Refactor to Class in near future!

    # Map state - General
    currentMapMode = RPG

    worldmapZoomGoal = 1.0
    worldmapZoom = 1.0
    worldmapZoomIcons = 1.0
    worldmapZoomMin = 0.25
    worldmapZoomMax = 2

    zoomAnchorMapX = 0.0
    zoomAnchorMapY = 0.0
    zoomAnchorScreenX = 0
    zoomAnchorScreenY = 0

    #These coordinates are where the top left of the map is placed on the screen!
    #In Screenspace!
    worldmapX = 0
    worldmapY = 0

    #In Worldspace!
    worldmapXGoal = 0
    worldmapYGoal = 0

    mapDragging = False
    mapGliding = False
    initialZoomDifferential = 0.0
    initialCoordinatesX = 0
    initialCoordinatesY = 0 
    dragStartMouse = (0, 0)
    dragStartMap = (0, 0)

    WORLDMAP_X = 7680
    WORLDMAP_Y = 4320

    #WORLDMAP_X = 15360
    #WORLDMAP_Y = 8640
    #when switching, change lerp formula for dynamic zoom

    # Map state - Lore
    worldmapCountries = False
    worldmapPaths = False
    worldmapRegions = False
    worldmapTowns = True

    wmInfoShowing = True
    wmStateBackup = None


    # Map state - RPG
    currentTown = "solsticeridge"
    currentArea = "easternveraxia"
    selectedDungeon = None
    selectedSubarea = None
    hoveredSubarea = None

    worldmapCenter = None
    wiggleLeft = 0
    wiggleRight = 0
    wiggleUp = 0
    wiggleDown = 0

    clouds_positions = {}
    clouds_anchors = {}
    clouds_velocity = {}
    clouds_velocity_target = {}
    clouds_timers = {}
    override_timer = 0


# OLD Implementation
#    def worldmap_update_alpha():
#        global wmPathsAlpha, wmCountriesAlpha, wmRegionsAlpha, wmTownsAlpha
#        if worldmapPaths:
#            if wmPathsAlpha != 1.0:
#                wmPathsAlpha = time_lerp(wmPathsAlpha, 1.0, 5)
#                if abs(wmPathsAlpha - 1.0) <= 0.01:
#                    wmPathsAlpha = 1.0
#        else:
#            if wmPathsAlpha != 0.0:
#                wmPathsAlpha = time_lerp(wmPathsAlpha, 0.0, 5)
#                if wmPathsAlpha <= 0.01:
#                    wmPathsAlpha = 0.0
#
#        if worldmapCountries:
#            if wmCountriesAlpha != 1.0:
#                wmCountriesAlpha = time_lerp(wmCountriesAlpha, 1.0, 5)
#                if abs(wmCountriesAlpha - 1.0) <= 0.01:
#                    wmCountriesAlpha = 1.0
#        else:
#            if wmCountriesAlpha != 0.0:
#                wmCountriesAlpha = time_lerp(wmCountriesAlpha, 0.0, 5)
#                if wmCountriesAlpha <= 0.01:
#                    wmCountriesAlpha = 0.0
##
#        if worldmapRegions:
#            if wmRegionsAlpha != 1.0:
#                wmRegionsAlpha = time_lerp(wmRegionsAlpha, 1.0, 5)
#                if abs(wmRegionsAlpha - 1.0) <= 0.01:
#                    wmRegionsAlpha = 1.0
#        else:
#            if wmRegionsAlpha != 0.0:
#                wmRegionsAlpha = time_lerp(wmRegionsAlpha, 0.0, 5)
#                if wmRegionsAlpha <= 0.01:
#                    wmRegionsAlpha = 0.0
#
#        if worldmapTowns:
#            if wmTownsAlpha != 1.0:
#                wmTownsAlpha = time_lerp(wmTownsAlpha, 1.0, 5)
#                if abs(wmTownsAlpha - 1.0) <= 0.01:
#                    wmTownsAlpha = 1.0
#        else:
#            if wmTownsAlpha != 0.0:
#                wmTownsAlpha = time_lerp(wmTownsAlpha, 0.0, 5)
#                if wmTownsAlpha <= 0.01:
#                    wmTownsAlpha = 0.0


    def clamp(v, minv, maxv):
        return max(minv, min(v, maxv))

    def clamp_map():
        global worldmapX, worldmapY

        scaledW = (WORLDMAP_X/SCREEN_W) * worldmapZoom 
        scaledH = (WORLDMAP_Y/SCREEN_H) * worldmapZoom

        min_x = 1 - scaledW
        min_y = 1 - scaledH

        if currentMapMode == RPG and not mapGliding:         
            worldspaceX, worldspaceY = screen_to_map(0.5, 0.5)
            
            worldspaceX = clamp(worldspaceX, (worldmapCenter[0]-wiggleLeft)/SCREEN_W, (worldmapCenter[0]+wiggleRight)/SCREEN_W)
            worldspaceY = clamp(worldspaceY, (worldmapCenter[1]-wiggleUp)/SCREEN_H, (worldmapCenter[1]+wiggleDown)/SCREEN_H)

            worldmapX = 0.5 - worldspaceX * worldmapZoom
            worldmapY = 0.5 - worldspaceY * worldmapZoom

        worldmapX = clamp(worldmapX, min_x, 0)
        worldmapY = clamp(worldmapY, min_y, 0)


    def worldmap_set_zoom(delta):
        global worldmapZoomGoal
        global zoomAnchorMapX, zoomAnchorMapY
        global zoomAnchorScreenX, zoomAnchorScreenY

        worldmapZoomGoal = clamp(
            worldmapZoomGoal + delta,
            worldmapZoomMin,
            worldmapZoomMax
        )

        mx, my = renpy.get_mouse_pos()

        # Screen-space anchor
        zoomAnchorScreenX = mx/SCREEN_W
        zoomAnchorScreenY = my/SCREEN_H

        # Convert mouse to map space ONCE
        zoomAnchorMapX = (mx/SCREEN_W - worldmapX) / worldmapZoom
        zoomAnchorMapY = (my/SCREEN_H - worldmapY) / worldmapZoom


    def start_drag():
        global mapDragging, dragStartMouse, dragStartMap, worldmapZoomGoal
        mapDragging = True
        #Stop zooming
        worldmapZoomGoal = worldmapZoom
        worldmap_update_zoom()

        dragStartMouse = renpy.get_mouse_pos()
        dragStartMap = (worldmapX, worldmapY)

    def stop_drag():
        global mapDragging
        mapDragging = False

    def worldmap_update_movement():
        global worldmapX, worldmapY, mapGliding, mapDragging, zoomAnchorScreenX, zoomAnchorScreenY, zoomAnchorMapX, zoomAnchorMapY

        if mapGliding:
            mapDragging = False
            #screen to world space
            currWorldspaceX = (0.5 - worldmapX) / worldmapZoom
            currWorldspaceY = (0.5 - worldmapY) / worldmapZoom

            #interpolate correct worldspace coordinates
            if initialZoomDifferential == 0:
                currWorldspaceGoalX = time_lerp(currWorldspaceX, worldmapXGoal, 5.0)#(abs(initialZoomDifferential)+1)*0.4)
                currWorldspaceGoalY = time_lerp(currWorldspaceY, worldmapYGoal, 5.0)#(abs(initialZoomDifferential)+1)*0.4)
            else:
                currentZoomDifferential = worldmapZoom - worldmapZoomGoal 
                factor = 1.0 - currentZoomDifferential / initialZoomDifferential
                currWorldspaceGoalX = initialCoordinatesX + (worldmapXGoal - initialCoordinatesX) * factor
                currWorldspaceGoalY = initialCoordinatesY + (worldmapYGoal - initialCoordinatesY) * factor

            #ensure complete lerping to target
            #renpy.log(f"Worldspace after interpolation: {currWorldspaceGoalX}, {currWorldspaceGoalY}")

    #        if currWorldspaceGoalX > worldmapXGoal:
    #            currWorldspaceGoalX = math.floor(currWorldspaceGoalX)
    #        else:
    #            currWorldspaceGoalX = math.ceil(currWorldspaceGoalX)
#
    #        if currWorldspaceGoalY > worldmapYGoal:
    #            currWorldspaceGoalY = math.floor(currWorldspaceGoalY)
    #        else:
    #            currWorldspaceGoalY = math.ceil(currWorldspaceGoalY)

            #renpy.log(f"Worldspace after rounding: {currWorldspaceGoalX}, {currWorldspaceGoalY}")
            #renpy.log(f"Difference to worldmapXGoal: {currWorldspaceGoalX - worldmapXGoal}, {currWorldspaceGoalY - worldmapYGoal}")

            #back to screen space
            if abs(currWorldspaceGoalX - worldmapXGoal) <= 0.5/SCREEN_W and abs(currWorldspaceGoalY - worldmapYGoal) <= 0.5/SCREEN_H:
                worldmapX = -worldmapXGoal*worldmapZoomGoal+0.5
                worldmapY = -worldmapYGoal*worldmapZoomGoal+0.5

                mapGliding = False
            else:
                worldmapX = -currWorldspaceGoalX*worldmapZoom+0.5
                worldmapY = -currWorldspaceGoalY*worldmapZoom+0.5

            
            #currWorldspaceY = int((SCREEN_H // 2 - worldmapY) / worldmapZoom)
            clamp_map()
            zoomAnchorScreenX = 0.5
            zoomAnchorScreenY = 0.5

            zoomAnchorMapX = worldmapXGoal
            zoomAnchorMapY = worldmapYGoal
            return

        #renpy.log(f"Screenspace: {worldmapX}, {worldmapY}")

        if not mapDragging:
            return

        mx, my = renpy.get_mouse_pos()
        dx = mx - dragStartMouse[0]
        dy = my - dragStartMouse[1]

        worldmapX = dragStartMap[0] + dx/SCREEN_W
        worldmapY = dragStartMap[1] + dy/SCREEN_H

        clamp_map()

    def worldmap_update_zoom():
        global worldmapZoom, worldmapZoomIcons, worldmapX, worldmapY
        update_dt()

        if worldmapZoom == worldmapZoomGoal:
            return

        t = clamp((worldmapZoom - 1.0) / (worldmapZoomMax - 1.0), 0.0, 1.0)
        lerp_factor = lerp(4.0, 6.0, t)

        worldmapZoom = time_lerp(worldmapZoom, worldmapZoomGoal, lerp_factor)

        if worldmapZoom <= 1:
            if abs(worldmapZoom - worldmapZoomGoal) <= 0.001: 
                worldmapZoom = worldmapZoomGoal 
        else: 
            if abs(worldmapZoom - worldmapZoomGoal) <= 0.01:
                worldmapZoom = worldmapZoomGoal

        #t = clamp((worldmapZoomIcons - 1.0) / (worldmapZoomMax - 1.0), 0.0, 1.0)
        #lerp_factor = lerp(0.1, 0.2, t)*10

        worldmapZoomIcons = remap_values(worldmapZoom, 2.0, 0.8, 1.0, 0.25)
        #worldmapZoomIcons = worldmapZoomIconsGoal lerp(worldmapZoomIcons, worldmapZoomIconsGoal, lerp_factor)

        #if worldmapZoomIcons <= 1:
        #    if abs(worldmapZoomIcons - worldmapZoomIconsGoal) <= 0.002: 
        #        worldmapZoomIcons = worldmapZoomIconsGoal 
        #else: 
        #    if abs(worldmapZoomIcons - worldmapZoomIconsGoal) <= 0.02:
        #        worldmapZoomIcons = worldmapZoomIconsGoal
#
        # Reposition map so anchor stays fixed under mouse
        if not mapGliding:
            worldmapX = zoomAnchorScreenX - zoomAnchorMapX * worldmapZoom
            worldmapY = zoomAnchorScreenY - zoomAnchorMapY * worldmapZoom

        clamp_map()


    def reset_map():
        global worldmapZoom, worldmapX, worldmapY
        worldmapZoom = 1.0
        worldmapZoomIcons = 1.0
        worldmapX = 0
        worldmapY = 0
        clamp_map()

    #x/y from top left corner
    def prepare_worldmap(zoom = 1.5, x = 4734, y = 2784):
        global worldmapZoom, worldmapZoomIcons, worldmapZoomGoal, worldmapX, worldmapY, zoomAnchorScreenX, zoomAnchorScreenY, zoomAnchorMapX, zoomAnchorMapY

        worldmapZoomGoal = zoom
        worldmapZoom = zoom
        worldmapZoomIcons = remap_values(worldmapZoom, 2.0, 0.8, 1.0, 0.25)
        #sets worldmapX/Y with desired zoomlevel
        center_on_map(x, y)

        if currentMapMode == LORE:
            prepare_worldmap_lore()
        elif currentMapMode == RPG:
            prepare_worldmap_rpg()

        clamp_map()

        zoomAnchorScreenX = 0.5
        zoomAnchorScreenY = 0.5

        zoomAnchorMapX = (zoomAnchorScreenX - worldmapX) // worldmapZoom
        zoomAnchorMapY = (zoomAnchorScreenY - worldmapY) // worldmapZoom

    def screen_to_map(screenX, screenY):
        mapX = (screenX - worldmapX) / worldmapZoom
        mapY = (screenY - worldmapY) / worldmapZoom
        return mapX, mapY

    def map_to_screen(mapX, mapY):
        screenX = worldmapX + mapX/SCREEN_W * worldmapZoom
        screenY = worldmapY + mapY/SCREEN_H * worldmapZoom
        return screenX, screenY

    def center_on_map(mapX, mapY, screenX=0.5, screenY=0.5):
        global worldmapX, worldmapY

        worldmapX = screenX - (mapX / SCREEN_W * worldmapZoom)
        worldmapY = screenY - (mapY / SCREEN_H * worldmapZoom)

    def map_to_screen_int(mapX, mapY):
        screenX = int((worldmapX*SCREEN_W + mapX * worldmapZoom))
        screenY = int((worldmapY*SCREEN_H + mapY * worldmapZoom))
        return screenX, screenY


    def glideto_worldmap(zoom, x, y, xoffset = 0, yoffset = 0):
        global worldmapZoomGoal, worldmapXGoal, worldmapYGoal, mapGliding, initialZoomDifferential, initialCoordinatesX, initialCoordinatesY
        worldmapZoomGoal = zoom
        worldmapXGoal = (x-xoffset/worldmapZoomGoal)/SCREEN_W
        worldmapYGoal = (y-yoffset/worldmapZoomGoal)/SCREEN_H
        mapGliding = True
        initialZoomDifferential = worldmapZoom - worldmapZoomGoal
        initialCoordinatesX, initialCoordinatesY = screen_to_map(0.5, 0.5)

    def save_worldmap_state():
        global wmStateBackup
        x, y  = screen_to_map(0.5, 0.5)#, SCREEN_W // 2, SCREEN_H // 2)
        x = int(x*1920)
        y = int(y*1080)
        return {
            "mapspaceX": x,
            "mapspaceY": y,
            "worldmapZoom": worldmapZoom,
            "worldmapPaths": worldmapPaths,
            "worldmapRegions": worldmapRegions,
            "worldmapCountries": worldmapCountries,
            "worldmapTowns": worldmapTowns,
        }

    def restore_worldmap_state(state):
        global worldmapPaths, worldmapRegions, worldmapCountries, worldmapTowns
        toggle_wm_paths(state["worldmapPaths"])
        toggle_wm_regions(state["worldmapRegions"])
        toggle_wm_countries(state["worldmapCountries"])
        toggle_wm_towns(state["worldmapTowns"])
        glideto_worldmap(state["worldmapZoom"], state["mapspaceX"], state["mapspaceY"])


    #Note: value can be True or False, use as a switch to turn it on.
    def toggle_wm_countries(value = None):
        global worldmapCountries
        if value != None:
            worldmapCountries = not value
        if worldmapCountries:
            renpy.hide_screen("s_worldmap_loreoverlay_countries")
        else:
            renpy.show_screen("s_worldmap_loreoverlay_countries")
        worldmapCountries = not worldmapCountries

    def toggle_wm_paths(value = None):
        global worldmapPaths
        if value != None:
            worldmapPaths = not value
        if worldmapPaths:
            renpy.hide_screen("s_worldmap_loreoverlay_paths")
        else:
            renpy.show_screen("s_worldmap_loreoverlay_paths")
        worldmapPaths = not worldmapPaths

    def toggle_wm_regions(value = None):
        global worldmapRegions
        if value != None:
            worldmapRegions = not value
        if worldmapRegions:
            renpy.hide_screen("s_worldmap_loreoverlay_regions")
        else:
            renpy.show_screen("s_worldmap_loreoverlay_regions")
        worldmapRegions = not worldmapRegions
        
    def toggle_wm_towns(value = None):
        global worldmapTowns
        if value != None:
            worldmapTowns = not value
        if worldmapTowns:
            renpy.hide_screen("s_worldmap_loreoverlay_towns")
        else:
            renpy.show_screen("s_worldmap_loreoverlay_towns")
        worldmapTowns = not worldmapTowns

    def reset_clouds():
        global clouds_positions, clouds_anchors, clouds_velocity, clouds_velocity_target, clouds_timers, override_timer
        clouds_positions = {}
        clouds_anchors = {}
        clouds_velocity = {}
        clouds_velocity_target = {}
        clouds_timers = {}
        override_timer = 0

    def worldmap_update_clouds():
        global clouds_positions, clouds_velocity, clouds_velocity_target, clouds_timers, override_timer

        #dt is global, and updated here in wm move function every frame
        if currentMapMode == LORE:
            return

        if override_timer > 0:
            override_timer -= dt
            return

        MAX_RADIUS = 50
        MAX_VELOCITY = 5

        for cloud_id, (x, y) in clouds_positions.items():

            ax, ay = clouds_anchors[cloud_id]
            vx, vy = clouds_velocity.get(cloud_id, (0, 0))
            vtx, vty = clouds_velocity_target.get(cloud_id, (0, 0))
            clouds_timers[cloud_id] -= dt

            if clouds_timers[cloud_id] <= 0:
                clouds_timers[cloud_id] = random.uniform(2, 6)
                vtx = random.uniform(-MAX_VELOCITY, MAX_VELOCITY)
                vty = random.uniform(-MAX_VELOCITY, MAX_VELOCITY)
                clouds_velocity_target[cloud_id] = (vtx, vty)
            
            vx = time_lerp(vx, vtx, 0.5)
            vy = time_lerp(vy, vty, 0.5)

            # move
            new_x = x + vx * dt
            new_y = y + vy * dt

            # soft boundary pull (keeps near anchor)
            dx = new_x - ax
            dy = new_y - ay
            dist = math.hypot(dx, dy)

            if dist > MAX_RADIUS:
                pull = (dist - MAX_RADIUS) * 0.05
                new_x -= dx / dist * pull
                new_y -= dy / dist * pull

            clouds_positions[cloud_id] = (new_x, new_y)
            clouds_velocity[cloud_id] = (vx, vy)


        #Alternate Cloud Movement

        #MAX_RADIUS = 50
        #ACCEL = 1.0        # how much direction changes
        #DAMPING = 0.98     # slows velocity (momentum feel)
        #MAX_SPEED = 10
        #
        #for cloud_id, (x, y) in clouds_positions.items():
                #
        #    ax, ay = clouds_anchors[cloud_id]
        #    vx, vy = clouds_velocity.get(cloud_id, (0, 0))
        #
        #    # small random acceleration (smooth randomness)
        #    noise_x = random.uniform(-1, 1)
        #    noise_y = random.uniform(-1, 1)
        #
        #    vx += noise_x * ACCEL
        #    vy += noise_y * ACCEL
        #
        #    # limit speed
        #    speed = math.hypot(vx, vy)
        #    if speed > MAX_SPEED:
        #        vx *= MAX_SPEED / speed
        #        vy *= MAX_SPEED / speed
        #
        #    # damping (creates momentum feel)
        #    vx *= DAMPING
        #    vy *= DAMPING
        #
        #    # move
        #    new_x = x + vx * dt
        #    new_y = y + vy * dt
        #
        #    # soft boundary pull (keeps near anchor)
        #    dx = new_x - ax
        #    dy = new_y - ay
        #    dist = math.hypot(dx, dy)
        #
        #    if dist > MAX_RADIUS:
        #        pull = (dist - MAX_RADIUS) * 0.05
        #        new_x -= dx / dist * pull
        #        new_y -= dy / dist * pull
        #
        #    clouds_positions[cloud_id] = (new_x, new_y)
        #    clouds_velocity[cloud_id] = (vx, vy)



################################################## RPG MODE FUNCTIONS ##########################################################

    def switch_worldmap_mode():
        if currentMapMode == LORE:
            prepare_worldmap_rpg()

        elif currentMapMode == RPG:
            prepare_worldmap_lore()

    def prepare_worldmap_lore():
        global currentMapMode, worldmapZoomMin, worldmapZoomGoal
        currentMapMode = LORE
        worldmapZoomMin = 0.25
        if wmStateBackup:
            restore_worldmap_state(wmStateBackup)
        worldmapZoomGoal = 0.25
        renpy.hide_screen("s_worldmap_rpgoverlay")
        renpy.hide_screen("s_dungeon_info")


    def prepare_worldmap_rpg():
        global currentMapMode, wmStateBackup, worldmapCenter, wiggleLeft, wiggleRight, wiggleUp, wiggleDown, worldmapZoomMin, clouds_positions, clouds_anchors, clouds_velocity, clouds_velocity_target, clouds_timers
        currentMapMode = RPG
        areaInfo = LOCATIONS_WORLDMAP_RPG.get(currentArea)
        wmStateBackup = save_worldmap_state()
        toggle_wm_regions(False)
        toggle_wm_paths(False)
        toggle_wm_countries(False)
        toggle_wm_towns(False)
        glideto_worldmap(1, areaInfo.get("targetx"), areaInfo.get("targety")) 
        worldmapCenter = (areaInfo.get("targetx"), areaInfo.get("targety"))
        wiggleLeft = areaInfo.get("wiggleleft")
        wiggleRight = areaInfo.get("wiggleright")
        wiggleUp = areaInfo.get("wiggleup")
        wiggleDown = areaInfo.get("wiggledown")
        worldmapZoomMin = 0.9
        reset_clouds()
        for cloud_id, cloud in LOCATIONS_WORLDMAP_RPG.get(currentArea).get("clouds").items():
            clouds_anchors[cloud_id] = [cloud["x"], cloud["y"]]
            spawnX = cloud["x"]+(cloud["x"]-worldmapCenter[0])/4
            spawnY = cloud["y"]+(cloud["y"]-worldmapCenter[1])/4
            clouds_positions[cloud_id] = [spawnX, spawnY]
            clouds_velocity[cloud_id] = (0,0)
            clouds_velocity_target[cloud_id] = (0,0)
            clouds_timers[cloud_id] = 0

        renpy.show_screen("s_worldmap_rpgoverlay")
        renpy.hide_screen("s_wm_info")


#Careful about callstack when implementing this!
label wm_jump_town(target):
    jump toggle_worldmap

label return_worldmap:
    if renpy.get_screen("s_dungeon_info"):
        jump close_dungeon_info
    if renpy.get_screen("s_wm_info"):
        jump close_wm_info
    jump toggle_worldmap

screen s_worldmap():
    zorder 0
    modal True

    timer 0.03 action [Function(worldmap_update_zoom), Function(worldmap_update_movement), Function(worldmap_update_clouds)] repeat True
    #timer 0.025 action [Function(worldmap_update_clouds)] repeat True

    fixed at popin_bounce, fadein:
        align (0.5, 0.5)
        # Background dim
        add Solid("#0008")

        # ===== VIEWPORT =====
        fixed:
            xpos 0
            ypos 0
            xsize SCREEN_W
            ysize SCREEN_H
            clipping True

        # ===== INPUT HANDLING =====
        key "mousedown_1" action Function(start_drag)
        key "mouseup_1" action Function(stop_drag)
        key "mousedown_4" action Function(worldmap_set_zoom, 0.2)
        key "mousedown_5" action Function(worldmap_set_zoom, -0.2)

        # Map container Main
        add "gui/maps/worldmap/worldmap_base.png" at colortransform(tint=todTintDict[tod], alphav = 1):
            subpixel True
            xpos worldmapX
            ypos worldmapY
            zoom worldmapZoom


transform screen_dissolve:
    on show:
        alpha 0.0
        easein 0.4 alpha 1.0
    on hide:
        easeout 0.4 alpha 0.0


screen s_worldmap_ui():
    zorder 10
    fixed at popin_bounce, fadein:
        align (0.5, 0.5)

        # ===== UI =====            
        hbox:
            align(0.99, 0.99)
            spacing 0

            imagebutton:
                idle "gui/icons/return_icon.png"
                action [Jump("return_worldmap")] at dyn_hover_effect

        if currentMapMode == LORE and not wmInfoShowing:
            fixed:
                xysize (250, 325)
                align(0.007, 0.99)
                vbox:
                    align (0.0, 1.0)
                    fixed:
                        xysize (250, 75)
                        button at dyn_hover_effect:
                            xysize (250, 75)
                            align (0.5, 0.5)
                            selected worldmapCountries
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(toggle_wm_countries)
                        text "Countries & Borders" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5
                    fixed:
                        xysize (250, 75)
                        button at dyn_hover_effect:
                            xysize (250, 75)
                            align (0.5, 0.5)
                            selected worldmapRegions
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(toggle_wm_regions)
                        text "Major Regions" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5
                    fixed:
                        xysize (250, 75)
                        button at dyn_hover_effect:
                            xysize (250, 75)
                            align (0.5, 0.5)
                            selected worldmapPaths
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(toggle_wm_paths)
                        text "Towns & Travel Routes" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5
                    fixed:
                        xysize (250, 75)
                        button at dyn_hover_effect:
                            xysize (250, 75)
                            align (0.5, 0.5)
                            selected worldmapTowns
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(toggle_wm_towns)
                        text "Town Icons" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5

            if not wmInfoShowing:
                hbox:
                    align (0.01, 0.01)
                    imagebutton:
                        xysize (140, 120)
                        yalign 0.5
                        idle "gui/icons/lore_icon.png"
                        hovered [Function(set_tooltip_data, "Swap Mode", 0.01, 0.04, True, "textmaplabel")]
                        unhovered [Function(clear_tooltip_data)]
                        action [Function(switch_worldmap_mode)] at dyn_hover_effect

                    text f"Lore":
                        font "fonts/map/IM FELL English Bold.ttf"
                        yalign 0.5
                        size 75
                        color "#ffce64"
                        outlines [ ( 3, "#2b2b2b", 2, 2) ]


        text "Elysterra" style "header" at loc_popup


    

screen s_worldmap_loreoverlay_countries():
    zorder 1
    fixed at screen_dissolve:
        align (0.5, 0.5)
        # Map container        
        add "gui/maps/worldmap/worldmap_countries_s.png":
            subpixel True
            xpos worldmapX
            ypos worldmapY
            zoom worldmapZoom * 2

screen s_worldmap_loreoverlay_paths():
    zorder 2
    fixed at screen_dissolve:
        align (0.5, 0.5)
        # Map container        
        add "gui/maps/worldmap/worldmap_paths_s.png":
            subpixel True
            xpos worldmapX
            ypos worldmapY
            zoom worldmapZoom * 2

screen s_worldmap_loreoverlay_regions():
    zorder 3
    fixed at screen_dissolve:
        align (0.5, 0.5)
        # Map container        
        add "gui/maps/worldmap/worldmap_labels_regions_s.png":
            subpixel True
            xpos worldmapX
            ypos worldmapY
            zoom worldmapZoom * 2

screen s_worldmap_loreoverlay_towns():
    zorder 4
    fixed at screen_dissolve:
        #TOWN ICONS
        align (0.5, 0.5)

        for loc_id, loc in LOCATIONS_WORLDMAP.items():
            $ sx, sy = map_to_screen_int(loc["x"], loc["y"])
            if -100 < sx < SCREEN_W+100 and -100 < sy < SCREEN_H+100:
                if worldmapZoom >= 0.8:
                    if loc["landmarks"][0] != "": #loc_id in wmTravelUnlock:
                        if loc["type"] == TOWN:
                            imagebutton at dyn_hover_effect, dyn_zoom(worldmapZoomIcons):
                                idle f"gui/icons/sigils/256/{loc['icon']}"
                                xpos sx
                                ypos sy
                                anchor (0.5, 0.5)
                                action [SetVariable("selectedLocation", loc_id), Jump("reopen_wm_info")]
                                #action Call("wm_jump_town", loc["target"])
                    else:
                        imagebutton at dyn_zoom(worldmapZoomIcons), colortransform(saturation = 0):
                            idle f"gui/icons/sigils/256/{loc['icon']}"
                            xpos sx
                            ypos sy
                            anchor (0.5, 0.5)
                            action [SetVariable("tempstring", "This towns info is still missing. Check again in future updates!"), Jump("mc_say")]

                else:
                    if loc["landmarks"][0] != "": #loc_id in wmTravelUnlock:
                        if loc["type"] == TOWN:
                            imagebutton at dyn_hover_effect:
                                idle f"gui/icons/sigils/64/{loc['icon']}"
                                xpos sx
                                ypos sy
                                anchor (0.5, 0.5)
                                action [SetVariable("selectedLocation", loc_id), Jump("reopen_wm_info")]
                                #action Call("wm_jump_town", loc["target"])
                    else:
                        imagebutton at colortransform(saturation = 0):##at dyn_zoom(worldmapZoomIcons):#, dyn_hover_effect(saturation=0, brightness=-0.2):
                            idle f"gui/icons/sigils/64/{loc['icon']}"
                            xpos sx
                            ypos sy
                            anchor (0.5, 0.5)
                            action [SetVariable("tempstring", "This towns info is still missing. Check again in future updates!"), Jump("mc_say")]


screen s_worldmap_rpgoverlay():
    zorder 1
    fixed at screen_dissolve: 
        align(0.5, 0.5)

        #Dungeons
        for dungeon_id, dungeon in LOCATIONS_WORLDMAP_RPG.get(currentArea).get("dungeons").items():
            if not flags.has_flag(MAP, "rpg", dungeon_id):
                #lockd symbol?
                continue

            $ sx, sy = map_to_screen_int(dungeon["x"], dungeon["y"])
            imagebutton at dyn_hover_effect, dyn_zoom(worldmapZoom*0.4):
                idle f"gui/icons/sigils/256/{dungeon['icon']}"
                xpos sx
                ypos sy
                anchor (0.5, 0.5)
                action [SetVariable("selectedDungeon", dungeon_id), Jump("reopen_dungeon_info")]
                #action Call("wm_jump_town", dungeon["target"])

            text dungeon["name"] at dyn_zoom(worldmapZoom*0.5):
                font "fonts/map/IM FELL English Bold.ttf"
                color "#ffce64"
                outlines [ ( 3, "#2b2b2b", 2, 2) ]
                anchor (0.5, 0.5)
                xpos sx
                ypos sy# + int(40 * worldmapZoom*0.5)
                size 40


        #Locations
        for loc_id, loc in LOCATIONS_WORLDMAP.items():
            if not flags.has_flag(MAP, "rpg", loc_id):
                continue
            $ sx, sy = map_to_screen_int(loc["x"], loc["y"])
            if -100 < sx < SCREEN_W+100 and -100 < sy < SCREEN_H+100:
                if loc["type"] == TOWN:
                    imagebutton at dyn_hover_effect, dyn_zoom(worldmapZoom*0.5):
                        idle f"gui/icons/sigils/256/{loc['icon']}"
                        xpos sx
                        ypos sy
                        anchor (0.5, 0.5)
                        action [SetVariable("selectedLocation", loc_id), Jump("return_worldmap")]
                        #action Call("wm_jump_town", loc["target"])
                    
                    text loc["name"] at dyn_zoom(worldmapZoom*0.5):
                        font "fonts/map/IM FELL English Bold.ttf"
                        color "#ffce64"
                        outlines [ ( 3, "#2b2b2b", 2, 2) ]
                        anchor (0.5, 0.5)
                        xpos sx
                        ypos sy# + int(60 * worldmapZoom*0.5)
                        size 50

        for cloud_id, cloud in LOCATIONS_WORLDMAP_RPG.get(currentArea).get("clouds").items():
            $ sx, sy = map_to_screen(clouds_positions[cloud_id][0], clouds_positions[cloud_id][1])
            add f"gui/maps/clouds/{cloud.get('icon')}.png" at dyn_zoom(worldmapZoom*cloud.get('zoomfactor', 1)), fadein(time = 1.5), colortransform(tint=todTintDict_weaker[tod], alphav = 1):
                subpixel True
                pos (sx, sy)
                anchor (0.5, 0.5)

        $ sx, sy = map_to_screen(4835, 2138)
        add f"gui/maps/clouds/celestialpeak.png" at dyn_zoom(worldmapZoom), colortransform(tint=todTintDict_weaker[tod], alphav = 1):
            pos (sx, sy)
            anchor (0.5, 0.5)

        if not wmInfoShowing:
            add f"gui/maps/general/scroll_{currentArea}.png" at fadein(), move_simple(0.5, 0.095, 2, 1.5), dyn_zoom_timed(1.0, 0.8, 2, 1.5):
                align (0.5, 0.5)

            hbox:
                align (0.01, 0.01)
                imagebutton:
                    xysize (140, 120)
                    yalign 0.5
                    idle "gui/icons/travel_icon.png"
                    hovered [Function(set_tooltip_data, "Swap Mode", 0.01, 0.04, True, "textmaplabel")]
                    unhovered [Function(clear_tooltip_data)]
                    action [Function(switch_worldmap_mode)] at dyn_hover_effect

                text f"Travel":
                    font "fonts/map/IM FELL English Bold.ttf"
                    xoffset -10
                    yalign 0.5
                    size 75
                    color "#ffce64"
                    outlines [ ( 3, "#2b2b2b", 2, 2) ]

label reopen_dungeon_info: 
    $ glideto_worldmap(2.0, LOCATIONS_WORLDMAP_RPG[currentArea]['dungeons'][selectedDungeon]["x"], LOCATIONS_WORLDMAP_RPG[currentArea]['dungeons'][selectedDungeon]["y"], 640) 
    $ wmInfoShowing = True
    $ wmStateBackup = save_worldmap_state()
    $ worldmapCountries, worldmapRegions, worldmapPaths, worldmapTowns = False, False, False, False
    hide screen s_dungeon_info
    show screen s_dungeon_info
    ""

label close_dungeon_info:
    hide screen s_dungeon_info
    $ clear_tooltip_data()
    $ restore_worldmap_state(wmStateBackup)
    $ wmInfoShowing = False
    ""


screen s_dungeon_info:
    zorder 6
    modal True
    $ dungeoninfo = LOCATIONS_WORLDMAP_RPG[currentArea]['dungeons'][selectedDungeon]

    fixed at popin_bounce, fadein:
        align (0.5, 0.5)
        if dungeoninfo["bg"]:
            add f"gui/maps/general/dungeonbgs/{selectedDungeon}.png":
                yalign 0.5

        add "gui/maps/general/dungeon_info_bg.png":
            align (0.5, 0.5)

        vbox:
            xsize 1280
            ypos 54
            #titlebox
            vbox:
                xysize (1280, 150)
                null height 8
                text f"{dungeoninfo['title']}":
                    font "fonts/PrincessAndTheFrog.ttf"
                    xalign 0.5
                    size 30
                    color "#ffffff"
                    outlines [ ( 2, "#9c7b37", 2, 2) ]
                null height 8
                text f"{dungeoninfo['name']}":
                    font "fonts/PrincessAndTheFrog.ttf"
                    xalign 0.5
                    size 65
                    color "#ffffff"
                    outlines [ ( 4, "#9c7b37", 3, 3) ]

            hbox:
                fixed:
                    xysize (360, 1.0)
                    #quests
                    viewport:
                        mousewheel True
                        ysize 782
                        vbox:
                            for subarea, areainfo in DUNGEON_INFO[selectedDungeon]["subareas"].items():
                                if flags.dungeons.has(selectedDungeon, subarea):
                                    fixed:
                                        ysize 100
                                        button at dyn_hover_effect, dyn_xyzoom(xz = 0.75):
                                            selected selectedSubarea == subarea
                                            xysize (360, 100)
                                            background "gui/quests/quest_bg_slide.png"
                                            selected_foreground "gui/quests/quest_bg_slide_selected.png"
                                            #if quests.get_bgslide(qid):
                                            #    idle f"gui/quests/quest_bg_slide_{qid}.png"
                                            hovered [SetVariable("hoveredSubarea", subarea)]
                                            action SetVariable("selectedSubarea", subarea)

                                        text f"{areainfo['name']}":
                                            size 30
                                            align (0.5, 0.5)
                                            text_align(0.5)
                                            outlines [ ( 2, "#0f0f0f", 0, 0) ]
                                            
                                        text f"Lvl {areainfo.get('level')}":
                                            size 22
                                            align (0.96, 0.9)
                                            italic True
                                            outlines [ ( 2, "#0f0f0f", 0, 0) ]
                                else:
                                    fixed:
                                        ysize 100
                                        button at colortransform(saturation = 0), dyn_xyzoom(xz = 0.75):
                                            selected selectedSubarea == subarea
                                            xysize (360, 100)
                                            background "gui/quests/quest_bg_slide.png"
                                            selected_foreground "gui/quests/quest_bg_slide_selected.png"
                                            #if quests.get_bgslide(qid):
                                            #    idle f"gui/quests/quest_bg_slide_{qid}.png"
                                            hovered [SetVariable("hoveredSubarea", subarea)]
                                            action NullAction()

                                        text f"{areainfo['name']}":
                                            size 30
                                            align (0.5, 0.5)
                                            text_align(0.5)
                                            outlines [ ( 2, "#0f0f0f", 0, 0) ]

                                        text f"Locked":
                                            size 22
                                            align (0.96, 0.1)
                                            italic True
                                            outlines [ ( 2, "#0f0f0f", 0, 0) ]

                                        text f"Lvl {areainfo.get('level')}":
                                            size 22
                                            align (0.96, 0.9)
                                            italic True
                                            outlines [ ( 2, "#0f0f0f", 0, 0) ]

                null width 60

                fixed:
                    xsize 1.0

                    vbox:
                        xsize 0.95
                        align (0.5, 0.3)
                        if selectedSubarea:
                            $ areaInfo = DUNGEON_INFO[selectedDungeon]["subareas"][selectedSubarea]
                            null height 20

                            textbutton "Go to Dungeon!" style "textmaplabel" at dyn_hover_effect_inverse:
                                text_size 80
                                align (0.5, 0.5)
                                action Function(load_dungeon, areaInfo)

                            null height 70

                            text "NOTE: Dungeons are still under construction! So for now they consist of a series of consecutive battles.\n":
                                size 30

                            text "Also, the combat system is functional, but still being developed — especially in terms of content, visuals, and balance.\n":
                                size 30
                            
                            text "Because of this, some progress (such as Adventurer Level) may be adjusted in future updates.\n":
                                size 30

                            text "Thanks for your understanding… and have fun!" :
                                size 30


 

    fixed:
        pos (1600, 540)
        imagebutton at dyn_hover_effect, dyn_delayed_zoomout_alpha(worldmapZoomIcons*0.4, worldmapZoomIcons*0.4):
            idle f"gui/icons/sigils/{dungeoninfo['icon']}"
            xanchor 0.5
            yanchor 0.5
            action [Jump("close_dungeon_info")]
        text dungeoninfo["name"] style "textmaplabel":
            size 60
            ypos 210
            xanchor 0.5
            outlines [ ( 3, "#131720", 1, 1) ]


label reopen_wm_info: 
    $ glideto_worldmap(2.0, LOCATIONS_WORLDMAP[selectedLocation]["x"], LOCATIONS_WORLDMAP[selectedLocation]["y"], 640) 
    $ wmInfoShowing = True
    $ wmStateBackup = save_worldmap_state()
    $ worldmapCountries, worldmapRegions, worldmapPaths, worldmapTowns = False, False, False, False
    hide screen s_wm_info
    show screen s_wm_info(selectedLocation)
    ""

label close_wm_info:
    hide screen s_wm_info
    $ restore_worldmap_state(wmStateBackup)
    $ wmInfoShowing = False
    ""

define nationTintDict = {
    "Veraxian Empire": "#ffd051",
    "Kingdom of Polarios": "#8529af",
    "Divine Mandate of Staliar": "#a31a1a",
    "Thalassian Concord": "#2791b1",
}


screen s_wm_info(location = "solsticeridge"):
    zorder 6
    modal True

    fixed at popin_bounce, fadein:
        align (0.5, 0.5)

        add "gui/maps/general/worldmap_infoscreen_bg.png" at colortransform(tint=nationTintDict[LOCATIONS_WORLDMAP[location]["partof"]]) #colortransform(tint = "#ffd051")
        add "gui/maps/general/worldmap_infoscreen_bg_ornaments.png"

        fixed:
            pos (0, 49)

            fixed:
                pos (920, 90)
                xysize (360, 280)
                #background Solid("#533e177e")
                vbox:
                    text "Part of:" style "textmaplabel":
                            size 18
                            xsize 360
                            xalign 0.0
                            text_align 0.5
                            outlines [ ( 2, "#131720", 1, 1) ]
                    xysize (360, 250)
                    add "gui/icons/sigils/veraxia_icon.png":
                        xalign 0.5
                    text LOCATIONS_WORLDMAP[location]["partof"] style "textmaplabel":
                            size 25
                            xsize 360
                            xalign 0.5
                            text_align 0.5
                            outlines [ ( 2, "#131720", 1, 1) ]

                

            vbox:
                #xysize (1280, 960)
                xpos 20
                fixed:
                    xysize (1280, 90)
                    text LOCATIONS_WORLDMAP[location]["name"] style "textmaplabel":
                        size 55
                        align (0.5, 0.5)
                        outlines [ ( 3, "#131720", 1, 1) ]
                fixed: 
                    xysize (1280, 30)
                fixed: 
                    xysize (1280, 60)
                    text "Overview" style "textmaplabel":
                        size 40
                        yalign 0.5
                        outlines [ ( 2, "#131720", 1, 1) ]
                fixed: 
                    xysize (1280, 10)

                fixed: 
                    xysize (830, 190)
                    xpos 30
                    #p1
                    text LOCATIONS_WORLDMAP[location]["description"].split("\n\n")[0] style "textmaptext":
                        size 22
                        yalign 0.0
                        xalign 0.0
                        outlines [ ( 2, "#131720", 0, 0) ]
                        color "#ffe797"

                fixed: 
                    xysize (1180, 180)
                    xpos 30
                    #p1
                    text LOCATIONS_WORLDMAP[location]["description"].split("\n\n")[1].strip() style "textmaptext":
                        size 22
                        yalign 0.0
                        xalign 0.0
                        outlines [ ( 2, "#131720", 0, 0) ]
                        color "#ffe797"

                fixed: 
                    xysize (1280, 60)
                    text "Significance" style "textmaplabel":
                        size 40
                        yalign 0.5
                        outlines [ ( 2, "#131720", 1, 1) ]
                fixed: 
                    xysize (1280, 5)
                fixed: 
                    xysize (830, 140)
                    xpos 30
                    #p1
                    vbox:
                        for entry in LOCATIONS_WORLDMAP[location]["significance"]:
                            hbox:
                                text "{image=gui/textimg/bulletpoint1.png} " style "textmaptext":
                                    yoffset 0
                                    size 28
                                    color "#ffe797"
                                    outlines [ (2, "#131720", 0, 0) ]
                                text f"{entry}" style "textmaptext":
                                    size 22
                                    yalign 0.0
                                    xalign 0.0
                                    outlines [ ( 2, "#131720", 0, 0) ]
                                    color "#ffe797"
                    
                fixed: 
                    xysize (1280, 60)
                    text "Major Landmarks" style "textmaplabel":
                        size 40
                        yalign 0.5
                        outlines [ ( 2, "#131720", 1, 1) ]
                fixed: 
                    xysize (1280, 5)
                fixed: 
                    xysize (830, 140)
                    xpos 30
                    #p1
                    vbox:
                        for entry in LOCATIONS_WORLDMAP[location]["landmarks"]:
                            hbox:
                                text "{image=gui/textimg/bulletpoint1.png} " style "textmaptext":
                                    yoffset 0
                                    size 28
                                    color "#ffe797"
                                    outlines [ (2, "#131720", 0, 0) ]
                                text entry style "textmaptext":
                                    size 22
                                    yalign 0.0
                                    xalign 0.0
                                    outlines [ ( 2, "#131720", 0, 0) ]
                                    color "#ffe797"

        

        #imagebutton at dyn_hover_effect:
        #    idle "gui/icons/return_icon.png"
        #    action [Jump("close_wm_info")]
    

    fixed:
        pos (1600, 540)
        imagebutton at dyn_hover_effect, dyn_delayed_zoomout_alpha(worldmapZoomIcons*0.4, worldmapZoomIcons*0.4):#dyn_zoom(worldmapZoomIcons):#, dyn_delayed_zoomout_alpha(worldmapZoomIcons, worldmapZoomIcons*2.0), :
            idle f"gui/icons/sigils/{LOCATIONS_WORLDMAP[location]['icon']}"
            xanchor 0.5
            yanchor 0.5
            action [Jump("close_wm_info")]
        text LOCATIONS_WORLDMAP[location]["name"] style "textmaplabel":
            size 60
            ypos 210
            xanchor 0.5
            outlines [ ( 3, "#131720", 1, 1) ]
