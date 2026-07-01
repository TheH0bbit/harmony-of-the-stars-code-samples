"""
Combat System
=============

This module implements the core turn-based combat framework used in
Harmony of the Stars.

Responsibilities
----------------
• Combat initialization and cleanup
• Turn order calculation
• Character and enemy management
• Target selection
• Damage and status effect processing
• Victory / defeat handling
• Loot and combat rewards
• Combat UI state

Architecture
------------
The CombatInstance class acts as the central controller for an active battle.
Rather than storing gameplay data directly on characters, combat-specific
information is encapsulated in CharCombatComponent and FoeCombatComponent,
allowing combat state to remain independent from the underlying character data.

The combat system interacts with several other gameplay systems,
including characters, inventory, abilities, quests, items, dungeon
progression and save management.

Notes
-----
This file originates from a larger project. Some referenced classes and
systems are intentionally omitted from this repository because only the
gameplay systems relevant for code review are included.
"""

init python:
    # Global reference to the currently active combat instance.
    combat = None

    #Positions Helper Array, Temporary Solution
    positionsV = [800, 875, 725, 950, 650]
    positionsH = [450, 325, 575, 200, 700] # Invert for foes

    combat_popups = []

    #CombatInstance Class - Holds near all information regarding the Combatstate, and initializes it, still needs more cleanup!
    class CombatInstance:
        def __init__(self, heroes, foes, cCallback = None):
            #This is just a MINOR refactored version, more to come. I will try to explain what everything is for future me
            #Issues to keep in mind, that will have to be improved in future updates:
            #The number of heroes and foes in the respective arrays heroes, foes, and units HAS to remain the same, otherwise the whole structure as of now breaks down. So do NOT remove fainted foes/heroes per combat.

            #Lists for all Hero and  Foe CharCombatComponents and a COMBINED list with references to the original two, NOT A SEPARATE LIST!
            self.heroes = []
            self.foes = []

            for hero in heroes:
                self.heroes.append(CharCombatComponent(hero))
            for foeID, level in foes:
                self.foes.append(FoeCombatComponent(foeID, level))

            self.units = MergedReferencedList(self.heroes, self.foes)

            self.numHeroes = len(heroes)
            self.numFoes = len(foes)

            #Speedvalues are the underlying characters BASE speeds
            #speedTable holds the values of when which character moves next. Initialized with 0.0, then increased once respective char has finished his Turn
            self.speedValues = []
            self.speedTable = []

            #Turnbuffer holds the decided order of charturns
            #turnbufferprediction holds the predicted order of charturns, for the interface mostly
            self.turnBuffer = []
            self.turnBufferPrediction = []
            self.initialTurns = True


            #Holds the UI SpritePositions
            self.heroPositions = []
            self.foePositions = []
            self.positions = []

            #Holds targeting information for AOE attacks
            self.aoeTargets = []

            #Holds Char sprites
            self.charSprites = []
            self.spriteEffects = []

            #Action State information
            self.currCharIndex = 0
            self.charInstance = None
            self.chosenAbilityID = None
            self.meleeHeroesRemain = True
            self.meleeFoesRemain = True
            self.combatState = ONGOING
            self.cCallback = cCallback
            self.first = True

            #Special Combat Rules
            self.ko = True
            self.death = True
            self.battletimer = 10000000

            #self.taunter = NONE

            #Message System Variables
            self.combat_text = "Initial"
            self.combat_text_lock = False
            self.combatMessages = []

            #load in heroes and foes, First melee then ranged for display position!
            for i, hero in enumerate(self.heroes):
                self.speedValues.append(hero.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{hero.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)
                #renpy.log(f"loading in heroes animation:{i} idle 0.3 : gui/sprites/{hero.cid}".lower() )


            for i, foe in enumerate(self.foes):
                self.speedValues.append(foe.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{foe.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)
                #renpy.log(f"loading in foes animation:{i} idle 0.3 : gui/sprites/{foe.cid}".lower() )

            #DEBUG
            #testBuff = Buff(BUFF, "Test", "TestBuff", 100, speed = 0, strength = 100, dexterity = 100, magicPow = -5)
            #statusEffects[0].append([testBuff, 0])

            #sort indicis in order from highest to lowest value, index 0 (Zero) always goes first, no matter what
            sortedSpeedIndicisHelper = list(enumerate(self.speedValues))
            main_char = sortedSpeedIndicisHelper.pop(0)
            sortedSpeedIndicisHelper.sort(key=lambda x : x[1], reverse=True)
            self.turnBuffer = [0] + [index for index, value in sortedSpeedIndicisHelper]
            self.turnBufferPrediction = list(self.turnBuffer)

            if debug:
                renpy.log(f"Initialized Combatstate:")
                for unit in self.units:
                    renpy.log(f"Unit: {unit.char.name}")
                    renpy.log(f"     Level: {unit.char.get_level}")
                    renpy.log(f"     {unit.char.get_stats.print()}")
                renpy.log(f"turnbuffer: {self.turnBuffer}")
                renpy.log(f"turnbufferprediction: {self.turnBufferPrediction}")
            return

        #instead of recreating a new combat state, sets up next phase using the previous combat state
        def init_next_phase(self, foes):
            self.foes = []

            for hero in self.heroes:
                hero.revive()

            for foeID, level in foes:
                self.foes.append(FoeCombatComponent(foeID, level))

            self.units = MergedReferencedList(self.heroes, self.foes)

            self.numHeroes = len(self.heroes)
            self.numFoes = len(foes)

            self.speedValues = []
            self.speedTable = []

            self.turnBuffer = []
            self.turnBufferPrediction = []
            self.initialTurns = True

            self.heroPositions = []
            self.foePositions = []
            self.positions = []

            calculate_positions()

            self.aoeTargets = []

            self.charSprites = []
            self.spriteEffects = []

            self.currCharIndex = 0
            self.charInstance = None
            self.chosenAbilityID = None

            check_remain_melee_heroes()
            check_remain_melee_foes()

            self.combatState = ONGOING
            self.cCallback = self.cCallback
            self.first = True

            #Special Combat Rules
            self.ko = True
            self.death = True
            self.battletimer = 10000000

            #self.taunter = NONE

            #Message System Variables
            self.combat_text = ""
            self.combat_text_lock = False
            self.combatMessages = []

            #load in heroes and foes, First melee then ranged for display position!
            for i, hero in enumerate(self.heroes):
                self.speedValues.append(hero.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{hero.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)
                #renpy.log(f"loading in heroes animation:{i} idle 0.3 : gui/sprites/{hero.cid}".lower() )


            for i, foe in enumerate(self.foes):
                self.speedValues.append(foe.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{foe.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)
                #renpy.log(f"loading in foes animation:{i} idle 0.3 : gui/sprites/{foe.cid}".lower() )

            #DEBUG
            #testBuff = Buff(BUFF, "Test", "TestBuff", 100, speed = 0, strength = 100, dexterity = 100, magicPow = -5)
            #statusEffects[0].append([testBuff, 0])

            #sort indicis in order from highest to lowest value, index 0 (Zero) always goes first, no matter what... for now
            sortedSpeedIndicisHelper = list(enumerate(self.speedValues))
            main_char = sortedSpeedIndicisHelper.pop(0)
            sortedSpeedIndicisHelper.sort(key=lambda x : x[1], reverse=True)
            self.turnBuffer = [0] + [index for index, value in sortedSpeedIndicisHelper]
            self.turnBufferPrediction = list(self.turnBuffer)

            if debug:
                renpy.log(f"Initialized Combatstate:")
                for unit in self.units:
                    renpy.log(f"Unit: {unit.char.name}")
                    renpy.log(f"     Level: {unit.char.get_level}")
                    renpy.log(f"     {unit.char.get_stats.print()}")
                renpy.log(f"turnbuffer: {self.turnBuffer}")
                renpy.log(f"turnbufferprediction: {self.turnBufferPrediction}")
            return


    class CharCombatComponent:
        def __init__(self, char):
            self.char = char
            self.cid = char.cid

            #initialize runtime combat state
            self.statusEffects = []
            self.passiveEffects = []

            #load in existing StatusEffects/PassiveEffects. NOTE: These here are only the TEMPORARY Effects, from the current Dungeon/Combatrun. All other buffs/debuffs etc. are part of the character class.
            #TODO: MAKE SURE statChanges are properly added where necessary!
            #TODO: Either find use for new implementation of passiveEffects or eventually delete it!

            self.basicattackID = "basicmelee"
            if basicRanged in self.char.get_abilities(OFF):
                self.basicattackID = "basicranged"

            #Parry: Melee Block Chance, Riposte: Melee Counterattack Chance, Reflect: All RANGES Reflect Attack Chance
            self.parry = "placeholdercounter"
            self.riposte = "placeholdercounter"
            self.reflect = "placeholdercounter"

            for passiveAbility in char.get_abilities(PSV):
                if passiveAbility.category == COUNTER:
                    for statusEffect in passiveAbility.statusEffects:
                        if statusEffect.category == PARRY and statusEffect.chance > self.parry.chance:
                            self.parry = statusEffect.statusID
                        elif statusEffect.category == RIPOSTE and statusEffect.chance > self.riposte.chance:
                            self.riposte = statusEffect.statusID
                        elif statusEffect.category == REFLECT and statusEffect.chance > self.reflect.chance:
                            self.reflect = statusEffect.statusID
                        else:
                            #TODO: Apply other status effects from passive abilities, also in revive!
                            pass
                        continue
                else:
                    self.passiveEffects.append(passiveAbility.abilityID)

            self.taunter = None
            self.alive = True

            self.statChanges = Stats()
            for statusEffect in self.statusEffects:
                _statusEffect = get_statuseffect_by_id(statusEffect[0])
                if statusEffect[1] < _statusEffect.duration and _statusEffect.statusType == BUFF:
                    self.statChanges.add_stats(_statusEffect.stats)

            self.hp = self.get_real_max_hp()
            self.mp = self.get_real_max_mp()
            self.stamina = self.get_real_max_stamina()

        def get_real_max_hp(self):
            return self.char.get_maxhp + self.statChanges.hp

        def get_real_max_mp(self):
            return self.char.get_maxmp + self.statChanges.mp
    
        def get_real_max_stamina(self):
            return self.char.get_maxstamina + self.statChanges.stamina

        def revive(self, statfactor = 1/3):
            self.statChanges = Stats()
            for statusEffect in self.statusEffects:
                _statusEffect = get_statuseffect_by_id(statusEffect[0])
                if statusEffect[1] < _statusEffect.duration and _statusEffect.statusType == BUFF:
                    self.statChanges.add_stats(_statusEffect.stats)
            self.taunter = None
            self.alive = True
            self.hp = max(self.hp, int(self.get_real_max_hp()*statfactor))
            self.mp = max(self.mp, int(self.get_real_max_hp()*statfactor))
            self.stamina = max(self.stamina, int(self.get_real_max_stamina()*statfactor))


    class FoeCombatComponent:
        def __init__(self, cid, level):
            self.cid = cid

            self.statusEffects = []
            self.passiveEffects = []

            #initialize runtime combat state
            foedata = get_foe_by_id(cid)
            foeclass = get_charclass_by_id(cid)

            #Facade view for the foe.char object, mimics relevant functions from character objects
            self.char = FoeCharFacade(
                name = foedata.name,
                descr = foedata.descr,
                level = level,
                baseStats = foeclass.get_stats(level),
                affinities = foeclass.get_affinities(),
                position = foedata.posCombat,
                dmgType = foedata.dmgType,
                weapon = foedata.weaponID,
                clothes = foedata.clothesID,
                acc = foedata.accID,
            )

            self.char.set_abilities(foedata.abilityIDs)
            self.basicattackID = "basicmelee"
            if basicRanged in self.char.get_abilities(OFF):
                self.basicattackID = "basicranged"

            #Parry: Melee Block Chance, Riposte: Melee Counterattack Chance, Reflect: All RANGES Reflect Attack Chance
            self.parry = "placeholdercounter"
            self.riposte = "placeholdercounter"
            self.reflect = "placeholdercounter"

            for passiveAbility in self.char.get_abilities(PSV):
                if passiveAbility.category == COUNTER:
                    for statusEffect in passiveAbility.statusEffects:
                        if statusEffect.category == PARRY and statusEffect.chance > self.parry.chance:
                            self.parry = statusEffect.statusID
                        elif statusEffect.category == RIPOSTE and statusEffect.chance > self.riposte.chance:
                            self.riposte = statusEffect.statusID
                        elif statusEffect.category == REFLECT and statusEffect.chance > self.reflect.chance:
                            self.reflect = statusEffect.statusID
                        else:
                            #TODO: Apply other status effects from passive abilities
                            pass
                        continue
                else:
                    self.passiveEffects.append(passiveAbility.abilityID)

            self.statChanges = Stats()
            for statusEffect in self.statusEffects:
                _statusEffect = get_statuseffect_by_id(statusEffect[0])
                if statusEffect[1] < _statusEffect.duration and _statusEffect.statusType == BUFF:
                    self.statChanges.add_stats(_statusEffect.stats)
                        
            self.hp = self.get_real_max_hp()
            self.mp = self.get_real_max_mp()
            self.stamina = self.get_real_max_stamina()

            self.taunter = None
            self.alive = True

        def get_real_max_hp(self):
            return self.char.get_maxhp + self.statChanges.hp

        def get_real_max_mp(self):
            return self.char.get_maxmp + self.statChanges.mp
    
        def get_real_max_stamina(self):
            return self.char.get_maxstamina + self.statChanges.stamina

    
    #Facade of Char functions/values for Foe object
    class FoeCharFacade:
        def __init__(self, name, descr, level, baseStats, affinities, position, dmgType, weapon, clothes, acc):
            self.name = name
            self.descr = descr
            self.get_stats = baseStats
            self.get_level = level
            self.affinities = affinities

            self.get_pos = position
            self.get_dmg_type = dmgType

            self.weapon = weapon
            self.clothes = clothes
            self.acc = acc

            self.damageAbilities = []
            self.supportAbilities = []
            self.controlAbilities = []
            self.passiveAbilities = []
            self.specialAbilities = []
            self.owAbilities = []


        @property
        def get_weapon_slot1(self):
            return get_item_by_id(self.weapon)

        @property
        def get_clothes(self):
            return get_item_by_id(self.clothes)

        @property
        def get_acc_slot1(self):
            return get_item_by_id(self.acc)

        @property 
        def get_maxhp(self):
            return self.get_stats.hp + self.get_weapon_slot1.hp + self.get_clothes.hp + self.get_acc_slot1.hp

        @property
        def get_maxmp(self):
            return self.get_stats.mp + self.get_weapon_slot1.mp + self.get_clothes.mp + self.get_acc_slot1.mp

        @property
        def get_maxstamina(self):
            return self.get_stats.stamina + self.get_weapon_slot1.stamina + self.get_clothes.stamina + self.get_acc_slot1.stamina

        @property
        def get_speed(self):
            return self.get_stats.speed + self.get_weapon_slot1.speed + self.get_clothes.speed + self.get_acc_slot1.speed

        @property
        def get_dexterity(self):
            return self.get_stats.dexterity + self.get_weapon_slot1.dexterity + self.get_clothes.dexterity + self.get_acc_slot1.dexterity

        @property
        def get_luck(self):
            return self.get_stats.luck + self.get_weapon_slot1.luck + self.get_clothes.luck + self.get_acc_slot1.luck

        @property
        def get_strength(self):
            return self.get_stats.strength + self.get_weapon_slot1.strength + self.get_clothes.strength + self.get_acc_slot1.strength

        @property
        def get_melee(self):
            return self.get_stats.strength + self.get_weapon_slot1.melee + self.get_clothes.melee + self.get_acc_slot1.melee

        @property
        def get_ranged(self):
            return self.get_stats.strength + self.get_weapon_slot1.ranged + self.get_clothes.ranged + self.get_acc_slot1.ranged

        @property 
        def get_magic_pow(self):
            return self.get_stats.magicPow + self.get_weapon_slot1.magicPow + self.get_clothes.magicPow + self.get_acc_slot1.magicPow

        @property
        def get_constitution(self):
            return self.get_stats.constitution + self.get_weapon_slot1.constitution + self.get_clothes.constitution + self.get_acc_slot1.constitution

        @property
        def get_resistance(self):
            return self.get_stats.resistance + self.get_weapon_slot1.resistance + self.get_clothes.resistance + self.get_acc_slot1.resistance

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

        def set_abilities(self, abilityIDs):
            if not isinstance(abilityIDs, (list, tuple, set)):
                abilityIDs = [abilityIDs] 

            for abilityID in abilityIDs:
                ability = get_ability_by_id(abilityID)
                if isinstance(ability, DamageAbility):
                    self.damageAbilities.append(abilityID)
                elif isinstance(ability, SupportAbility):
                    self.supportAbilities.append(abilityID)
                elif isinstance(ability, ControlAbility):
                    self.state.controlAbilities.append(abilityID)
                elif isinstance(ability, PassiveAbility):
                    self.passiveAbilities.append(abilityID)
                elif isinstance(ability, SpecialAbility):
                    self.specialAbilities.append(abilityID)
                elif isinstance(ability, OverworldAbility):
                    self.owAbilities.append(abilityID)

 
        def get_abilities(self, identifier):
            if identifier == ALL:
                id_lists = (
                    self.damageAbilities,
                    self.supportAbilities,
                    self.controlAbilities,
                    self.passiveAbilities,
                    self.specialAbilities,
                    self.owAbilities,
                )
                return [get_ability_by_id(aid) for lst in id_lists for aid in lst]
            
            mapping = {
                OFF: self.damageAbilities,
                SUP: self.supportAbilities,
                CTR: self.controlAbilities,
                PSV: self.passiveAbilities,
                SPEC: self.specialAbilities,
                OW: self.owAbilities,
            }

            ids = mapping.get(identifier, [])
            return [get_ability_by_id(aid) for aid in ids]

        def get_affinities(self):
            tempAffinities = Affinities()
            tempAffinities.add_affinities(self.affinities)
            tempAffinities.add_affinities(self.get_weapon_slot1.affinities)
            tempAffinities.add_affinities(self.get_clothes.affinities)
            tempAffinities.add_affinities(self.get_acc_slot1.affinities)
            return tempAffinities


    ################################################ End of Facade #####################################################################


    #Initializes a Combat Encounter.
    def init_combat(heroes, foes, cCallback = None):
        global combat, combat_popups
        combat_popups = []
        combat = CombatInstance(heroes, foes, cCallback)
        calculate_positions()
        return

    def combat_rules(death = False, ko = False, battletimer = 10000000):
        combat.death = death
        combat.ko = ko
        combat.battletimer = battletimer


    ################################################ COMBAT UI SYSTEM FUNCTIONS #########################################################
    def set_combat_text(text):
        if not combat.combat_text_lock:
            combat.combat_text = text

    def set_combat_text_ability(ability, mp_req = False, stamina_req = False, blocked = False):
        if mp_req:
            set_combat_text(f"{ability.name} - {ability.mp} MP - Not enough MP\n{ability.descr}")
            return

        if stamina_req:
            set_combat_text(f"{ability.name} - {ability.stamina} Stamina - Not enough Stamina\n{ability.descr}")
            return

        if blocked:
            set_combat_text("Blocked")
            return
        else:
            info_text = f"{ability.name} - "
            if ability.mp:
                info_text += f"{ability.mp} MP\n{ability.descr}"
            elif ability.stamina:
                info_text += f"{ability.stamina} Stamina\n{ability.descr}"
            else:
                info_text = f"{ability.name}\n{ability.descr}" 
            set_combat_text(info_text)

    def set_combat_text_lock(value):
        combat.combat_text_lock = value

    def set_combat_text_pause(text, pause = -1.0):
        set_combat_text_lock(True)
        if pause == -1.0:
            pause = len(text)/20.0 + 1.0
        combat.combat_text = text
        renpy.pause(pause)
        set_combat_text_lock(False)

    def append_message(msg, duration = -1):
        combat.combatMessages.append((msg, duration))
        renpy.log(f"Appending Message to Buffer {msg}")
    
    def display_combat_messages():
        set_combat_text_lock(True)
        for entry in combat.combatMessages:
            set_combat_text_pause(entry[0], entry[1])
        set_combat_text_lock(False)
        combat.combatMessages = []

    def refresh_screen(screenName):
        renpy.hide_screen(screenName)
        renpy.show_screen(screenName, _layer = "screens")
    
    def close_combat_screens():
        renpy.hide_screen("combat_options_main")
        renpy.hide_screen("combat_options_skills")
        renpy.hide_screen("target_selection_foes")
        renpy.hide_screen("combat_text")
        renpy.hide_screen("testScreen")
        renpy.hide_screen("combat_turnbuffer")

    ################################################ COMBAT HELPER FUNCTIONS #########################################################

    #Calculates the Coordinates where to Position Hero and Foe Sprites
    def calculate_positions():
        #Counters
        meleeHeroes = 0
        rangedHeroes = 0
        for h in combat.heroes:
            if(h.char.get_pos == MELEE):
                meleeHeroes += 1
            else:
                rangedHeroes += 1

        for i in range(meleeHeroes):
            if (meleeHeroes % 2) == 0:
                combat.heroPositions.append((positionsH[i], positionsV[i] - 38))
            else: 
                combat.heroPositions.append((positionsH[i], positionsV[i]))

        for i in range(rangedHeroes):
            if (rangedHeroes % 2) == 0:
                combat.heroPositions.append((positionsH[i]-150, positionsV[i] -38))
            else: 
                combat.heroPositions.append((positionsH[i]-150, positionsV[i]))

        meleeFoes = 0
        rangedFoes = 0
        for f in combat.foes:
            if(f.char.get_pos == MELEE):
                meleeFoes += 1
            else:
                rangedFoes += 1

        for i in range(meleeFoes):
            if (meleeFoes % 2) == 0:
                combat.foePositions.append((1920-positionsH[i], positionsV[i] + 50))
            else: 
                combat.foePositions.append((1920-positionsH[i], positionsV[i]))

        for i in range(rangedFoes):
            if (rangedFoes % 2) == 0:
                combat.foePositions.append((1920-positionsH[i]+150, positionsV[i] + 50 - 65))
            else: 
                combat.foePositions.append((1920-positionsH[i]+150, positionsV[i] - 65))

        combat.positions = MergedReferencedList(combat.heroPositions, combat.foePositions)

        return

    def get_aoe_targets_foes(center, falloff = True):
        ability = get_ability_by_id(combat.chosenAbilityID)
        combat.aoeTargets = []
        centerXY = combat.foePositions[center]
        pixelRadius = ability.radius * AVGDISTANCE
        #MeleeRow
        for i, pos in enumerate(combat.foePositions):
            pixelDistance = distance(centerXY, pos)
            if pixelDistance <= pixelRadius:
                if falloff: 
                    combat.aoeTargets.append((i + combat.numHeroes, 1.0 - (pixelDistance/pixelRadius)))
                else:
                    combat.aoeTargets.append((i + combat.numHeroes, 1.0))
                #renpy.log(f"appending target to combat.aoeTargets: {i+combat.numHeroes}")
        renpy.show_screen("show_aoe_targets", _layer = "screens")

    def get_aoe_targets_heroes(center, falloff = True):
        ability = get_ability_by_id(combat.chosenAbilityID)
        combat.aoeTargets = []
        centerXY = combat.heroPositions[center]
        pixelRadius = ability.radius * AVGDISTANCE
        #MeleeRow
        for i, pos in enumerate(combat.heroPositions):
            pixelDistance = distance(centerXY, pos)
            if pixelDistance <= pixelRadius:
                if falloff: 
                    combat.aoeTargets.append((i, 1.0 - (pixelDistance/pixelRadius)))
                else:
                    combat.aoeTargets.append((i, 1.0))
                #renpy.log(f"appending target to combat.aoeTargets: {i+combat.numHeroes}")
        return combat.aoeTargets

    def check_remain_melee_heroes():
        for i, hero in enumerate(combat.heroes):
            if hero.char.get_pos == MELEE and hero.alive:
                combat.meleeHeroesRemain = True
                return
        combat.meleeHeroesRemain = False

    def check_remain_melee_foes():
        for i, foe in enumerate(combat.foes):
            if foe.char.get_pos == MELEE and foe.alive:
                combat.meleeFoesRemain = True
                return
        combat.meleeFoesRemain = False
    
    #Animation Control
    def load_char_combat_anim(pos, state, duration = 0.3):
        #renpy.log(f"loading in animation:{pos} {state} {duration}: gui/sprites/{combat.units[pos].cid}/{state}".lower() )
        combat.charSprites[pos] = Animation(f"gui/sprites/{combat.units[pos].cid}/{state}".lower(), True, duration)

    def add_popup_combat(x, y, duration=0.8, style="textbase", transform = None, text = None, icon = None):
        if not transform:
            transform = popupTransformBase
        combat_popups.append({
            "id": renpy.random.random(),
            "posx": x,
            "posy": y,
            "duration": duration,
            "style": style,
            "start": time.time(),
            "transform": transform,
            "text": text,
            "icon": icon,
        })

    def add_sprite_effect(target, duration = 1.0, transform = None):
        combat.spriteEffects[target] = {
            "id": renpy.random.random(),
            "duration": duration,
            "transform": transform,
            "start": time.time(),
        }

############################################################# END SETUP ##################################################################################################
############################################################ COMBAT LOGIC ################################################################################################


    #Loads in the next char and executes their turn. If Foe, whole turn. If Hero, until options menu.
    def next_turn():
        #Check EncounterState
        if not any(c.alive for c in combat.heroes):
            combat.combatState = DEFEAT
            renpy.jump("end_combat")
        elif not any(c.alive for c in combat.foes):
            combat.combatState = VICTORY
            renpy.jump("end_combat")
        
        #renpy.log(f"Turnbuffer: {turnBuffer}")

        if combat.battletimer <= 0:
            combat.combatState = VICTORY
            renpy.jump("end_combat")

        combat.battletimer -= 1
        
        d100 = roll_dice()
        combat.currCharIndex = combat.turnBuffer.pop(0)
        combat.charInstance = combat.units[combat.currCharIndex]
        #renpy.log(f"combat.currCharIndex: {combat.currCharIndex}")

        #StatusEffects
        #statusEffect[0] holds the id of actual Status Effect
        #statusEffect[1] holds the duration for how long the effect has been active already
        #statusEffect[2] If applicable, holds additional values, i.e.: Taunt -> tauntingChar
        combat.charInstance.taunter = None
        combat.charInstance.stunned = False
        for statusEffect in combat.charInstance.statusEffects[:]: #iterates over a shallow copy of the list, so as not to create problems when removing an element of the list
            _statusEffect = get_statuseffect_by_id(statusEffect[0])
            #Check Timer
            if statusEffect[1] >= _statusEffect.duration:
                try:
                    combat.charInstance.statusEffects.remove(statusEffect)
                except ValueError:
                    renpy.log(f"Error when trying to remove: {statusEffect} from {combat.units[combat.currCharIndex]}.")
                pass

            else:
                statusEffect[1] += 1
                #BUFF
                if _statusEffect.statusType == BUFF:
                    combat.charInstance.statChanges.add_stats(_statusEffect.stats)
                #DOT
                elif _statusEffect.statusType == DOT:
                    dotDamage = combat.charInstance.get_real_max_hp() / _statusEffect.power
                    take_damage(combat.currCharIndex, dotDamage)
                    #renpy.log(f"{combat.units[combat.currCharIndex].name} is taking {dotDamage} Dot Damage, {_statusEffect.duration - statusEffect[1]} more Turns.")
                    #TODO: Show Dot Damage visually!

                #REGEN
                elif _statusEffect.statusType == REGEN:
                    regenerate_hmp(combat.currCharIndex, _statusEffect.hpRegen, _statusEffect.mpRegen)
                #STUN
                elif _statusEffect.statusType == STUN:
                    combat.charInstance.stunned = True
                    renpy.log(f"Char at {combat.currCharIndex} is stunned.")
                #TAUNT
                elif _statusEffect.statusType == TAUNT:
                    taunter = statusEffect[2]
                    if combat.units[taunter].alive and combat.units[taunter].get_pos != RANGED:
                        combat.charInstance.taunter = taunter
                        renpy.log(f"Char at {combat.currCharIndex} is taunted by Char at {taunter}.")
                    else:
                        combat.charInstance.taunter = None
                        renpy.log("Ranged chars can't taunt")
                else:
                    raise TypeError("StatusEffect ID doesnt match" + str(statusEffect[0].statusType))

        recalculate_statchanges(combat.currCharIndex)

        #increase combat.speedTable
        if(combat.speedValues[combat.currCharIndex] + combat.charInstance.statChanges.speed <= 0):
            combat.speedTable[combat.currCharIndex] += 1
        else:
            combat.speedTable[combat.currCharIndex] += 1/(combat.speedValues[combat.currCharIndex] + combat.charInstance.statChanges.speed)

        #Update Text TODO
        combat.combat_text = f"{combat.units[combat.currCharIndex].char.name}s Turn"

        calculate_turn_buffer()
        predict_turn_buffer()
        renpy.show_screen("combat_turnbuffer")

        #Give Control to current Char
        if combat.charInstance.stunned:
            next_turn()
        else:
            if(combat.currCharIndex < combat.numHeroes):
                renpy.jump("show_combat_options_main")
            elif combat.combatState == ONGOING: 
                execute_foes_turn()
            else:
                pass
                #TODO: Just saw that there is no alternative currently? Rethink this later.

    #Appends the next Char to the Buffer
    def calculate_turn_buffer():
        if combat.initialTurns:
            if(min(combat.speedTable) > 0.0):
                combat.initialTurns = False
                combat.turnBuffer.append(combat.speedTable.index(min(combat.speedTable)))
        else:
            combat.turnBuffer.append(combat.speedTable.index(min(combat.speedTable)))
        #renpy.log(combat.speedTable)

    def predict_turn_buffer():
        combat.turnBufferPrediction = list(combat.turnBuffer)
        speedTablePrediction = list(combat.speedTable)
        for char in combat.turnBuffer:
            if(combat.speedValues[char] + combat.units[char].statChanges.speed <= 0):
                speedTablePrediction[char] += 1
            else:
                speedTablePrediction[char] += 1/(combat.speedValues[char] + combat.units[char].statChanges.speed)
        for i in range (10 - len(combat.turnBuffer)): #Amount of predicted turns = 10
            combat.turnBufferPrediction.append(speedTablePrediction.index(min(speedTablePrediction)))
            char = combat.turnBufferPrediction[-1]
            if(combat.speedValues[char] + combat.units[char].statChanges.speed <= 0):
                speedTablePrediction[char] += 1
            else:
                speedTablePrediction[char] += 1/(combat.speedValues[char] + combat.units[char].statChanges.speed)

    #Deal Damage to unit, target is index of the targeted character, NOT the instance.
    def take_damage(target, damage):
        targetchar = combat.units[target]

        if not targetchar.alive:
            return
        
        add_popup_combat(combat.positions[target][0], combat.positions[target][1]-75, text = f"-{damage} HP", duration = 2, transform = fadeinout(transition = 0.15, wait = 1.5), style = "text_damage")
        add_sprite_effect(target, 1, sprite_hit())
        targetchar.hp -= damage

        if targetchar.hp <= 0:
            if not combat.ko:
                targetchar.hp = 1
                append_message(f"{targetchar.char.name} just barely held on...")
                return

            targetchar.hp = 0
            targetchar.alive = False
            load_char_combat_anim(target, "ko", 1.0)
            append_message(f"{targetchar.char.name} has fainted.")

            if target >= combat.numHeroes: #if target was a Foe
                loottable = get_loot_by_id(combat.units[target].cid)
                if loottable is not None:
                    for item in loottable.roll_loot():
                        lootInventory.add_item(item)
                    lootInventory.add_money(loottable.roll_money(), sound = False)
                    #TODO: Make EXP gain more flashy, also make sure system works as intended and eventually that non fighting characters get part xp(per finished combat/dungeon perhaps?)
                    for i, hero in enumerate(combat.heroes):
                        exp = round(loottable.get_exp(combat.units[target].char.get_level - hero.char.get_level)/combat.numHeroes)
                        hero.char.gain_exp(exp)
                        add_popup_combat(combat.positions[i][0], combat.positions[i][1]-75, text = f"+{exp} EXP", duration = 2, transform = fadeinout(transition = 0.15, wait = 1.5), style = "text_exp")

            combat.speedTable[target] = 1000000
            if target in combat.turnBuffer:
                try:
                    combat.turnBuffer.remove(target)
                except ValueError:
                    renpy.log(f"Error when trying to remove: {combat.units[target].char.name} from turnBuffer.")
                calculate_turn_buffer()
        return

    def calculate_damage(caster, target, ability):
        targetchar = combat.units[target]
        casterchar = combat.units[caster]

        #parameters
        power = casterchar.char.get_power(ability.attType) + ability.power + casterchar.statChanges.get_power(ability.attType)
        defense = targetchar.char.get_defense(ability.attType) + targetchar.statChanges.get_defense(ability.attType)
        luckdiff = (casterchar.char.get_luck + casterchar.statChanges.luck) / (targetchar.char.get_luck + targetchar.statChanges.luck)
        #base critchance = 20%, already uses luck as parameter, no additional luck for dice
        d100 = roll_dice()
        crit = d100 < 25 * (casterchar.char.get_luck + casterchar.statChanges.luck) / (targetchar.char.get_luck + targetchar.statChanges.luck)
        dmgType = ability.dmgType

        if debug:
            renpy.log(f"Calculating Damage, dmgType is: {dmgType}")
            
        if dmgType == ADAPTIVE:
            dmgType = casterchar.char.get_dmg_type
            if debug:
                renpy.log(f"Adaptive is: {casterchar.char.get_dmg_type}")

        if dmgType == NORMAL:
            #Basic Damage Calculation: Normal Power vs Resistance
            damage = power * (power/(power+defense))

        elif dmgType == PIERCING:
            #Gamble type of Attack, if attack pierces, ignore 75% armor, do increased damage and apply Bleed(?) effect(see statuseffect application), if not, increase armor value by 1.25 and half damage
            d100 = roll_dice(1, 100, luckdiff, 1.15)
            if 100 - d100 <= get_pierce_chance(caster, target, ability):
                #Pierced, ignore 75% of armor and increase damage by 1.25
                damage = power * (power/(power+defense * 0.25)) * 1.25
            else:
                #Failed to pierce, lower damage by 0.5
                damage = power * (power/(power+defense*1.25)) * 0.5

        elif dmgType == BLUNT:
            #Ol' reliable, Damage scales inversely with foes relative armor, May apply Stun(see statuseffect application) Note: deliberately ignores temporary stat changes, might want to change at some point?
            armorratio = targetchar.char.get_defense(ability.attType) / targetchar.char.get_stats_average
            damage = power * (power/(power+defense)) * armorratio
            
        elif dmgType == SLICING:
            #Situational Attack, lower base damage, but damage scales STRONGLY with relative speed of caster/target. high chance to apply Bleed effect, so especially useful against high HP targets/bosses
            speedratio = (casterchar.char.get_speed + casterchar.statChanges.speed)/(targetchar.char.get_speed + targetchar.statChanges.speed)
            damage = power * (power/(power+defense)) * speedratio

        elif dmgType == EXPLOSIVE:
            #Situational Attack, lower base damage, but ignores 25% of defense and scales additionally with casters magic Power. Most often is AOE attack. Chance to apply Stun effect?, especially useful groups of enemies and high armor enemies
            damage = power * (power/(power+defense*0.75)) + casterchar.char.get_magic_pow * 0.5
            
        elif dmgType == TRUE:
            #Completly ignores foes defense, not much to say here. Reserved for the most powerful of abilities, Always useful.
            damage = power * 1.25

        if crit:
            damage *= 1.5

        #if debug:
        #    renpy.log(f"Damage Attacker is: {damage}, Defense Defender is {targetInfo[1]}")

        return round(max(damage, 1))


    #takes damage/resistance ratio, speedratio and dexratio of caster/target into account
    def get_pierce_chance(caster, target, ability):
        casterchar = combat.units[caster]
        targetchar = combat.units[target]

        # Safety floors to avoid division by zero
        res = max(1.0, targetchar.char.get_defense(ability.attType) + targetchar.statChanges.get_defense(ability.attType))
        speedtarget = max(1.0, targetchar.char.get_speed + targetchar.statChanges.speed)
        dexteritytarget = max(1.0, targetchar.char.get_dexterity + targetchar.statChanges.dexterity)

        dmg = casterchar.char.get_power(ability.attType) + ability.power + casterchar.statChanges.get_power(ability.attType)
        speedcaster = casterchar.char.get_speed + casterchar.statChanges.speed
        dexteritycaster = casterchar.char.get_dexterity + casterchar.statChanges.dexterity

        damageratio = clamp((dmg / res) - 0.5, 0.0, 1.0)
        speedratio  = clamp((speedcaster / speedtarget) - 0.5, 0.0, 1.0)
        dexratio    = clamp((dexteritycaster / dexteritytarget) - 0.5, 0.0, 1.0)

        chance = (damageratio * 0.5 + speedratio * 0.25 + dexratio * 0.25)
        if debug:
            renpy.log(f"Pierce Chance: {chance}")

        return round(clamp(chance * 100, 5, 100))

    #Recovers HP and MP by factors mp/hp respectively
    def regenerate_hmp(target, hp = 0, mp = 0, stamina = 0):
        targetchar = combat.units[target]

        targetchar.hp = min(targetchar.hp + round(targetchar.get_real_max_hp() * hp), targetchar.get_real_max_hp())
        targetchar.mp = min(targetchar.mp + round(targetchar.get_real_max_mp() * mp), targetchar.get_real_max_mp())
        targetchar.stamina = min(targetchar.stamina + round(targetchar.get_real_max_stamina() * stamina), targetchar.get_real_max_stamina())
        return


    def apply_affinities(damage, caster, target, magicType):
        targetchar = combat.units[target]
        casterchar = combat.units[caster]

        damage *= casterchar.char.get_affinities().get_affinity(magicType) / targetchar.char.get_affinities().get_affinity(magicType)
        return max(round(damage), 1)

    def recalculate_statchanges(target):
        targetchar = combat.units[target]

        targetchar.statChanges = Stats()
        for statusEffect in targetchar.statusEffects:
            _statusEffect = get_statuseffect_by_id(statusEffect[0])
            if statusEffect[1] < _statusEffect.duration and _statusEffect.statusType == BUFF:
                targetchar.statChanges.add_stats(_statusEffect.stats)
        return

    def apply_status_effects(target, statusEffects): #statusEffects, as always, a list of statusEffect ID´s
        targetchar = combat.units[target]

        if statusEffects is not None:
            for statusEffectID in statusEffects:
                statusEffect = get_statuseffect_by_id(statusEffectID)
                d100 = roll_dice()
                if d100 > statusEffect.chance:
                    renpy.log(f"Not applying status effect, bad luck. {d100} > {statusEffect.chance}")
                    continue
                renpy.log(f"Applying status effect. {d100} < {statusEffect.chance}")
                if statusEffect.statusType == TAUNT:
                    targetchar.statusEffects.append([statusEffectID, statusEffect.duration, combat.currCharIndex])
                elif statusEffect.statusType == BUFF:
                    targetchar.statusEffects.append([statusEffectID, statusEffect.duration, None])
                    recalculate_statchanges(target)
                else:
                    targetchar.statusEffects.append([statusEffectID, statusEffect.duration, None])
        return

    #Targets is a set of Tuples like this(targetIndex, damagemodifier/falloff)
    def execute_damage_ability(ability, targets):
        for targetInfo in targets:
            target = targetInfo[0]
            targetchar = combat.units[target]
            if not targetchar.alive:
                continue

            #Dexterity check, roll new dice for each opponent, Ex: heroEva = 20, foeEva = 30; if (100+20-30)=90 >= rand[1-100] -> 90% accuracy
            d100 = roll_dice()
            if ability.radius > 0: #TODO: AOE attacks cant miss currently, Keep as intended?
                pass
            elif (100 + combat.charInstance.char.get_dexterity + combat.charInstance.statChanges.dexterity - targetchar.char.get_dexterity - targetchar.statChanges.dexterity) < d100:
                append_message(f"{targetchar.char.name} dodges the Attack")
                continue

            #Roll again for Counter
            d100 = roll_dice()
            damage = calculate_damage(combat.currCharIndex, target, ability)
            #Counter check, Reflect always has Priority, then Riposte, then Parry
            #renpy.log(f"Counter chance check: {d100}?")

            #Reflect, no reach check
            if get_statuseffect_by_id(targetchar.reflect).chance >= d100: 
                counterDamage = damage * get_statuseffect_by_id(targetchar.reflect).power
                counterDamage *= targetInfo[1]
                counterDamage = apply_affinities(counterDamage, target, combat.currCharIndex, ability.magicType)
                take_damage(combat.currCharIndex, counterDamage)
                append_message(f"{targetchar.char.name} REFLECTED the attack, {combat.charInstance.char.name} takes {counterDamage} damage")
                continue

            #Riposte, melee check
            elif get_statuseffect_by_id(targetchar.riposte).chance >= d100 and ability.reach == MELEE: 
                counterDamage = calculate_damage(target, combat.currCharIndex, basicMelee) * get_statuseffect_by_id(targetchar.riposte).power
                if combat.charInstance.char.get_pos == RANGED:
                    counterDamage *= 2
                take_damage(combat.currCharIndex, counterDamage)
                append_message(f"{targetchar.char.name} RIPOSTED the attack, {combat.charInstance.char.name} takes {counterDamage} damage")
                continue

            #Parry, melee check
            elif get_statuseffect_by_id(targetchar.parry).chance >= d100 and ability.reach == MELEE: 
                append_message(f"{targetchar.char.name} PARRIED the attack")
                continue
            
            #Attack goes through!:
            if debug:
                renpy.log(f"Damage Fall off is: {targetInfo[1]}")
            damage *= targetInfo[1]
            damage = apply_affinities(damage, combat.currCharIndex, target, ability.magicType)
            if targetchar.char.get_pos == RANGED and ability.reach == MELEE:
                damage *= 2
            append_message(f"Dealing {damage} damage to {targetchar.char.name}")
            take_damage(target, damage)
            apply_status_effects(target, ability.statusEffects)

        return

########################################################## END COMBAT LOGIC ##############################################################################################
########################################################## HEROS TURN LOGIC ##############################################################################################


    #Executes the Players chosen ability and invokes the next turn
    #targets - a single target if Singletarget, a list of targets otherwise, each entry consists of (target, damageFalloff)
    def execute_heroes_turn(targets): 
        ability = get_ability_by_id(combat.chosenAbilityID)
        if ability.radius == SINGLE:
            targets = [(targets, 1.0)]
        combat.charInstance.mp -= ability.mp
        combat.charInstance.stamina -= ability.stamina

        #Check for abilitytype
        if isinstance(ability, DamageAbility):
            execute_damage_ability(ability, targets)
        elif isinstance(ability, SupportAbility):
            for targetInfo in targets:
                if ability.category == HEAL:
                    regenerate_hmp(targetInfo[0], ability.power)
                apply_status_effects(targetInfo[0], ability.statusEffects)

        elif isinstance(ability, SpecialAbility):
            pass
        else:
            raise TypeError("Ability type doesnt match")
        #load_char_combat_anim(combat.currCharIndex, "basicattack", 0.1)#basicMelee.name.lower()) #TODO
        set_combat_text_pause(f"{combat.charInstance.char.name} uses {ability.name}")
        display_combat_messages()
        next_turn()
    
    #Hero resting
    def recover_heroes_turn():
        regenerate_hmp(combat.currCharIndex, 0.05, 0.05)
        set_combat_text_pause(f"{combat.charInstance.char.name} is Resting")
        next_turn()


######################################################## END HEROS TURN LOGIC ############################################################################################
########################################################### FOE TURN LOGIC ###############################################################################################


    #Executes a single foes turn
    def execute_foes_turn():
        foe_use_ability()
        next_turn()

    #Runs through foes logic what ability to use and executes it
    def foe_use_ability():
        foeInstance = combat.units[combat.currCharIndex]
        foeIdentifier = f"{foeInstance.char.name}@Pos {combat.currCharIndex}" #For Debugging

        renpy.log(f"Foe {foeIdentifier} choosing Ability.")
        d100loop = renpy.random.randint(1, 100)
        while(True):
            if d100loop <= CHANCESTATUS: # x %chance
                renpy.log(f"Foe {foeIdentifier} using SupportAbility - d100loop= {d100loop}")
                #Status Ability - currently each Ability equally as likely(if possible to cast)
                supportAbilities = foeInstance.char.get_abilities(SUP)
                numAbilities = len(supportAbilities)
                if numAbilities == 0:
                    renpy.log(f"Foe {foeIdentifier} doesn't have any StatusAbilities")
                    d100loop += CHANCESTATUS
                    continue
                randAbility = renpy.random.randint(0, numAbilities-1)

                for i in range(numAbilities): #Try in numerical order, TODO: better implementation
                    ability = get_ability_by_id(supportAbilities[randAbility])
                    if ability.mp <= foeInstance.mp: #Check for MP TODO: check for stamina
                        renpy.log(f"Foe {foeIdentifier} has enough MP for Ability")
                        target = get_lowest_percent_health_foe()

                        #Check for Category and possible targets
                        #HEAL
                        if ability.category == HEAL and get_percent_health(target+combat.numHeroes) <= 100.0: 
                            renpy.log(f"Foe {foeIdentifier} is using a Heal, and has found a target")
                            regenerate_hmp(target+combat.numHeroes, get_ability_by_id(supportAbilities[randAbility]).power)
                            foeInstance.mp -= ability.mp
                            return

                        #TODO: OTHER Support ability Categories, default

                    randAbility = (randAbility + 1) % numAbilities
                    renpy.log(f"Foe {foeIdentifier}: NVM, not possible, try next SupportAbility")
                d100loop += CHANCESTATUS
                renpy.log(f"No SupportAbility possible, moving on.")
                continue

                #CONTROL ABILITIES
            elif d100loop <= CHANCESPECIAL:
                #Special Ability
                renpy.log(f"No Special ability implementation yet, moving on.")
                return
            elif d100loop <= CHANCEREST:
                #Recover for a Turn
                renpy.log(f"Foe {foeIdentifier} trying to rest - d100loop= {d100loop}")
                if get_percent_health(combat.currCharIndex) <= 0.5 or get_percent_health(combat.currCharIndex) <= 0.25:
                    append_message(f"{foeInstance.char.name} is resting...")
                    recover_foe_turn()
                    return
                d100loop += CHANCEREST - CHANCESPECIAL
                renpy.log(f"Foe {foeIdentifier} too healthy to rest, moving on.")
            else:
                #Damage Ability - Last because Damage Ability always works! - currently each Ability equally as likely (if possible to cast)
                renpy.log(f"Foe {foeIdentifier} using DamageAbility - d100loop= {d100loop}")
                damageAbilities = foeInstance.char.get_abilities(OFF)
                numAbilities = len(damageAbilities)
                
                randAbility = renpy.random.randint(0, numAbilities-1)
                renpy.log(f"numAbilities = {numAbilities}")
                check_remain_melee_foes()
                for i in range(numAbilities):
                    ability = get_ability_by_id(damageAbilities[randAbility])
                    renpy.log(f"Foe {foeIdentifier} trying to choose DamageAbility in loop: {ability.name}")
                    if ability.mp <= foeInstance.mp and not (foeInstance.char.get_pos == RANGED and ability.reach == MELEE and combat.meleeFoesRemain): #to second part: logic in brackets evaluates to true only if the character is ranged, the ability is melee and there are still friendly melee frontliners, and only then do we NOT allow the abilíty to be chosen
                        #renpy.log(f"Foe {foeIdentifier} has enough MP for Ability")
                        combat.chosenAbilityID = ability.abilityID
                        break
                    randAbility = (randAbility + 1) % numAbilities
                append_message(f"{foeInstance.char.name} uses {ability.name}")
                foeInstance.mp -= ability.mp
                #chose Target randomly, if fainted, add 1 and try again
                if foeInstance.taunter:
                    target = foeInstance.taunter
                else:
                    target = d100loop % combat.numHeroes

                check_remain_melee_heroes()
                while not combat.units[target].alive or (ability.reach < combat.units[target].char.get_pos and combat.meleeHeroesRemain): #TODO: CHECK THAT LOGIC and decide, can ranged heroes attack other ranged heroes always??? #to second part: if target is out of reach AND there are no other melee heroes remaining, only then do we search for a new target
                    target = (target + 1) % combat.numHeroes
                targets = None
                if ability.radius == SINGLE:
                    targets = [(target, 1.0)]
                else: 
                    get_aoe_targets_heroes(target)
                    targets = combat.aoeTargets

                renpy.log(f"Foe Targets are: {targets}")

                execute_damage_ability(ability, targets)

                display_combat_messages()
                return        

    def get_lowest_percent_health_foe():
        result = None
        lowest = 1.0
        for i in range(combat.numFoes):
            current = get_percent_health(i+combat.numHeroes)
            if current <= lowest:
                result = i
                lowest = current
        return result

    def get_percent_health(index):
        return combat.units[index].hp / combat.units[index].get_real_max_hp()

    def get_percent_mp(index):
        return combat.units[index].mp / combat.units[index].get_real_max_mp()

    def get_percent_stamina(index):
        return combat.units[index].stamina / combat.units[index].get_real_max_stamina()


    #Foe resting
    def recover_foe_turn():
        regenerate_hmp(combat.currCharIndex, 0.05, 0.05, 0.05)


######################################################### END FOE TURN LOGIC #############################################################################################
####################################################### COMBAT CONTROL LABELS  ##########################################################################################

label start_combat: 
    if not debug:
        $ config.rollback_enabled = False
    else:
        "Feel free to jump back here"
        
    #Show combat screens
    $ renpy.show_screen("combat_main_screen", _layer = "screens")
    $ renpy.show_screen("combat_text", _layer = "screens")

    jump turn_next_turn
    return

label turn_next_turn:
    $ next_turn()
    $ renpy.log("ERROR - overshot, this shouldnt happen @ label turn_next_turn")
    return


label show_combat_options_main:
    python:
        tr = None
        if combat.first:
            tr = fadein(wait = 3.5)
            combat.first = False
        _result = renpy.call_screen("combat_options_main", _layer = "screens", _transform = tr)
    if _result == ATTACK: 
        $ combat.chosenAbilityID = combat.charInstance.basicattackID
        jump show_target_selection
    elif _result == SKILLS:
        jump show_combat_options_skills
    elif _result == REST:
        $ regenerate_hmp(combat.currCharIndex, 0.1, 0.05, 0.05)
        $ next_turn()
    elif _result == LEAVE:
        $ combatState = LEAVE
        jump end_combat
    return
        

label show_combat_options_skills:
    $ check_remain_melee_heroes()
    $ _result = renpy.call_screen("combat_options_skills")
    if _result == BACK:
        jump show_combat_options_main
    elif _result in [OFF, SUP, CTR, SPEC]: 
        $ combat.chosenAbilityID = _result
        jump show_target_selection
    else:
        $ combat.chosenAbilityID = _result
        jump show_target_selection
    return


label show_target_selection:

    show screen combat_text
    python:
        set_combat_text(f"{get_ability_by_id(combat.chosenAbilityID).name} - Choose Target")
        check_remain_melee_heroes()
        check_remain_melee_foes()
        _result = 0
        if get_ability_by_id(combat.chosenAbilityID).targeting == HOSTILE:
            _result = renpy.call_screen("target_selection_foes", _layer = "screens")
        elif get_ability_by_id(combat.chosenAbilityID).targeting == FRIENDLY:
            _result = renpy.call_screen("target_selection_heroes", _layer = "screens")
        elif get_ability_by_id(combat.chosenAbilityID).targeting == SELF:
            execute_heroes_turn(_result)
        else:
            raise TypeError(f"Invalid Targeting parameter{get_ability_by_id(combat.chosenAbilityID).targeting}")
        if _result == -1:
            renpy.jump("show_combat_options_main")
        else:
            #renpy.log(f"target/s: {_result}")
            execute_heroes_turn(_result)
    return



label end_combat:
    $ config.rollback_enabled = True
    $ close_combat_screens()

    if combat.combatState == DEFEAT:
        $ reset_lootinventory()

    if currDungeon: #We are/were inside a Dungeon
        if combat.combatState == VICTORY:
            $ currDungeon.next_phase() #also handles dungeon completion
        else:
            jump exit_dungeon
            
    $ renpy.call_screen("s_combat_exit")
    #$ combat.combatMessages = []
    jump leave_combat
    return

label leave_combat:
    call hide_combat_screens from _call_hide_combat_screens
    $ tempstring = combat.cCallback
    $ combat = None
    if tempstring is not None:
        jump expression tempstring
    jump current_location

#TODO: still relevant or to be deleted?
label hide_combat_screens():
    hide screen combat_main_screen
    hide screen combat_popups
    hide screen combat_text
    return