"""
Inventory storage, item counts and currency helpers.
"""

init python:
    class Inventory(object):
        def __init__(self, maxSize):
            self.inventory = []
            self.maxSize = maxSize
            self.money = 0

        def _resolve_item(self, item):
            if isinstance(item, Item):
                return item
            return get_item_by_id(item)

        def find_item_index(self, item):
            for index, inv_item in enumerate(self.inventory):
                if inv_item.itemID == item.itemID:
                    return index
            return -1

        def add_item(self, item, amount = 1, popup = False):
            item = self._resolve_item(item)
            if item is None or item.name == "None":
                return False

            if popup:
                add_popup_item(item.itemID, amount)

            item_index = self.find_item_index(item)
            if item_index >= 0:
                self.inventory[item_index].amount += amount
            else:
                self.inventory.append(InvItem(item.itemID, amount))

            return True

        def get_item_amount(self, item):
            item = self._resolve_item(item)
            if item is None or item.name == "None":
                return 0

            item_index = self.find_item_index(item)
            if item_index == -1:
                return 0
            return self.inventory[item_index].amount

        # Includes copies currently equipped by the main party.
        def get_item_amount_full(self, item):
            item = self._resolve_item(item)
            if item is None or item.name == "None":
                return 0

            result = self.get_item_amount(item)
            for cid in MAINCHARS:
                result += gc(cid).has_equipped_amount(item)

            return result

        def check_item_amount(self, item, amount = 1):
            return self.get_item_amount(item) >= amount

        def remove_item(self, item, amount = 1):
            item = self._resolve_item(item)
            if item is None or item.name == "None":
                return False

            item_index = self.find_item_index(item)
            if item_index == -1 or self.inventory[item_index].amount < amount:
                return False

            if self.inventory[item_index].amount == amount:
                self.inventory.pop(item_index)
            else:
                self.inventory[item_index].amount -= amount

            return True

        def get_filtered_items(self, key = -1):
            self.sort_inventory()
            return [
                inv_item
                for inv_item in self.inventory
                if key == ALL or get_item_by_id(inv_item.itemID).category == key
            ]

        def add_money(self, amount, popup = False, sound = True):
            self.money += amount
            if sound:
                play_sfx("coin_money_1", channel = 9)
            if popup:
                add_popup_money(amount)

        def remove_money(self, amount):
            if self.money < amount:
                return False
            self.money -= amount
            return True

        def check_money(self, amount):
            return self.money >= amount

        def get_gold(self):
            return self.money // 10000

        def get_silver(self):
            return self.money // 100 % 100

        def get_copper(self):
            return self.money % 100

        def merge_inventory(self, inventory):
            for inv_item in inventory.inventory:
                self.add_item(inv_item.itemID, inv_item.amount)
            self.add_money(inventory.money)

        def sort_inventory(self):
            self.inventory.sort(key = lambda inv_item: get_item_by_id(inv_item.itemID).sortID)

        def log_contents(self):
            for inv_item in self.inventory:
                renpy.log(f"{inv_item.itemID}: {inv_item.amount}")


    class InvItem(object):
        def __init__(self, itemID, amount):
            self.itemID = itemID
            self.amount = amount
