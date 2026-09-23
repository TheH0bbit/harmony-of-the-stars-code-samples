"""
Interactive world map handling for navigation, lore overlays and dungeon selection.
"""

init python:
    class WorldMapController:
        MAP_WIDTH = 7680
        MAP_HEIGHT = 4320

        def __init__(self):
            self.mode = RPG

            self.zoom = 1.0
            self.zoom_goal = 1.0
            self.icon_zoom = 1.0
            self.zoom_min = 0.25
            self.zoom_max = 2.0

            self.zoom_anchor_map = (0.0, 0.0)
            self.zoom_anchor_screen = (0.0, 0.0)

            # Map position is stored in normalized screen space.
            self.x = 0.0
            self.y = 0.0
            self.target_x = 0.0
            self.target_y = 0.0

            self.dragging = False
            self.gliding = False
            self.drag_start_mouse = (0, 0)
            self.drag_start_map = (0.0, 0.0)
            self.initial_zoom_difference = 0.0
            self.initial_coordinates = (0.0, 0.0)

            self.show_countries = False
            self.show_paths = False
            self.show_regions = False
            self.show_towns = True

            self.info_showing = True
            self.mode_state_backup = None
            self.info_state_backup = None

            self.current_town = "solsticeridge"
            self.current_area = "easternveraxia"
            self.selected_dungeon = None
            self.selected_subarea = None
            self.hovered_subarea = None

            self.map_center = None
            self.wiggle_left = 0
            self.wiggle_right = 0
            self.wiggle_up = 0
            self.wiggle_down = 0

            self.cloud_positions = {}
            self.cloud_anchors = {}
            self.cloud_velocity = {}
            self.cloud_velocity_target = {}
            self.cloud_timers = {}
            self.cloud_override_timer = 0.0

        @staticmethod
        def clamp(value, minimum, maximum):
            return max(minimum, min(value, maximum))

        def clamp_map(self):
            scaled_width = (self.MAP_WIDTH / SCREEN_W) * self.zoom
            scaled_height = (self.MAP_HEIGHT / SCREEN_H) * self.zoom

            min_x = 1 - scaled_width
            min_y = 1 - scaled_height

            if self.mode == RPG and not self.gliding and self.map_center:
                map_x, map_y = self.screen_to_map(0.5, 0.5)
                center_x, center_y = self.map_center

                map_x = self.clamp(
                    map_x,
                    (center_x - self.wiggle_left) / SCREEN_W,
                    (center_x + self.wiggle_right) / SCREEN_W,
                )
                map_y = self.clamp(
                    map_y,
                    (center_y - self.wiggle_up) / SCREEN_H,
                    (center_y + self.wiggle_down) / SCREEN_H,
                )

                self.x = 0.5 - map_x * self.zoom
                self.y = 0.5 - map_y * self.zoom

            self.x = self.clamp(self.x, min_x, 0)
            self.y = self.clamp(self.y, min_y, 0)

        def set_zoom(self, delta):
            self.zoom_goal = self.clamp(
                self.zoom_goal + delta,
                self.zoom_min,
                self.zoom_max,
            )

            mouse_x, mouse_y = renpy.get_mouse_pos()
            screen_x = mouse_x / SCREEN_W
            screen_y = mouse_y / SCREEN_H

            self.zoom_anchor_screen = (screen_x, screen_y)
            self.zoom_anchor_map = self.screen_to_map(screen_x, screen_y)

        def start_drag(self):
            self.dragging = True
            self.zoom_goal = self.zoom
            self.update_zoom()
            self.drag_start_mouse = renpy.get_mouse_pos()
            self.drag_start_map = (self.x, self.y)

        def stop_drag(self):
            self.dragging = False

        def update_movement(self):
            if self.gliding:
                self.dragging = False
                current_x, current_y = self.screen_to_map(0.5, 0.5)

                if self.initial_zoom_difference == 0:
                    goal_x = time_lerp(current_x, self.target_x, 5.0)
                    goal_y = time_lerp(current_y, self.target_y, 5.0)
                else:
                    current_difference = self.zoom - self.zoom_goal
                    factor = 1.0 - current_difference / self.initial_zoom_difference
                    initial_x, initial_y = self.initial_coordinates
                    goal_x = initial_x + (self.target_x - initial_x) * factor
                    goal_y = initial_y + (self.target_y - initial_y) * factor

                reached_target = (
                    abs(goal_x - self.target_x) <= 0.5 / SCREEN_W
                    and abs(goal_y - self.target_y) <= 0.5 / SCREEN_H
                )

                if reached_target:
                    self.x = -self.target_x * self.zoom_goal + 0.5
                    self.y = -self.target_y * self.zoom_goal + 0.5
                    self.gliding = False
                else:
                    self.x = -goal_x * self.zoom + 0.5
                    self.y = -goal_y * self.zoom + 0.5

                self.clamp_map()
                self.zoom_anchor_screen = (0.5, 0.5)
                self.zoom_anchor_map = (self.target_x, self.target_y)
                return

            if not self.dragging:
                return

            mouse_x, mouse_y = renpy.get_mouse_pos()
            dx = mouse_x - self.drag_start_mouse[0]
            dy = mouse_y - self.drag_start_mouse[1]

            self.x = self.drag_start_map[0] + dx / SCREEN_W
            self.y = self.drag_start_map[1] + dy / SCREEN_H
            self.clamp_map()

        def update_zoom(self):
            update_dt()

            if self.zoom == self.zoom_goal:
                return

            t = self.clamp((self.zoom - 1.0) / (self.zoom_max - 1.0), 0.0, 1.0)
            lerp_factor = lerp(4.0, 6.0, t)
            self.zoom = time_lerp(self.zoom, self.zoom_goal, lerp_factor)

            threshold = 0.001 if self.zoom <= 1 else 0.01
            if abs(self.zoom - self.zoom_goal) <= threshold:
                self.zoom = self.zoom_goal

            self.icon_zoom = remap_values(self.zoom, 2.0, 0.8, 1.0, 0.25)

            if not self.gliding:
                anchor_screen_x, anchor_screen_y = self.zoom_anchor_screen
                anchor_map_x, anchor_map_y = self.zoom_anchor_map
                self.x = anchor_screen_x - anchor_map_x * self.zoom
                self.y = anchor_screen_y - anchor_map_y * self.zoom

            self.clamp_map()

        def reset(self):
            self.zoom = 1.0
            self.zoom_goal = 1.0
            self.icon_zoom = 1.0
            self.x = 0.0
            self.y = 0.0
            self.clamp_map()

        def prepare(self, zoom=1.5, x=4734, y=2784):
            self.zoom = zoom
            self.zoom_goal = zoom
            self.icon_zoom = remap_values(self.zoom, 2.0, 0.8, 1.0, 0.25)
            self.center_on_map(x, y)

            if self.mode == LORE:
                self.prepare_lore()
            elif self.mode == RPG:
                self.prepare_rpg()

            self.clamp_map()
            self.zoom_anchor_screen = (0.5, 0.5)
            self.zoom_anchor_map = self.screen_to_map(0.5, 0.5)

        def screen_to_map(self, screen_x, screen_y):
            map_x = (screen_x - self.x) / self.zoom
            map_y = (screen_y - self.y) / self.zoom
            return map_x, map_y

        def map_to_screen(self, map_x, map_y):
            screen_x = self.x + map_x / SCREEN_W * self.zoom
            screen_y = self.y + map_y / SCREEN_H * self.zoom
            return screen_x, screen_y

        def center_on_map(self, map_x, map_y, screen_x=0.5, screen_y=0.5):
            self.x = screen_x - (map_x / SCREEN_W * self.zoom)
            self.y = screen_y - (map_y / SCREEN_H * self.zoom)

        def map_to_screen_int(self, map_x, map_y):
            screen_x = int(self.x * SCREEN_W + map_x * self.zoom)
            screen_y = int(self.y * SCREEN_H + map_y * self.zoom)
            return screen_x, screen_y

        def glide_to(self, zoom, x, y, xoffset=0, yoffset=0):
            self.zoom_goal = zoom
            self.target_x = (x - xoffset / self.zoom_goal) / SCREEN_W
            self.target_y = (y - yoffset / self.zoom_goal) / SCREEN_H
            self.gliding = True
            self.initial_zoom_difference = self.zoom - self.zoom_goal
            self.initial_coordinates = self.screen_to_map(0.5, 0.5)

        def capture_state(self):
            map_x, map_y = self.screen_to_map(0.5, 0.5)
            return {
                "map_x": int(map_x * SCREEN_W),
                "map_y": int(map_y * SCREEN_H),
                "zoom": self.zoom,
                "paths": self.show_paths,
                "regions": self.show_regions,
                "countries": self.show_countries,
                "towns": self.show_towns,
            }

        def restore_state(self, state):
            if not state:
                return

            self.toggle_paths(state["paths"])
            self.toggle_regions(state["regions"])
            self.toggle_countries(state["countries"])
            self.toggle_towns(state["towns"])
            self.glide_to(state["zoom"], state["map_x"], state["map_y"])

        def _set_overlay(self, attribute, screen_name, value=None):
            current = getattr(self, attribute)
            enabled = not current if value is None else value
            setattr(self, attribute, enabled)

            if enabled:
                renpy.show_screen(screen_name)
            else:
                renpy.hide_screen(screen_name)

        def toggle_countries(self, value=None):
            self._set_overlay("show_countries", "s_worldmap_loreoverlay_countries", value)

        def toggle_paths(self, value=None):
            self._set_overlay("show_paths", "s_worldmap_loreoverlay_paths", value)

        def toggle_regions(self, value=None):
            self._set_overlay("show_regions", "s_worldmap_loreoverlay_regions", value)

        def toggle_towns(self, value=None):
            self._set_overlay("show_towns", "s_worldmap_loreoverlay_towns", value)

        def set_all_overlays(self, value):
            self.toggle_regions(value)
            self.toggle_paths(value)
            self.toggle_countries(value)
            self.toggle_towns(value)

        def reset_clouds(self):
            self.cloud_positions = {}
            self.cloud_anchors = {}
            self.cloud_velocity = {}
            self.cloud_velocity_target = {}
            self.cloud_timers = {}
            self.cloud_override_timer = 0.0

        def update_clouds(self):
            if self.mode == LORE:
                return

            if self.cloud_override_timer > 0:
                self.cloud_override_timer -= dt
                return

            max_radius = 50
            max_velocity = 5

            for cloud_id, (x, y) in list(self.cloud_positions.items()):
                anchor_x, anchor_y = self.cloud_anchors[cloud_id]
                velocity_x, velocity_y = self.cloud_velocity.get(cloud_id, (0, 0))
                target_x, target_y = self.cloud_velocity_target.get(cloud_id, (0, 0))
                self.cloud_timers[cloud_id] -= dt

                if self.cloud_timers[cloud_id] <= 0:
                    self.cloud_timers[cloud_id] = random.uniform(2, 6)
                    target_x = random.uniform(-max_velocity, max_velocity)
                    target_y = random.uniform(-max_velocity, max_velocity)
                    self.cloud_velocity_target[cloud_id] = (target_x, target_y)

                velocity_x = time_lerp(velocity_x, target_x, 0.5)
                velocity_y = time_lerp(velocity_y, target_y, 0.5)

                new_x = x + velocity_x * dt
                new_y = y + velocity_y * dt

                dx = new_x - anchor_x
                dy = new_y - anchor_y
                distance = math.hypot(dx, dy)

                if distance > max_radius:
                    pull = (distance - max_radius) * 0.05
                    new_x -= dx / distance * pull
                    new_y -= dy / distance * pull

                self.cloud_positions[cloud_id] = (new_x, new_y)
                self.cloud_velocity[cloud_id] = (velocity_x, velocity_y)

        def switch_mode(self):
            if self.mode == LORE:
                self.prepare_rpg()
            elif self.mode == RPG:
                self.prepare_lore()

        def prepare_lore(self):
            self.mode = LORE
            self.zoom_min = 0.25

            if self.mode_state_backup:
                self.restore_state(self.mode_state_backup)
            else:
                self.zoom_goal = 0.25

            renpy.hide_screen("s_worldmap_rpgoverlay")
            renpy.hide_screen("s_dungeon_info")

        def prepare_rpg(self):
            self.mode = RPG
            area_info = LOCATIONS_WORLDMAP_RPG.get(self.current_area)
            if not area_info:
                return

            self.mode_state_backup = self.capture_state()
            self.set_all_overlays(False)
            self.glide_to(1.0, area_info.get("targetx"), area_info.get("targety"))

            self.map_center = (area_info.get("targetx"), area_info.get("targety"))
            self.wiggle_left = area_info.get("wiggleleft", 0)
            self.wiggle_right = area_info.get("wiggleright", 0)
            self.wiggle_up = area_info.get("wiggleup", 0)
            self.wiggle_down = area_info.get("wiggledown", 0)
            self.zoom_min = 0.9

            self.reset_clouds()
            for cloud_id, cloud in area_info.get("clouds", {}).items():
                cloud_x = cloud["x"]
                cloud_y = cloud["y"]
                self.cloud_anchors[cloud_id] = (cloud_x, cloud_y)

                spawn_x = cloud_x + (cloud_x - self.map_center[0]) / 4
                spawn_y = cloud_y + (cloud_y - self.map_center[1]) / 4
                self.cloud_positions[cloud_id] = (spawn_x, spawn_y)
                self.cloud_velocity[cloud_id] = (0, 0)
                self.cloud_velocity_target[cloud_id] = (0, 0)
                self.cloud_timers[cloud_id] = 0

            renpy.show_screen("s_worldmap_rpgoverlay")
            renpy.hide_screen("s_wm_info")


