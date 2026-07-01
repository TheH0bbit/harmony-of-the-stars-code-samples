"""
Character Stats
====================

Defines the Stats data model used throughout the project.

The class represents the collection of numerical attributes that
describe a character's combat capabilities. Statistics can be
combined, modified and queried by gameplay systems such as combat,
equipment, skills and progression.

"""

init python:
    class Stats(object):
        def __init__(self, hp = 0, mp = 0, stamina = 0, speed = 0, strength = 0, magicPow = 0, dexterity = 0, luck = 0, constitution = 0, resistance = 0, denormalize = 0):
            self.hp = hp
            self.mp = mp
            self.stamina = stamina
            self.strength = strength
            self.magicPow = magicPow
            self.constitution = constitution
            self.resistance = resistance
            self.speed = speed
            self.dexterity = dexterity
            self.luck = luck
            if denormalize != 0:
                factor = denormalize / (self.speed + self.strength + self.magicPow + self.dexterity + self.constitution + self.resistance)
                self.mult_stats_round(factor)
                self.mp = mp
                self.hp = hp
                self.stamina = stamina

        def add_stats(self, incrStats):
            self.hp += incrStats.hp
            self.mp += incrStats.mp
            self.stamina += incrStats.stamina
            self.strength += incrStats.strength
            self.magicPow += incrStats.magicPow
            self.constitution += incrStats.constitution
            self.resistance += incrStats.resistance
            self.speed += incrStats.speed
            self.dexterity += incrStats.dexterity
            self.luck += incrStats.luck


        def mult_stats(self, factor):
            self.hp = self.hp * factor
            self.mp = self.mp * factor
            self.stamina = self.stamina * factor
            self.strength = self.strength * factor
            self.magicPow = self.magicPow * factor
            self.constitution = self.constitution * factor
            self.resistance = self.resistance * factor
            self.speed = self.speed * factor
            self.dexterity = self.dexterity * factor
            self.luck = self.luck * factor

        def mult_stats_round(self, factor):
            self.hp = round(self.hp * factor)
            self.mp = round(self.mp * factor)
            self.stamina = round(self.stamina * factor)
            self.strength = round(self.strength * factor)
            self.magicPow = round(self.magicPow * factor)
            self.constitution = round(self.constitution * factor)
            self.resistance = round(self.resistance * factor)
            self.speed = round(self.speed * factor)
            self.dexterity = round(self.dexterity * factor)
            self.luck = round(self.luck * factor)

        def copy_stats(self):
            return Stats(hp = self.hp, mp = self.mp, stamina = self.stamina, strength = self.strength, magicPow = self.magicPow, constitution = self.constitution, resistance = self.resistance, speed = self.speed, dexterity = self.dexterity, luck = self.luck)

        def reset(self):
            self.mp = 0
            self.hp = 0
            self.stamina = 0
            self.strength = 0
            self.magicPow = 0
            self.constitution = 0
            self.resistance = 0
            self.speed = 0
            self.dexterity = 0
            self.luck = 0
        
        def print(self):
            #renpy.log(f"printing Stats - HP:{self.hp:.2f}, MP:{self.mp:.2f}, SPD:{self.speed:.2f}, STR:{self.strength:.2f}, MAG:{self.magicPow:.2f}, DEX:{self.dexterity:.2f}, CON:{self.constitution:.2f}, RES:{self.resistance:.2f}")
            return f"printing Stats - HP:{self.hp:.2f}, MP:{self.mp:.2f}, STA:{self.stamina:.2f}, STR:{self.strength:.2f}, MAG:{self.magicPow:.2f}, CON:{self.constitution:.2f}, RES:{self.resistance:.2f}, SPD:{self.speed:.2f}, DEX:{self.dexterity:.2f}, LUCK:{self.luck:.2f}"

        def get_power(self, attType):
            damage_calcs = {
                MELEE: self.strength,
                RANGED: self.strength,
                MAGIC: self.magicPow
            }
            return damage_calcs.get(attType, 0)


        def get_defense(self, attType):
            resistance_calcs = {
                MELEE: self.constitution,
                RANGED: self.constitution,
                MAGIC: self.resistance
            }
            return resistance_calcs.get(attType, 0)

    class Affinities(object):
        def __init__(self, energy = 1.0, manipulation = 1.0, light = 1.0, shadow = 1.0,  origin = 1.0, force = 1.0):
            self.energy = energy
            self.manipulation = manipulation
            self.light = light
            self.shadow = shadow
            self.origin = origin
            self.force = force

        def add_affinities(self, affinities):
            self.energy *= affinities.energy
            self.manipulation *= affinities.manipulation
            self.light *= affinities.light
            self.shadow *= affinities.shadow
            self.origin *= affinities.origin
            self.force *= affinities.force

        def copy_affinites(self):
            return Affinities(self.energy, self.manipulation, self.light, self.shadow, self.origin, self.force)

        def get_affinity(self, magicType):
            affinity_calcs = {
                NONE: 1,
                ENERGY: self.energy,
                MANIPULATION: self.manipulation,
                LIGHT: self.light,
                SHADOW: self.shadow,
                ORIGIN: self.origin,
                FORCE: self.force
            }
            return affinity_calcs.get(magicType, 1)