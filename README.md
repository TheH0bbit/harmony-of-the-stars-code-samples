# Harmony of the Stars - Code Samples

This repository contains a curated selection of gameplay and navigation code from *Harmony of the Stars*, a larger Ren'Py project I have been developing.

It is intended as a code sample rather than a standalone build. The files still reference project-specific assets, constants, data definitions and supporting systems that are not included here.

## Featured samples

### `NavigationSystems/worldmap.rpy`

World map interaction and presentation logic. `WorldMapController` keeps camera movement, zooming, dragging, map modes, lore overlays, location selection and ambient cloud state together while Ren'Py screens handle presentation.

### `RPGSystems/Combat/combat.rpy`

The main turn-based combat implementation. It includes encounter state, hero and enemy combat components, turn order, targeting, damage calculations, status effects, enemy decision logic and combat UI state.

### `RPGSystems/Chars/characters.rpy`

Character registration and persistent progression state. Static definitions are kept separate from save-backed runtime data, with helpers for progression, equipment, skills, relationships and combat-facing properties.

### `RPGSystems/quests.rpy`

A data-driven quest system with persistent quest state, stage progression, requirement checks, rewards and metadata access. Quest definitions remain separate from the player's current progress.

## Supporting systems

The repository also includes smaller systems used by the featured samples, including inventory and item handling, skills and stats, abilities, loot, status effects, progression flags, character schedules and location navigation.

`RPGSystems/Items/inventory.rpy` and `RPGSystems/Items/items.rpy`, for example, show the lightweight item registry and inventory structures used by the character and combat systems.

## Project structure

```text
NavigationSystems/
    characterLocations.rpy
    locationCatches.rpy
    locationsInfo.rpy
    locationsNavigator.rpy
    worldmap.rpy

RPGSystems/
    Chars/
        characters.rpy
        skillSystem.rpy
        stats.rpy
    Combat/
        abilities.rpy
        combat.rpy
        loot.rpy
        statusEffects.rpy
    Items/
        inventory.rpy
        items.rpy
    flags.rpy
    quests.rpy
```

The `.rpy` format mixes Python with Ren'Py-specific screen and label syntax, so these files are not intended to run as ordinary Python modules. Some content-heavy project data has also been omitted to keep the repository focused on system code.

## What these samples cover

* Persistent game state separated from runtime wrappers and controllers
* Data-driven RPG and progression systems
* Turn-based combat and status-effect handling
* Inventory, equipment and item registration
* Navigation and character scheduling
* Ren'Py screen integration with Python-side gameplay logic
* Refactoring a state-heavy world map into a controller-based structure

## Notes

This is a snapshot of code from an actively developed personal project. It is intentionally selective and not a complete representation of the full game or its dependencies.
