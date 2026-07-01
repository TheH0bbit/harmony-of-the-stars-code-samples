"""
Inventory System
================

Implements inventory management for characters and the player.

Responsibilities
----------------

• Item storage
• Item stacking
• Adding and removing items
• Currency management
• Inventory queries
• Equipment-aware item counting

Architecture
------------

The inventory stores lightweight inventory entries rather than
duplicating item definitions. Gameplay systems reference the
shared item registry defined in items.rpy, allowing item data
to remain centralized while inventories only track ownership
and quantities.

Collaborates with
-----------------

• Item Registry
• Equipment System
• Shops
• Crafting
• Quests
• Character System
"""

init python:
    class Inventory(object):
        def __init__(self, maxSize):
            self.inventory = []
            self.maxSize = maxSize
            self.money = 0

            self.itemIndex = -1 #last searched items index, if not in inventory then -1

        # Returns the index of an item within the inventory, or -1 if the item is not present.
        def find_item_index(self, item):
            for i, inv in enumerate(self.inventory):
                if inv.itemID == item.itemID:
                    return i
            return -1
        
        #Adds Item to Inventory
        def add_item(self, item, amount = 1, popup = False):
            if not isinstance(item, Item):
                item = get_item_by_id(item)
            if item.name == "None":
                return
            if popup:
                add_popup_item(item.itemID, amount)

            self.itemIndex = self.find_item_index(item)
            if self.itemIndex >= 0:
                renpy.log(f"Found ItemInstance already in Inventory, adding more {item.itemID}")
                self.inventory[self.itemIndex].amount += amount
            else:
                self.inventory.append(InvItem(item.itemID, amount))
                renpy.log(f"didn't find ItemInstance in Inventory, adding instance {item.itemID}")
            return

        #Returns amount of item in inventory 
        def get_item_amount(self, item):
            if not isinstance(item, Item):
                item = get_item_by_id(item)
            if item.name == "None":
                return 0
            self.itemIndex = self.find_item_index(item)
            if self.itemIndex == -1:
                return 0
            else: 
                return self.inventory[self.itemIndex].amount

        #Returns amount of item in inventory + equipped items taken into account as well! ONLY USE THIS ON MAIN PLAYER INVENTORY!!!!
        def get_item_amount_full(self, item):
            if not isinstance(item, Item):
                item = get_item_by_id(item)
            if item.name == "None":
                return 0
            self.itemIndex = self.find_item_index(item)
            result = 0
            if self.itemIndex == -1:
                pass
            else: 
                result += self.inventory[self.itemIndex].amount

            for cid in MAINCHARS:
                char = gc(cid)
                result += char.has_equipped_amount(item)

            return result

        #Checks if the specified amount of items are available in inventory
        def check_item_amount(self, item, amount=1):
            if not isinstance(item, Item):
                item = get_item_by_id(item)
            if item.name == "None":
                return 0
            self.itemIndex = self.find_item_index(item)
            if self.itemIndex != -1:
                if self.inventory[self.itemIndex].amount >= amount:
                    return True
                else:
                    return False
            else:
                return False

        #removes item from inventory if possible, returns true if successful
        def remove_item(self, item, amount = 1):
            if not isinstance(item, Item):
                item = get_item_by_id(item)
            if item.name == "None":
                return 0
            if self.check_item_amount(item, amount):
                if self.inventory[self.itemIndex].amount == amount:
                    self.inventory.pop(self.itemIndex)
                    renpy.log(f"removing itemInstance completely {amount} from Inventory {item.itemID}")
                    return True
                else:
                    self.inventory[self.itemIndex].amount -= amount
                    renpy.log(f"removing itemInstance x {amount} from Inventory {item.itemID}")
                    return True
            else:
                return False

        def get_filtered_items(self, key = -1):
            self.sort_inventory()
            itemList = []
            for invItem in self.inventory:
                if get_item_by_id(invItem.itemID).category == key or key == ALL:
                    itemList.append(invItem)
            return itemList

        def add_money(self, amount, popup = False, sound = True):
            self.money += amount
            if sound:
                play_sfx("coin_money_1", channel = 9)
            if popup:
                renpy.log("inventory - adding popup?")
                add_popup_money(amount)
            return
        
        def remove_money(self, amount):
            if (self.money >= amount):
                self.money -= amount
                return True
            else:
                return False

        def check_money(self, amount):
            if (self.money >= amount):
                return True
            else:
                return False

        def get_gold(self):
            return self.money // 10000
        def get_silver(self):
            return self.money // 100 % 100
        def get_copper(self):
            return self.money % 100

        def merge_inventory(self, inventory):
            for invItem in inventory.inventory:
                self.add_item(get_item_by_id(invItem.itemID), invItem.amount)
            self.add_money(inventory.money)

        def sort_inventory(self):
            self.inventory.sort(key = lambda invItem: get_item_by_id(invItem.itemID).sortID)

        def print(self):
            renpy.log("Printing Inventory: ")
            for invItem in self.inventory:
                renpy.log(f"{invItem.itemID}: {invItem.amount}")

    #Item Instance - Instance of items in an Inventory
    class InvItem(object):
        def __init__(self, itemID, amount):
            self.itemID = itemID
            self.amount = amount