default worldmap = WorldMapController()

# Labels and screens

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

    timer 0.03 action [Function(worldmap.update_zoom), Function(worldmap.update_movement), Function(worldmap.update_clouds)] repeat True

    fixed at popin_bounce, fadein:
        align (0.5, 0.5)
        add Solid("#0008")

        fixed:
            xpos 0
            ypos 0
            xsize SCREEN_W
            ysize SCREEN_H
            clipping True

        key "mousedown_1" action Function(worldmap.start_drag)
        key "mouseup_1" action Function(worldmap.stop_drag)
        key "mousedown_4" action Function(worldmap.set_zoom, 0.2)
        key "mousedown_5" action Function(worldmap.set_zoom, -0.2)

        add "gui/maps/worldmap/worldmap_base.png" at colortransform(tint=todTintDict[tod], alphav = 1):
            subpixel True
            xpos worldmap.x
            ypos worldmap.y
            zoom worldmap.zoom


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

        hbox:
            align(0.99, 0.99)
            spacing 0

            imagebutton:
                idle "gui/icons/return_icon.png"
                action [Jump("return_worldmap")] at dyn_hover_effect

        if worldmap.mode == LORE and not worldmap.info_showing:
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
                            selected worldmap.show_countries
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(worldmap.toggle_countries)
                        text "Countries & Borders" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5
                    fixed:
                        xysize (250, 75)
                        button at dyn_hover_effect:
                            xysize (250, 75)
                            align (0.5, 0.5)
                            selected worldmap.show_regions
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(worldmap.toggle_regions)
                        text "Major Regions" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5
                    fixed:
                        xysize (250, 75)
                        button at dyn_hover_effect:
                            xysize (250, 75)
                            align (0.5, 0.5)
                            selected worldmap.show_paths
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(worldmap.toggle_paths)
                        text "Towns & Travel Routes" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5
                    fixed:
                        xysize (250, 75)
                        button at dyn_hover_effect:
                            xysize (250, 75)
                            align (0.5, 0.5)
                            selected worldmap.show_towns
                            selected_background "gui/maps/worldmap/worldmap_selectionbutton_selected.png"
                            background "gui/maps/worldmap/worldmap_selectionbutton.png"
                            action Function(worldmap.toggle_towns)
                        text "Town Icons" style "textstarry":
                            yoffset 2
                            align (0.5, 0.5)
                            text_align 0.5

            if not worldmap.info_showing:
                hbox:
                    align (0.01, 0.01)
                    imagebutton:
                        xysize (140, 120)
                        yalign 0.5
                        idle "gui/icons/lore_icon.png"
                        hovered [Function(set_tooltip_data, "Swap Mode", 0.01, 0.04, True, "textmaplabel")]
                        unhovered [Function(clear_tooltip_data)]
                        action [Function(worldmap.switch_mode)] at dyn_hover_effect

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
        add "gui/maps/worldmap/worldmap_countries_s.png":
            subpixel True
            xpos worldmap.x
            ypos worldmap.y
            zoom worldmap.zoom * 2

