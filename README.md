# Harmony of the Stars – Gameplay Systems

This repository contains representative gameplay systems from *Harmony of the Stars*, a solo-developed RPG / Visual Novel project.

The included code focuses on the gameplay architecture and systems that I implemented during development. Since these systems originate from a larger project, some references to other project modules remain.

The gameplay systems in Harmony of the Stars follow a modular architecture where static game data (items, quests, skills, locations) is separated from runtime state, allowing individual systems to interact through shared interfaces while remaining largely independent.

For gameplay images and additional technical information:

https://theh0bbit.github.io/

## Suggested Reading

If you're reviewing the code, I recommend starting with:

- RPGSystems/Combat/combat.rpy
- RPGSystems/Items/inventory.rpy
- RPGSystems/quests.rpy
- Navigation/worldmap.rpy

