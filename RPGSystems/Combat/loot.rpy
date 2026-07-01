"""
Loot Definitions
================

Defines loot table structures and helper functions used to
generate combat rewards.

Loot tables specify experience, currency and potential item
drops awarded after combat encounters.
"""

init python:
    LOOTTABLES = {}

    def register_loot(loot):
        LOOTTABLES[loot.lootID] = loot

    def get_loot_by_id(lootID):
        return LOOTTABLES.get(lootID)


    class Loot(object):
        def __init__(self, lootID, exp, money, loottable):
            self.lootID = lootID
            self.exp = exp
            self.money = money
            self.loottable = loottable #list of tuples: (itemID, chance(1(lowest)-100(highest)), rolls)
            register_loot(self)

        def roll_loot(self):
            reward = []
            for lootInfo in self.loottable:
                for i in range(lootInfo[2]):
                    if renpy.random.randint(1, 100) <= lootInfo[1]:
                        reward.append(lootInfo[0])
            return reward

        def get_exp(self, levelDiff):
            if levelDiff >= 0:
                return round(min(self.exp * (1+levelDiff**3/125), self.exp * 10))
            else:
                return round(max(self.exp / (1+abs(levelDiff**3/125)), self.exp / 10))

        def roll_money(self):
            return round(self.money * (1.0 - renpy.random.randint(0, 80)/100))


    ############################################ LOOTTABLES ##################################################

    goblinLoot = Loot("goblin", 40, 5, (("silverring1", 10, 1),))
    goblinArcherLoot = Loot("goblin_archer", 50, 5, (("silverring1", 10, 1),))
    wolfLoot = Loot("wolf_base", 75, 5, ())
    goonmeleeLoot = Loot("goonmelee_generic", 100, 15, (("twohander", 5, 1), ))
    goonrangedLoot = Loot("goonranged_generic", 100, 15, (("yukibow", 5, 1), ))

    