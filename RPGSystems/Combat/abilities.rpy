"""
Ability Definitions
===================

Defines the Ability data model together with the global ability
registry.

Abilities describe active combat actions and their execution
logic. Character statistics are intentionally handled by the
skill system rather than abilities themselves, keeping character
progression separate from combat behaviour.
"""

init python:

    ABILITIES = {}

    def register_ability(ability):
        ABILITIES[ability.abilityID] = ability

    def get_ability_by_id(abilityID):
        if isinstance(abilityID, Ability):
            return abilityID
        return ABILITIES.get(abilityID)

    class Ability(object):
        def __init__(self, abilityID, name, descr, power = 0):
            self.abilityID = abilityID
            self.name = name
            self.descr = descr
            self.power = power
            register_ability(self)

    class DamageAbility(Ability):
        def __init__(self, abilityID, name, descr, power, mp, stamina = 0, radius = SINGLE, targeting = HOSTILE, activation = INSTANT, reach = MELEE, attType = MELEE, dmgType = ADAPTIVE, magicType = NONE, statusEffects = []):
            super().__init__(abilityID, name, descr, power)
            self.mp = mp
            self.stamina = stamina
            self.radius = radius
            self.targeting = targeting
            self.activation = activation
            self.reach = reach 
            self.attType = attType
            self.dmgType = dmgType
            self.magicType = magicType
            self.statusEffects = statusEffects

    class SupportAbility(Ability):
        def __init__(self, abilityID, name, descr, power, mp, stamina = 0, radius = SINGLE, targeting = FRIENDLY, activation = INSTANT, reach = RANGED, magicType = NONE, statusEffects = [], category = NONE):
            super().__init__(abilityID, name, descr, power)
            self.mp = mp
            self.stamina = stamina
            self.radius = radius
            self.targeting = targeting
            self.activation = activation
            self.reach = reach
            self.magicType = magicType
            self.statusEffects = statusEffects
            self.category = category

    class ControlAbility(Ability):
        def __init__(self, abilityID, name, descr, power, mp, stamina = 0, radius = SINGLE, targeting = FRIENDLY, activation = INSTANT, reach = RANGED, magicType = NONE, statusEffects = [], category = NONE):
            super().__init__(abilityID, name, descr, power)
            self.mp = mp
            self.stamina = stamina
            self.radius = radius
            self.targeting = targeting
            self.activation = activation
            self.reach = reach
            self.magicType = magicType
            self.statusEffects = statusEffects
            self.category = category


    class PassiveAbility(Ability):
        def __init__(self, abilityID, name, descr, statusEffects = [], category = NONE, power = 0):
            super().__init__(abilityID, name, descr, power)
            self.statusEffects = statusEffects
            self.category = category

    class OverworldAbility(Ability):
        def __init__(self, abilityID, name, descr, power, mp, stamina = 0, shape = CIRCLE, radius = 200, friendlyfire = False, activation = INSTANT, reach = 200, attType = MELEE, dmgType = ADAPTIVE, magicType = NONE, statusEffects = []):
            super().__init__(abilityID, name, descr, power)
            self.mp = mp
            self.stamina = stamina
            self.shape = shape
            #Clarification: Radius indicates the radius of the affected Area, not the radius of the casting range, see reach
            self.radius = radius
            self.friendlyfire = friendlyfire
            self.activation = activation
            #Reach indicates the radius of the casting range, 10 means 500px
            self.reach = reach
            self.attType = attType
            self.dmgType = dmgType
            self.magicType = magicType
            self.statusEffects = statusEffects



    class SpecialAbility(Ability): #TODO
        def __init__(self, abilityID, name, descr, power, mp, stamina = 0, radius = SINGLE, targeting = HOSTILE, activation = INSTANT, reach = MELEE, attType = MELEE, dmgType = ADAPTIVE, magicType = NONE, statusEffects = []):
            super().__init__(abilityID, name, descr, power)
            self.mp = mp
            self.stamina = stamina
            self.radius = radius
            self.targeting = targeting
            self.activation = activation
            self.reach = reach 
            self.attType = attType
            self.dmgType = dmgType
            self.magicType = magicType
            self.statusEffects = statusEffects