screen s_worldmap_loreoverlay_paths():
    zorder 2
    fixed at screen_dissolve:
        align (0.5, 0.5)
        add "gui/maps/worldmap/worldmap_paths_s.png":
            subpixel True
            xpos worldmap.x
            ypos worldmap.y
            zoom worldmap.zoom * 2

screen s_worldmap_loreoverlay_regions():
    zorder 3
    fixed at screen_dissolve:
        align (0.5, 0.5)
        add "gui/maps/worldmap/worldmap_labels_regions_s.png":
            subpixel True
            xpos worldmap.x
            ypos worldmap.y
            zoom worldmap.zoom * 2

screen s_worldmap_loreoverlay_towns():
    zorder 4
    fixed at screen_dissolve:
        align (0.5, 0.5)

        for loc_id, loc in LOCATIONS_WORLDMAP.items():
            $ sx, sy = worldmap.map_to_screen_int(loc["x"], loc["y"])
            if -100 < sx < SCREEN_W+100 and -100 < sy < SCREEN_H+100:
                if worldmap.zoom >= 0.8:
                    if loc["landmarks"][0] != "":
                        if loc["type"] == TOWN:
                            imagebutton at dyn_hover_effect, dyn_zoom(worldmap.icon_zoom):
                                idle f"gui/icons/sigils/256/{loc['icon']}"
                                xpos sx
                                ypos sy
                                anchor (0.5, 0.5)
                                action [SetVariable("selectedLocation", loc_id), Jump("reopen_wm_info")]
                    else:
                        imagebutton at dyn_zoom(worldmap.icon_zoom), colortransform(saturation = 0):
                            idle f"gui/icons/sigils/256/{loc['icon']}"
                            xpos sx
                            ypos sy
                            anchor (0.5, 0.5)
                            action [SetVariable("tempstring", "This towns info is still missing. Check again in future updates!"), Jump("mc_say")]

                else:
                    if loc["landmarks"][0] != "":
                        if loc["type"] == TOWN:
                            imagebutton at dyn_hover_effect:
                                idle f"gui/icons/sigils/64/{loc['icon']}"
                                xpos sx
                                ypos sy
                                anchor (0.5, 0.5)
                                action [SetVariable("selectedLocation", loc_id), Jump("reopen_wm_info")]
                    else:
                        imagebutton at colortransform(saturation = 0):
                            idle f"gui/icons/sigils/64/{loc['icon']}"
                            xpos sx
                            ypos sy
                            anchor (0.5, 0.5)
                            action [SetVariable("tempstring", "This towns info is still missing. Check again in future updates!"), Jump("mc_say")]


