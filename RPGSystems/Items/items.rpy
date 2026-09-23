"""
Shared item definitions, registration and equipment item types.
"""

init python:
    ITEMS = {}

    def register_item(item):
        ITEMS[item.itemID] = item

    def get_item_by_id(itemID):
        return ITEMS.get(itemID)

    def check_wpncategory(wpnCategory, item):
        if NONE in wpnCategory:
            return False
        if ONEHANDED in wpnCategory and item.wpnCategory < 10:
            return True
        if TWOHANDED in wpnCategory and item.wpnCategory >= 10:
            return True
        return item.wpnCategory in wpnCategory

    def money_to_gold(amount):
        return amount // 10000

    def money_to_silver(amount):
        return amount // 100 % 100

    def money_to_copper(amount):
        return amount % 100


    class Item(object):
        def __init__(self, itemID, sortID, name, category, descr, stats = None, affinities = None):
            self.itemID = itemID
            self.sortID = sortID
            self.name = name
            self.category = category
            self.descr = descr
            self.stats = stats if stats is not None else Stats()
            self.affinities = affinities if affinities is not None else Affinities()
            register_item(self)

        @property
        def inspect(self):
            return f"{self.name} \nID: {self.itemID}\nCategory: {self.category}\ndescr: {self.descr}"

        @property
        def hp(self): return self.stats.hp

        @property
        def mp(self): return self.stats.mp

        @property
        def stamina(self): return self.stats.stamina

        @property
        def speed(self): return self.stats.speed

        @property
        def strength(self): return self.stats.strength

        @property
        def melee(self): return self.stats.strength

        @property
        def ranged(self): return self.stats.strength

        @property
        def magicPow(self): return self.stats.magicPow

        @property
        def dexterity(self): return self.stats.dexterity

        @property
        def luck(self): return self.stats.luck

        @property
        def constitution(self): return self.stats.constitution

        @property
        def resistance(self): return self.stats.resistance


    class Weapon(Item):
        def __init__(self, itemID, sortID, name, category, descr, wpnCategory, dmgType, stats = None, affinities = None):
            super().__init__(itemID, sortID, name, category, descr, stats, affinities)
            self.wpnCategory = wpnCategory
            self.dmgType = dmgType


    class Cloth(Item):
        def __init__(self, itemID, sortID, name, category, descr, stats = None, affinities = None):
            super().__init__(itemID, sortID, name, category, descr, stats, affinities)


    class Accessoire(Item):
        def __init__(self, itemID, sortID, name, category, descr, stats = None, affinities = None):
            super().__init__(itemID, sortID, name, category, descr, stats, affinities)
