"""
Status-effect definitions used by the combat system.
"""

init python:
    STATUSEFFECTS = {}

    def register_statuseffect(statuseffect):
        STATUSEFFECTS[statuseffect.statusID] = statuseffect

    def get_statuseffect_by_id(statusID):
        return STATUSEFFECTS.get(statusID)

    class StatusEffect(object):
        def __init__(self, statusID, statusType, name, descr, duration, chance):
            self.statusID = statusID
            self.statusType = statusType
            self.name = name
            self.descr = descr
            self.duration = duration
            self.chance = chance
            register_statuseffect(self)
    
    class Buff(StatusEffect):
        def __init__(self, statusID, statusType, name, descr, duration = 1, chance = 0, strength = 0, magicPow = 0, constitution = 0, resistance = 0, speed = 0, dexterity = 0, luck = 0):
            super().__init__(statusID, statusType, name, descr, duration, chance)
            self.stats = Stats(0, 0, 0, strength, magicPow, constitution, resistance, speed, dexterity, luck)

    class DoT(StatusEffect):
        def __init__(self, statusID, statusType, name, descr, duration = 1, chance = 0, power = 0, magicType = -1):
            super().__init__(statusID, statusType, name, descr, duration, chance)
            self.power = power
            self.duration = duration
            self.magicType = magicType

    class Regen(StatusEffect):
        def __init__(self, statusID, statusType, name, descr, duration = 1, chance = 0, hpRegen = 0, mpRegen = 0):
            super().__init__(statusID, statusType, name, descr, duration, chance)
            self.hpRegen = hpRegen
            self.mpRegen = mpRegen

    class Stun(StatusEffect):
        def __init__(self, statusID, statusType, name, descr, duration = 1, chance = 10):
            super().__init__(statusID, statusType, name, descr, duration, chance)


    class Taunt(StatusEffect):
        def __init__(self, statusID, statusType, name, descr, duration = 1, chance = 100):
            super().__init__(statusID, statusType, name, descr, duration, chance)

    class Counter(StatusEffect):
        def __init__(self, statusID, statusType, name, descr, duration = 1, chance = 0, power = 0, category = PARRY):
            super().__init__(statusID, statusType, name, descr, duration, chance)
            self.power = power
            self.category = category