screen s_worldmap_rpgoverlay():
    zorder 1
    fixed at screen_dissolve:
        align(0.5, 0.5)

        # Dungeon markers
        for dungeon_id, dungeon in LOCATIONS_WORLDMAP_RPG.get(worldmap.current_area).get("dungeons").items():
            if not flags.has_flag(MAP, "rpg", dungeon_id):
                continue

            $ sx, sy = worldmap.map_to_screen_int(dungeon["x"], dungeon["y"])
            imagebutton at dyn_hover_effect, dyn_zoom(worldmap.zoom*0.4):
                idle f"gui/icons/sigils/256/{dungeon['icon']}"
                xpos sx
                ypos sy
                anchor (0.5, 0.5)
                action [Function(setattr, worldmap, "selected_dungeon", dungeon_id), Jump("reopen_dungeon_info")]

            text dungeon["name"] at dyn_zoom(worldmap.zoom*0.5):
                font "fonts/map/IM FELL English Bold.ttf"
                color "#ffce64"
                outlines [ ( 3, "#2b2b2b", 2, 2) ]
                anchor (0.5, 0.5)
                xpos sx
                ypos sy
                size 40


        # Travel locations
        for loc_id, loc in LOCATIONS_WORLDMAP.items():
            if not flags.has_flag(MAP, "rpg", loc_id):
                continue
            $ sx, sy = worldmap.map_to_screen_int(loc["x"], loc["y"])
            if -100 < sx < SCREEN_W+100 and -100 < sy < SCREEN_H+100:
                if loc["type"] == TOWN:
                    imagebutton at dyn_hover_effect, dyn_zoom(worldmap.zoom*0.5):
                        idle f"gui/icons/sigils/256/{loc['icon']}"
                        xpos sx
                        ypos sy
                        anchor (0.5, 0.5)
                        action [SetVariable("selectedLocation", loc_id), Jump("return_worldmap")]

                    text loc["name"] at dyn_zoom(worldmap.zoom*0.5):
                        font "fonts/map/IM FELL English Bold.ttf"
                        color "#ffce64"
                        outlines [ ( 3, "#2b2b2b", 2, 2) ]
                        anchor (0.5, 0.5)
                        xpos sx
                        ypos sy
                        size 50

        for cloud_id, cloud in LOCATIONS_WORLDMAP_RPG.get(worldmap.current_area).get("clouds").items():
            $ sx, sy = worldmap.map_to_screen(worldmap.cloud_positions[cloud_id][0], worldmap.cloud_positions[cloud_id][1])
            add f"gui/maps/clouds/{cloud.get('icon')}.png" at dyn_zoom(worldmap.zoom*cloud.get('zoomfactor', 1)), fadein(time = 1.5), colortransform(tint=todTintDict_weaker[tod], alphav = 1):
                subpixel True
                pos (sx, sy)
                anchor (0.5, 0.5)

        $ sx, sy = worldmap.map_to_screen(4835, 2138)
        add f"gui/maps/clouds/celestialpeak.png" at dyn_zoom(worldmap.zoom), colortransform(tint=todTintDict_weaker[tod], alphav = 1):
            pos (sx, sy)
            anchor (0.5, 0.5)

        if not worldmap.info_showing:
            add f"gui/maps/general/scroll_{worldmap.current_area}.png" at fadein(), move_simple(0.5, 0.095, 2, 1.5), dyn_zoom_timed(1.0, 0.8, 2, 1.5):
                align (0.5, 0.5)

            hbox:
                align (0.01, 0.01)
                imagebutton:
                    xysize (140, 120)
                    yalign 0.5
                    idle "gui/icons/travel_icon.png"
                    hovered [Function(set_tooltip_data, "Swap Mode", 0.01, 0.04, True, "textmaplabel")]
                    unhovered [Function(clear_tooltip_data)]
                    action [Function(worldmap.switch_mode)] at dyn_hover_effect

                text f"Travel":
                    font "fonts/map/IM FELL English Bold.ttf"
                    xoffset -10
                    yalign 0.5
                    size 75
                    color "#ffce64"
                    outlines [ ( 3, "#2b2b2b", 2, 2) ]

