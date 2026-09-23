"""
Character registration, persistent state and progression helpers.

Static character definitions are kept separate from save-backed CharacterState
objects. Combat, equipment, skill and flag systems are defined elsewhere in the
project.
"""

default char_states = {}

init python:
    # Runtime lookup of registered character wrappers.
    ALLCHARS = {}

    # Stable order used by character selection UI.
    MAINCHAR_ORDER = [
        "zero",
        "nova",
        "yuki",
        "alita",
        "solaria",
        "ceecee",
        "anai",
    ]
    MAINCHARS = []

    def register_char(char):
        ALLCHARS[char.cid] = char

    def rebuild_mainchars():
        MAINCHARS.clear()
        for cid in MAINCHAR_ORDER:
            char = ALLCHARS.get(cid)
            if char and char.unlocked:
                MAINCHARS.append(char.cid)

    def get_char_by_id(cid):
        return ALLCHARS.get(cid)

    def gc(cid):
        return ALLCHARS.get(cid)

    # Rebuild wrappers after startup/load without replacing saved CharacterState data.
    def reload_chars():
        global selChar, zero, nova, yuki, alita, solaria, ceecee, anai, ella, nessa, aria, ezra, cyrus, lucan, solsticeridge
        ALLCHARS.clear()

        # Main cast
        zero = Chara("zero")
        nova = Chara("nova")
        yuki = Chara("yuki")
        alita = Chara("alita")
        solaria = Chara("solaria")
        ceecee = Chara("ceecee")
        anai = Chara("anai")

        # Side characters
        ella = Chara("ella")
        nessa = Chara("nessa")
        aria = Chara("aria")
        ezra = Chara("ezra")
        cyrus = Chara("cyrus")
        lucan = Chara("lucan")

        # Location proxy used by the event system.
        solsticeridge = Chara("solsticeridge")

        for cid in ALLCHARS:
            gc(cid).reapply_skills()

        if selChar is None:
            selChar = zero
        selChar = gc(selChar.cid)
        rebuild_mainchars()

    def get_next_mainchar(current=None):
        if current is None:
            current = selChar.cid
        if not MAINCHARS or current not in MAINCHARS:
            return None
        idx = MAINCHARS.index(current)

        return MAINCHARS[(idx + 1) % len(MAINCHARS)] 

    def get_prev_mainchar(current=None):
        if current is None:
            current = selChar.cid
        if not MAINCHARS or current not in MAINCHARS:
            return None
        idx = MAINCHARS.index(current)
        return MAINCHARS[(idx - 1) % len(MAINCHARS)]

    class CharacterDef:
        def __init__(self, cid, name, lastname, color, height, species, type):
            self.cid = cid
            self.name = name
            self.lastname = lastname
            self.color = color
            self.height = height
            self.species = species
            self.type = type

    class CharacterState:
        __version__ = 1

        def __init__(self, cid, unlocked, combat_unlocked, descr, age, charclassID, level, wpnCategory, posCombat, weaponID, clothesID, accID, loot = None):
            self.cid = cid
            self.unlocked = unlocked
            self.combat_unlocked = combat_unlocked
            self.descr = descr

            # Narrative progression
            self.age = age
            self.affection = 0
            self.clevel = 0
            self.counters = {}

            # RPG progression
            self.charclassID = charclassID
            self.level = level
            self.exp = 0
            self.totalexp = 0
            self.wpnCategory = wpnCategory
            self.posCombat = posCombat
            self.baseMaxStats = 0
            self.skillpoints = 0
            self.unlockedSkillnodes = set()
            self.unlockedOther = set()
            self.permaStatIncreases = Stats()
            self.skillStatIncreases = Stats()

            # Equipment
            self.weapons = [weaponID, "wpnnone"]
            self.clothes = clothesID
            self.accs = [accID, "accnone", "accnone"]
            self.loot = loot

            # Abilities
            self.damageAbilities = []
            self.supportAbilities = []
            self.controlAbilities = []
            self.passiveAbilities = []
            self.specialAbilities = []
            self.owAbilities = []

    def get_cstate(cid):
        if cid not in char_states:
            cstate = CharacterState(
                cid=cid,
                unlocked=False,
                combat_unlocked=False,
                descr="",
                age=0,
                charclassID="default",
                level=1,
                wpnCategory=[],
                posCombat=None,
                weaponID="wpnnone",
                clothesID="clothesnone",
                accID="accnone",
            )
            char_states[cid] = cstate
        return char_states[cid]

    # Hook for future save-state migrations.
    def migrate_character(cstate):
        if not hasattr(cstate, "__version__"):
            cstate.__version__ = 1

    def update_skills():
        for cid in ALLCHARS:
            gc(cid).reapply_skills()

    def update_stats():
        for cid in ALLCHARS:
            gc(cid).update_stats()

    def update_skills_and_stats():
        update_skills()
        update_stats()


    class Chara:
        def __init__(self, cid):
            self.state = get_cstate(cid)
            self.cid = cid
            register_char(self)

        def reapply_skills(self):
            self.state.skillStatIncreases.reset()

            # Rebuild derived skill data from the persistent set of unlocked nodes.

            self.state.damageAbilities = []
            self.state.supportAbilities = []
            self.state.controlAbilities = []
            self.state.passiveAbilities = []
            self.state.specialAbilities = []
            self.state.owAbilities = []

            for nodeID in self.state.unlockedSkillnodes:
                self.apply_skillnode(nodeID)

        def apply_skillnode(self, nodeID):
            node = SKILLNODES.get(nodeID)
            if not node:
                return

            skilltype, value = node.skill.split(":", 1)

            if skilltype == "ability":
                self.set_abilities(value)
                return

        def unlock_skillnode(self, nodeID):
            if SKILLNODES.get(nodeID) is not None:
                self.state.unlockedSkillnodes.add(nodeID)
                self.apply_skillnode(nodeID)
                self.state.skillpoints -= SKILLNODES[nodeID].cost

        def check_skillnode(self, nodeID):
            return nodeID in self.state.unlockedSkillnodes

        def can_unlock_skillnode(self, nodeID):
            node = SKILLNODES.get(nodeID)
            if not node:
                return False
            if self.state.skillpoints < node.cost:
                return False
            for parents in node.parents:
                if parents.nodeID not in self.state.unlockedSkillnodes:
                    return False
            return True

        def add_skillpoints(self, amount=1):
            self.state.skillpoints += amount
       
        # Static character data
        @property
        def name(self):
            if self.cid == "zero":
                return mcname
            return CHAR_DEFS[self.cid].name

        @property
        def lastname(self):
            return CHAR_DEFS[self.cid].lastname

        @property
        def color(self):
            return CHAR_DEFS[self.cid].color

        @property
        def height(self):
            return CHAR_DEFS[self.cid].height

        @property
        def species(self):
            return CHAR_DEFS[self.cid].species

        @property
        def type(self):
            return CHAR_DEFS[self.cid].type

        # Persistent character data
        @property
        def inspect(self):
            return CHAR_DEFS[self.cid].name + " \n" + self.state.descr

        @property
        def unlocked(self):
            return self.state.unlocked

        @property
        def combat_unlocked(self):
            return self.state.combat_unlocked

        @property
        def descr(self):
            return self.state.descr

        @property
        def age(self):
            return self.state.age

        
        @property
        def get_flags(self):
            return flags.char.get(self.cid)

        def has_flag(self, flag):
            return flags.char.has(self.cid, flag)
        
        def set_flag(self, flag):
            flags.char.set(self.cid, flag)

        def clear_flag(self, flag):
            flags.char.remove(self.cid, flag)
        
        def inc_counter(self, key, amount=1):
            self.state.counters[key] = self.state.counters.get(key, 0) + amount

        def get_counter(self, key):
            return self.state.counters.get(key, 0)


        def equip_item(self, item, identifier, slot):
            if isinstance(item, str):
                item = get_item_by_id(item)
            if identifier == WPN or identifier == SHIELD:
                return self.equip_hands(item, slot)
            elif identifier == CLOTHES:
                return self.equip_clothes(item)
            elif identifier == ACC:
                return self.equip_acc(item, slot)


        def unequip_item(self, identifier, slot):
            if identifier == WPN:
                if self.state.weapons[slot] != "wpnnone":
                    mainInventory.add_item(self.state.weapons[slot])
                    self.state.weapons[slot] = "wpnnone"
            elif identifier == CLOTHES:
                if self.state.clothes != "clothesnone":
                    mainInventory.add_item(self.get_clothes)
                    self.state.clothes = "clothesnone"
            elif identifier == ACC:
                if self.state.accs[slot] != "accnone":
                    mainInventory.add_item(self.state.accs[slot])
                    self.state.accs[slot] = "accnone"

        def has_equipped_amount(self, item):
            result = 0
            itemID = item
            if not isinstance(item, str):
                itemID = item.itemID

            if self.state.clothes == itemID:
                result += 1
            if self.state.weapons[0] == itemID:
                result += 1
            if self.state.weapons[1] == itemID:
                result += 1
            if self.state.accs[0] == itemID:
                result += 1
            if self.state.accs[1] == itemID:
                result += 1
            if self.state.accs[2] == itemID:
                result += 1

            return result
                

        def equip_hands(self, item, slot = 0):
            if(isinstance(item, Weapon) and check_wpncategory(self.state.wpnCategory, item)):
                if item.wpnCategory >= 10:  # Two-handed weapon
                    self.unequip_item(WPN, 0)
                    self.unequip_item(WPN, 1)
                    self.state.weapons[0] = item.itemID
                else:
                    if self.get_weapon_slot1.wpnCategory >= 10:
                        self.unequip_item(WPN, 0)
                    self.unequip_item(WPN, slot)
                    self.state.weapons[slot] = item.itemID
                mainInventory.remove_item(item)
                return True
            else:
                return False


        def equip_clothes(self, item):
            if isinstance(item, Cloth):
                self.unequip_item(CLOTHES, 0)
                self.state.clothes = item.itemID
                mainInventory.remove_item(item)
                return True
            else:
                return False

        def equip_acc(self, item, slot):
            if isinstance(item, Accessoire):
                self.unequip_item(ACC, slot)
                self.state.accs[slot] = item.itemID
                mainInventory.remove_item(item)
                return True
            else:
                return False

        def update_stats(self):
            self.state.baseMaxStats = get_charclass_by_id(self.state.charclassID).get_stats(self.state.level)

        # Combat progression
        def gain_exp(self, exp):
            self.state.totalexp += exp
            self.state.exp += exp
            while self.state.exp >= 90 + self.state.level * self.state.level * 10:
                self.state.exp -= (90 + self.state.level * self.state.level * 10)
                self.level_up()
                

        def level_up(self):
            self.add_skillpoints(1)
            self.state.level += 1
            self.update_stats()


        def set_level(self, level):
            self.state.level = level
            self.update_stats()
            add_popup_levelup(self.cid, self.state.level, "Adventurer")


        # Relationship progression
        def gain_affection(self, points):
            add_popup_affection(self.cid)
            self.state.affection += points
            if self.state.affection >= 5 + self.state.clevel:
                self.state.affection = 5 + self.state.clevel

        def can_clevel_up(self):
            if self.state.affection >= 5 + self.state.clevel:
                return True
            return False

        def clevel_up(self):
            self.state.clevel += 1
            self.state.affection = 0
            add_popup_levelup(self.cid, self.state.clevel, "Character")


        def set_clevel(self, level):
            self.state.clevel = level
            self.state.affection = 0

        @property
        def get_exp(self):
            return self.state.exp

        @property
        def get_totalexp(self):
            return self.state.totalexp

        @property
        def get_reqexp(self):
            return 90 + self.state.level * self.state.level * 10

        @property
        def get_level(self):
            return self.state.level

        @property
        def get_affection(self):
            return self.state.affection

        @property
        def get_reqaffection(self):
            return 5 + self.state.clevel

        @property
        def get_clevel(self):
            return self.state.clevel

        @property
        def get_stats(self):
            return self.state.baseMaxStats

        @property
        def get_bonusstats(self):
            return self.state.skillStatIncreases

        @property
        def get_skillpoints(self):
            return self.state.skillpoints

        @property
        def get_skilllist(self):
            return self.state.unlockedSkillnodes

        @property
        def get_weapon_slot1(self):
            return get_item_by_id(self.state.weapons[0])

        @property
        def get_weapon_slot2(self):
            return get_item_by_id(self.state.weapons[1])

        @property
        def get_clothes(self):
            return get_item_by_id(self.state.clothes)

        @property
        def get_acc_slot1(self):
            return get_item_by_id(self.state.accs[0])

        @property
        def get_acc_slot2(self):
            return get_item_by_id(self.state.accs[1])

        @property
        def get_acc_slot3(self):
            return get_item_by_id(self.state.accs[2])

        @property
        def get_dmg_type(self):
            return self.get_weapon_slot1.dmgType


        @property 
        def get_maxhp(self):
            return self.get_stats.hp + self.get_bonusstats.hp + self.get_weapon_slot1.hp + self.get_weapon_slot2.hp + self.get_clothes.hp + self.get_acc_slot1.hp + self.get_acc_slot2.hp + self.get_acc_slot3.hp

        @property
        def get_maxmp(self):
            return self.get_stats.mp + self.get_bonusstats.mp + self.get_weapon_slot1.mp + self.get_weapon_slot2.mp + self.get_clothes.mp + self.get_acc_slot1.mp + self.get_acc_slot2.mp + self.get_acc_slot3.mp

        @property
        def get_maxstamina(self):
            return self.get_stats.stamina + self.get_bonusstats.stamina + self.get_weapon_slot1.stamina + self.get_weapon_slot2.stamina + self.get_clothes.stamina + self.get_acc_slot1.stamina + self.get_acc_slot2.stamina + self.get_acc_slot3.stamina

        @property
        def get_speed(self):
            return self.get_stats.speed + self.get_bonusstats.speed + self.get_weapon_slot1.speed + self.get_weapon_slot2.speed + self.get_clothes.speed + self.get_acc_slot1.speed + self.get_acc_slot2.speed + self.get_acc_slot3.speed

        @property
        def get_pos(self):
            return self.state.posCombat

        @property
        def get_dexterity(self):
            return self.get_stats.dexterity + self.get_bonusstats.dexterity + self.get_weapon_slot1.dexterity + self.get_weapon_slot2.dexterity + self.get_clothes.dexterity + self.get_acc_slot1.dexterity + self.get_acc_slot2.dexterity + self.get_acc_slot3.dexterity

        @property
        def get_luck(self):
            return self.get_stats.luck + self.get_bonusstats.luck + self.get_weapon_slot1.luck + self.get_weapon_slot2.luck + self.get_clothes.luck + self.get_acc_slot1.luck + self.get_acc_slot2.luck + self.get_acc_slot3.luck

        @property
        def get_strength(self):
            return self.get_stats.strength + self.get_bonusstats.strength + self.get_weapon_slot1.strength + self.get_weapon_slot2.strength + self.get_clothes.strength + self.get_acc_slot1.strength + self.get_acc_slot2.strength + self.get_acc_slot3.strength

        @property
        def get_melee(self):
            return self.get_stats.strength + self.get_bonusstats.strength + self.get_weapon_slot1.melee + self.get_weapon_slot2.melee + self.get_clothes.melee + self.get_acc_slot1.melee + self.get_acc_slot2.melee + self.get_acc_slot3.melee

        @property
        def get_ranged(self):
            return self.get_stats.strength + self.get_bonusstats.strength + self.get_weapon_slot1.ranged + self.get_weapon_slot2.ranged +self.get_clothes.ranged + self.get_acc_slot1.ranged + self.get_acc_slot2.ranged + self.get_acc_slot3.ranged

        @property 
        def get_magic_pow(self):
            return self.get_stats.magicPow + self.get_bonusstats.magicPow + self.get_weapon_slot1.magicPow + self.get_weapon_slot2.magicPow + self.get_clothes.magicPow + self.get_acc_slot1.magicPow + self.get_acc_slot2.magicPow + self.get_acc_slot3.magicPow

        @property
        def get_constitution(self):
            return self.get_stats.constitution + self.get_bonusstats.constitution + self.get_weapon_slot1.constitution + self.get_weapon_slot2.constitution + self.get_clothes.constitution + self.get_acc_slot1.constitution + self.get_acc_slot2.constitution + self.get_acc_slot3.constitution

        @property
        def get_resistance(self):
            return self.get_stats.resistance + self.get_bonusstats.resistance + self.get_weapon_slot1.resistance + self.get_weapon_slot2.resistance + self.get_clothes.resistance + self.get_acc_slot1.resistance + self.get_acc_slot2.resistance + self.get_acc_slot3.resistance

        @property
        def get_stats_average(self):
            return (self.get_strength + self.get_magic_pow + self.get_constitution + self.get_resistance + self.get_speed + self.get_dexterity + self.get_luck) / 7.0

        def get_power(self, attType):
            damage_calcs = {
                MELEE: self.get_melee,
                RANGED: self.get_ranged,
                MAGIC: self.get_magic_pow
            }
            return damage_calcs.get(attType, 0)


        def get_defense(self, attType):
            resistance_calcs = {
                MELEE: self.get_constitution,
                RANGED: self.get_constitution,
                MAGIC: self.get_resistance
            }
            return resistance_calcs.get(attType, 0)

        def get_charaffinities(self):
            return get_charclass_by_id(self.state.charclassID).get_affinities()
        
        def get_affinities(self):
            tempAffinities = Affinities()
            tempAffinities.add_affinities(self.get_charaffinities())
            tempAffinities.add_affinities(self.get_weapon_slot1.affinities)
            tempAffinities.add_affinities(self.get_weapon_slot2.affinities)
            tempAffinities.add_affinities(self.get_clothes.affinities)
            tempAffinities.add_affinities(self.get_acc_slot1.affinities)
            tempAffinities.add_affinities(self.get_acc_slot2.affinities)
            tempAffinities.add_affinities(self.get_acc_slot3.affinities)
            return tempAffinities
 
        def get_abilities(self, identifier):
            if identifier == ALL:
                id_lists = (
                    self.state.damageAbilities,
                    self.state.supportAbilities,
                    self.state.controlAbilities,
                    self.state.passiveAbilities,
                    self.state.specialAbilities,
                    self.state.owAbilities,
                )
                return [get_ability_by_id(aid) for lst in id_lists for aid in lst]
            
            mapping = {
                OFF: self.state.damageAbilities,
                SUP: self.state.supportAbilities,
                CTR: self.state.controlAbilities,
                PSV: self.state.passiveAbilities,
                SPEC: self.state.specialAbilities,
                OW: self.state.owAbilities,
            }

            ids = mapping.get(identifier, [])
            return [get_ability_by_id(aid) for aid in ids]

        def set_abilities(self, abilityIDs):
            if not isinstance(abilityIDs, (list, tuple, set)):
                abilityIDs = [abilityIDs] 

            for abilityID in abilityIDs:
                ability = get_ability_by_id(abilityID)
                if isinstance(ability, DamageAbility):
                    self.state.damageAbilities.append(abilityID)
                elif isinstance(ability, SupportAbility):
                    self.state.supportAbilities.append(abilityID)
                elif isinstance(ability, ControlAbility):
                    self.state.controlAbilities.append(abilityID)
                elif isinstance(ability, PassiveAbility):
                    self.state.passiveAbilities.append(abilityID)
                elif isinstance(ability, SpecialAbility):
                    self.state.specialAbilities.append(abilityID)
                elif isinstance(ability, OverworldAbility):
                    self.state.owAbilities.append(abilityID)

        def set_description(self, descr):
            self.state.descr = descr
        
        def set_age(self, age):
            self.state.age = age

        def set_unlocked(self, value):
            self.state.unlocked = value
            rebuild_mainchars()

        def set_combat_unlocked(self, value):
            self.state.combat_unlocked = value

        def set_class(self, charclassID):
            self.state.charclassID = charclassID

        def set_affinities(self, affinities):
            # Affinities are defined by the active character class.
            return

        def set_weapon_slot1(self, weapon):
            self.state.weapons[0] = weapon.itemID
        
        def set_weapon_slot2(self, weapon):
            self.state.weapons[1] = weapon.itemID
        
        def set_clothes(self, clothes):
            self.state.clothes = clothes.itemID
        
        def set_acc_slot1(self, acc):
            self.state.accs[0] = acc.itemID
        
        def set_acc_slot2(self, acc):
            self.state.accs[1] = acc.itemID
        
        def set_acc_slot3(self, acc):
            self.state.accs[2] = acc.itemID
        
        def set_pos_combat(self, pos):
            self.state.posCombat = pos

        def set_wpn_category(self, categories):
            self.state.wpnCategory = categories