label reopen_dungeon_info:
    $ worldmap.glide_to(2.0, LOCATIONS_WORLDMAP_RPG[worldmap.current_area]['dungeons'][worldmap.selected_dungeon]["x"], LOCATIONS_WORLDMAP_RPG[worldmap.current_area]['dungeons'][worldmap.selected_dungeon]["y"], 640)
    $ worldmap.info_showing = True
    $ worldmap.info_state_backup = worldmap.capture_state()
    $ worldmap.set_all_overlays(False)
    hide screen s_dungeon_info
    show screen s_dungeon_info
    ""

label close_dungeon_info:
    hide screen s_dungeon_info
    $ clear_tooltip_data()
    $ worldmap.restore_state(worldmap.info_state_backup)
    $ worldmap.info_showing = False
    ""


screen s_dungeon_info:
    zorder 6
    modal True
    $ dungeoninfo = LOCATIONS_WORLDMAP_RPG[worldmap.current_area]['dungeons'][worldmap.selected_dungeon]

    fixed at popin_bounce, fadein:
        align (0.5, 0.5)
        if dungeoninfo["bg"]:
            add f"gui/maps/general/dungeonbgs/{worldmap.selected_dungeon}.png":
                yalign 0.5

        add "gui/maps/general/dungeon_info_bg.png":
            align (0.5, 0.5)

        vbox:
            xsize 1280
            ypos 54
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
                    viewport:
                        mousewheel True
                        ysize 782
                        vbox:
                            for subarea, areainfo in DUNGEON_INFO[worldmap.selected_dungeon]["subareas"].items():
                                if flags.dungeons.has(worldmap.selected_dungeon, subarea):
                                    fixed:
                                        ysize 100
                                        button at dyn_hover_effect, dyn_xyzoom(xz = 0.75):
                                            selected worldmap.selected_subarea == subarea
                                            xysize (360, 100)
                                            background "gui/quests/quest_bg_slide.png"
                                            selected_foreground "gui/quests/quest_bg_slide_selected.png"
                                            hovered [Function(setattr, worldmap, "hovered_subarea", subarea)]
                                            action Function(setattr, worldmap, "selected_subarea", subarea)

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
                                            selected worldmap.selected_subarea == subarea
                                            xysize (360, 100)
                                            background "gui/quests/quest_bg_slide.png"
                                            selected_foreground "gui/quests/quest_bg_slide_selected.png"
                                            hovered [Function(setattr, worldmap, "hovered_subarea", subarea)]
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
                        if worldmap.selected_subarea:
                            $ areaInfo = DUNGEON_INFO[worldmap.selected_dungeon]["subareas"][worldmap.selected_subarea]
                            null height 20

                            textbutton "Go to Dungeon!" style "textmaplabel" at dyn_hover_effect_inverse:
                                text_size 80
                                align (0.5, 0.5)
                                action Function(load_dungeon, areaInfo)

                            null height 70





    fixed:
        pos (1600, 540)
        imagebutton at dyn_hover_effect, dyn_delayed_zoomout_alpha(worldmap.icon_zoom*0.4, worldmap.icon_zoom*0.4):
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
    $ worldmap.glide_to(2.0, LOCATIONS_WORLDMAP[selectedLocation]["x"], LOCATIONS_WORLDMAP[selectedLocation]["y"], 640)
    $ worldmap.info_showing = True
    $ worldmap.info_state_backup = worldmap.capture_state()
    $ worldmap.set_all_overlays(False)
    hide screen s_wm_info
    show screen s_wm_info(selectedLocation)
    ""

label close_wm_info:
    hide screen s_wm_info
    $ worldmap.restore_state(worldmap.info_state_backup)
    $ worldmap.info_showing = False
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

        add "gui/maps/general/worldmap_infoscreen_bg.png" at colortransform(tint=nationTintDict[LOCATIONS_WORLDMAP[location]["partof"]])
        add "gui/maps/general/worldmap_infoscreen_bg_ornaments.png"

        fixed:
            pos (0, 49)

            fixed:
                pos (920, 90)
                xysize (360, 280)
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
                    text LOCATIONS_WORLDMAP[location]["description"].split("\n\n")[0] style "textmaptext":
                        size 22
                        yalign 0.0
                        xalign 0.0
                        outlines [ ( 2, "#131720", 0, 0) ]
                        color "#ffe797"

                fixed:
                    xysize (1180, 180)
                    xpos 30
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





    fixed:
        pos (1600, 540)
        imagebutton at dyn_hover_effect, dyn_delayed_zoomout_alpha(worldmap.icon_zoom*0.4, worldmap.icon_zoom*0.4):
            idle f"gui/icons/sigils/{LOCATIONS_WORLDMAP[location]['icon']}"
            xanchor 0.5
            yanchor 0.5
            action [Jump("close_wm_info")]
        text LOCATIONS_WORLDMAP[location]["name"] style "textmaplabel":
            size 60
            ypos 210
            xanchor 0.5
            outlines [ ( 3, "#131720", 1, 1) ]
