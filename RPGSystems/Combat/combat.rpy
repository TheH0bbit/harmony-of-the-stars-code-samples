"""
Turn-based combat controller and runtime combat components.

Combat-specific state is kept separate from persistent character data through
CharCombatComponent and FoeCombatComponent. Ability, item, dungeon and UI
helpers referenced here belong to the larger Ren'Py project.
"""

init python:
    # Active encounter.
    combat = None

    # Screen positions used by the current battle layout.
    positionsV = [800, 875, 725, 950, 650]
    positionsH = [450, 325, 575, 200, 700]  # Mirrored for foes

    combat_popups = []

    def combat_log(message):
        if debug:
            renpy.log(message)

    class CombatInstance:
        def __init__(self, heroes, foes, cCallback = None):
            # Unit lists keep stable indexes for the lifetime of an encounter.
            self.heroes = []
            self.foes = []

            for hero in heroes:
                self.heroes.append(CharCombatComponent(hero))
            for foeID, level in foes:
                self.foes.append(FoeCombatComponent(foeID, level))

            self.units = MergedReferencedList(self.heroes, self.foes)

            self.numHeroes = len(heroes)
            self.numFoes = len(foes)

            # Speed table stores accumulated turn delay per unit.
            self.speedValues = []
            self.speedTable = []

            # Current and predicted turn order.
            self.turnBuffer = []
            self.turnBufferPrediction = []
            self.initialTurns = True


            # UI positions
            self.heroPositions = []
            self.foePositions = []
            self.positions = []

            # Area-of-effect targeting
            self.aoeTargets = []

            # Sprite state
            self.charSprites = []
            self.spriteEffects = []

            # Current action state
            self.currCharIndex = 0
            self.charInstance = None
            self.chosenAbilityID = None
            self.meleeHeroesRemain = True
            self.meleeFoesRemain = True
            self.combatState = ONGOING
            self.cCallback = cCallback
            self.first = True

            # Encounter rules
            self.ko = True
            self.death = True
            self.battletimer = 10000000


            # Combat messages
            self.combat_text = "Initial"
            self.combat_text_lock = False
            self.combatMessages = []

            # Build sprite and speed state in stable unit order.
            for i, hero in enumerate(self.heroes):
                self.speedValues.append(hero.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{hero.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)


            for i, foe in enumerate(self.foes):
                self.speedValues.append(foe.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{foe.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)


            # The main character at index 0 always opens the encounter.
            sortedSpeedIndices = list(enumerate(self.speedValues))
            sortedSpeedIndices.pop(0)
            sortedSpeedIndices.sort(key=lambda x : x[1], reverse=True)
            self.turnBuffer = [0] + [index for index, _ in sortedSpeedIndices]
            self.turnBufferPrediction = list(self.turnBuffer)

            if debug:
                combat_log(f"Initialized Combatstate:")
                for unit in self.units:
                    combat_log(f"Unit: {unit.char.name}")
                    combat_log(f"     Level: {unit.char.get_level}")
                    combat_log(f"     {unit.char.get_stats.print()}")
                combat_log(f"turnbuffer: {self.turnBuffer}")
                combat_log(f"turnbufferprediction: {self.turnBufferPrediction}")
            return

        # Reuse surviving hero state while replacing foes for the next phase.
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

            # Encounter rules
            self.ko = True
            self.death = True
            self.battletimer = 10000000


            # Combat messages
            self.combat_text = ""
            self.combat_text_lock = False
            self.combatMessages = []

            # Build sprite and speed state in stable unit order.
            for i, hero in enumerate(self.heroes):
                self.speedValues.append(hero.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{hero.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)


            for i, foe in enumerate(self.foes):
                self.speedValues.append(foe.char.get_speed)
                self.speedTable.append(0.0)

                self.charSprites.append(Animation(f"gui/sprites/{foe.cid}/idle".lower(), True, 0.4))
                self.spriteEffects.append(None)


            # The main character at index 0 always opens the phase.
            sortedSpeedIndices = list(enumerate(self.speedValues))
            sortedSpeedIndices.pop(0)
            sortedSpeedIndices.sort(key=lambda x : x[1], reverse=True)
            self.turnBuffer = [0] + [index for index, _ in sortedSpeedIndices]
            self.turnBufferPrediction = list(self.turnBuffer)

            if debug:
                combat_log(f"Initialized Combatstate:")
                for unit in self.units:
                    combat_log(f"Unit: {unit.char.name}")
                    combat_log(f"     Level: {unit.char.get_level}")
                    combat_log(f"     {unit.char.get_stats.print()}")
                combat_log(f"turnbuffer: {self.turnBuffer}")
                combat_log(f"turnbufferprediction: {self.turnBufferPrediction}")
            return


    class CharCombatComponent:
        def __init__(self, char):
            self.char = char
            self.cid = char.cid

            # Runtime combat state
            self.statusEffects = []
            self.passiveEffects = []

            # Load temporary effects carried through the current combat run.

            self.basicattackID = "basicmelee"
            if basicRanged in self.char.get_abilities(OFF):
                self.basicattackID = "basicranged"

            # Defensive reaction chances used by combat resolution.
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

            # Runtime combat state
            foedata = get_foe_by_id(cid)
            foeclass = get_charclass_by_id(cid)

            # Facade keeps foe access compatible with character-facing combat code.
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

            # Defensive reaction chances used by combat resolution.
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


    # Character-like facade for foe definitions.
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
        combat_log(f"Appending Message to Buffer {msg}")

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


    # Build mirrored screen positions for heroes and foes.
    def calculate_positions():
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
        for i, pos in enumerate(combat.foePositions):
            pixelDistance = distance(centerXY, pos)
            if pixelDistance <= pixelRadius:
                if falloff:
                    combat.aoeTargets.append((i + combat.numHeroes, 1.0 - (pixelDistance/pixelRadius)))
                else:
                    combat.aoeTargets.append((i + combat.numHeroes, 1.0))
        renpy.show_screen("show_aoe_targets", _layer = "screens")

    def get_aoe_targets_heroes(center, falloff = True):
        ability = get_ability_by_id(combat.chosenAbilityID)
        combat.aoeTargets = []
        centerXY = combat.heroPositions[center]
        pixelRadius = ability.radius * AVGDISTANCE
        for i, pos in enumerate(combat.heroPositions):
            pixelDistance = distance(centerXY, pos)
            if pixelDistance <= pixelRadius:
                if falloff:
                    combat.aoeTargets.append((i, 1.0 - (pixelDistance/pixelRadius)))
                else:
                    combat.aoeTargets.append((i, 1.0))
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

    def load_char_combat_anim(pos, state, duration = 0.3):
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



    # Advance to the next unit and hand control to AI or player input.
    def next_turn():
        if not any(c.alive for c in combat.heroes):
            combat.combatState = DEFEAT
            renpy.jump("end_combat")
        elif not any(c.alive for c in combat.foes):
            combat.combatState = VICTORY
            renpy.jump("end_combat")


        if combat.battletimer <= 0:
            combat.combatState = VICTORY
            renpy.jump("end_combat")

        combat.battletimer -= 1

        d100 = roll_dice()
        combat.currCharIndex = combat.turnBuffer.pop(0)
        combat.charInstance = combat.units[combat.currCharIndex]

        # Resolve active effects before the unit acts.
        combat.charInstance.taunter = None
        combat.charInstance.stunned = False
        for statusEffect in combat.charInstance.statusEffects[:]:  # Copy allows effects to expire during iteration.
            _statusEffect = get_statuseffect_by_id(statusEffect[0])
            if statusEffect[1] >= _statusEffect.duration:
                try:
                    combat.charInstance.statusEffects.remove(statusEffect)
                except ValueError:
                    combat_log(f"Error when trying to remove: {statusEffect} from {combat.units[combat.currCharIndex]}.")
                pass

            else:
                statusEffect[1] += 1
                if _statusEffect.statusType == BUFF:
                    combat.charInstance.statChanges.add_stats(_statusEffect.stats)
                elif _statusEffect.statusType == DOT:
                    dotDamage = combat.charInstance.get_real_max_hp() / _statusEffect.power
                    take_damage(combat.currCharIndex, dotDamage)

                elif _statusEffect.statusType == REGEN:
                    regenerate_hmp(combat.currCharIndex, _statusEffect.hpRegen, _statusEffect.mpRegen)
                elif _statusEffect.statusType == STUN:
                    combat.charInstance.stunned = True
                    combat_log(f"Char at {combat.currCharIndex} is stunned.")
                elif _statusEffect.statusType == TAUNT:
                    taunter = statusEffect[2]
                    if combat.units[taunter].alive and combat.units[taunter].get_pos != RANGED:
                        combat.charInstance.taunter = taunter
                        combat_log(f"Char at {combat.currCharIndex} is taunted by Char at {taunter}.")
                    else:
                        combat.charInstance.taunter = None
                        combat_log("Ranged chars can't taunt")
                else:
                    raise TypeError("StatusEffect ID doesnt match" + str(statusEffect[0].statusType))

        recalculate_statchanges(combat.currCharIndex)

        if(combat.speedValues[combat.currCharIndex] + combat.charInstance.statChanges.speed <= 0):
            combat.speedTable[combat.currCharIndex] += 1
        else:
            combat.speedTable[combat.currCharIndex] += 1/(combat.speedValues[combat.currCharIndex] + combat.charInstance.statChanges.speed)

        combat.combat_text = f"{combat.units[combat.currCharIndex].char.name}s Turn"

        calculate_turn_buffer()
        predict_turn_buffer()
        renpy.show_screen("combat_turnbuffer")

        if combat.charInstance.stunned:
            next_turn()
        else:
            if(combat.currCharIndex < combat.numHeroes):
                renpy.jump("show_combat_options_main")
            elif combat.combatState == ONGOING:
                execute_foes_turn()
            else:
                pass

    def calculate_turn_buffer():
        if combat.initialTurns:
            if(min(combat.speedTable) > 0.0):
                combat.initialTurns = False
                combat.turnBuffer.append(combat.speedTable.index(min(combat.speedTable)))
        else:
            combat.turnBuffer.append(combat.speedTable.index(min(combat.speedTable)))

    def predict_turn_buffer():
        combat.turnBufferPrediction = list(combat.turnBuffer)
        speedTablePrediction = list(combat.speedTable)
        for char in combat.turnBuffer:
            if(combat.speedValues[char] + combat.units[char].statChanges.speed <= 0):
                speedTablePrediction[char] += 1
            else:
                speedTablePrediction[char] += 1/(combat.speedValues[char] + combat.units[char].statChanges.speed)
        for i in range(10 - len(combat.turnBuffer)):
            combat.turnBufferPrediction.append(speedTablePrediction.index(min(speedTablePrediction)))
            char = combat.turnBufferPrediction[-1]
            if(combat.speedValues[char] + combat.units[char].statChanges.speed <= 0):
                speedTablePrediction[char] += 1
            else:
                speedTablePrediction[char] += 1/(combat.speedValues[char] + combat.units[char].statChanges.speed)

    # Apply damage to a unit by combat index.
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

            if target >= combat.numHeroes:
                loottable = get_loot_by_id(combat.units[target].cid)
                if loottable is not None:
                    for item in loottable.roll_loot():
                        lootInventory.add_item(item)
                    lootInventory.add_money(loottable.roll_money(), sound = False)
                    for i, hero in enumerate(combat.heroes):
                        exp = round(loottable.get_exp(combat.units[target].char.get_level - hero.char.get_level)/combat.numHeroes)
                        hero.char.gain_exp(exp)
                        add_popup_combat(combat.positions[i][0], combat.positions[i][1]-75, text = f"+{exp} EXP", duration = 2, transform = fadeinout(transition = 0.15, wait = 1.5), style = "text_exp")

            combat.speedTable[target] = 1000000
            if target in combat.turnBuffer:
                try:
                    combat.turnBuffer.remove(target)
                except ValueError:
                    combat_log(f"Error when trying to remove: {combat.units[target].char.name} from turnBuffer.")
                calculate_turn_buffer()
        return

    def calculate_damage(caster, target, ability):
        targetchar = combat.units[target]
        casterchar = combat.units[caster]

        power = casterchar.char.get_power(ability.attType) + ability.power + casterchar.statChanges.get_power(ability.attType)
        defense = targetchar.char.get_defense(ability.attType) + targetchar.statChanges.get_defense(ability.attType)
        luckdiff = (casterchar.char.get_luck + casterchar.statChanges.luck) / (targetchar.char.get_luck + targetchar.statChanges.luck)
        # Luck is already included in the critical-hit calculation.
        d100 = roll_dice()
        crit = d100 < 25 * (casterchar.char.get_luck + casterchar.statChanges.luck) / (targetchar.char.get_luck + targetchar.statChanges.luck)
        dmgType = ability.dmgType

        if debug:
            combat_log(f"Calculating Damage, dmgType is: {dmgType}")

        if dmgType == ADAPTIVE:
            dmgType = casterchar.char.get_dmg_type
            if debug:
                combat_log(f"Adaptive is: {casterchar.char.get_dmg_type}")

        if dmgType == NORMAL:
            damage = power * (power/(power+defense))

        elif dmgType == PIERCING:
            # Pierce trades consistency for a chance to bypass most defense.
            d100 = roll_dice(1, 100, luckdiff, 1.15)
            if 100 - d100 <= get_pierce_chance(caster, target, ability):
                damage = power * (power/(power+defense * 0.25)) * 1.25
            else:
                damage = power * (power/(power+defense*1.25)) * 0.5

        elif dmgType == BLUNT:
            # Crush favors raw strength against defended targets.
            armorratio = targetchar.char.get_defense(ability.attType) / targetchar.char.get_stats_average
            damage = power * (power/(power+defense)) * armorratio

        elif dmgType == SLICING:
            # Flurry scales with the caster's speed advantage.
            speedratio = (casterchar.char.get_speed + casterchar.statChanges.speed)/(targetchar.char.get_speed + targetchar.statChanges.speed)
            damage = power * (power/(power+defense)) * speedratio

        elif dmgType == EXPLOSIVE:
            # Arcane damage mixes physical and magic scaling and partially ignores defense.
            damage = power * (power/(power+defense*0.75)) + casterchar.char.get_magic_pow * 0.5

        elif dmgType == TRUE:
            # True damage bypasses defense.
            damage = power * 1.25

        if crit:
            damage *= 1.5

        return round(max(damage, 1))


    # Calculate the pierce chance from offense, defense, speed and dexterity.
    def get_pierce_chance(caster, target, ability):
        casterchar = combat.units[caster]
        targetchar = combat.units[target]

            # Avoid division by zero for very low derived stats.
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
            combat_log(f"Pierce Chance: {chance}")

        return round(clamp(chance * 100, 5, 100))

    # Recover resources by a percentage of each maximum value.
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

    def apply_status_effects(target, statusEffects):
        targetchar = combat.units[target]

        if statusEffects is not None:
            for statusEffectID in statusEffects:
                statusEffect = get_statuseffect_by_id(statusEffectID)
                d100 = roll_dice()
                if d100 > statusEffect.chance:
                    combat_log(f"Status effect roll failed: {d100} > {statusEffect.chance}")
                    continue
                combat_log(f"Applying status effect. {d100} < {statusEffect.chance}")
                if statusEffect.statusType == TAUNT:
                    targetchar.statusEffects.append([statusEffectID, statusEffect.duration, combat.currCharIndex])
                elif statusEffect.statusType == BUFF:
                    targetchar.statusEffects.append([statusEffectID, statusEffect.duration, None])
                    recalculate_statchanges(target)
                else:
                    targetchar.statusEffects.append([statusEffectID, statusEffect.duration, None])
        return

    # targets contains (unit_index, damage_modifier) pairs.
    def execute_damage_ability(ability, targets):
        for targetInfo in targets:
            target = targetInfo[0]
            targetchar = combat.units[target]
            if not targetchar.alive:
                continue

            # Roll accuracy separately for each target.
            d100 = roll_dice()
            if ability.radius > 0:
                pass
            elif (100 + combat.charInstance.char.get_dexterity + combat.charInstance.statChanges.dexterity - targetchar.char.get_dexterity - targetchar.statChanges.dexterity) < d100:
                append_message(f"{targetchar.char.name} dodges the Attack")
                continue

            d100 = roll_dice()
            damage = calculate_damage(combat.currCharIndex, target, ability)
            # Defensive reactions resolve in priority order.

            if get_statuseffect_by_id(targetchar.reflect).chance >= d100:
                counterDamage = damage * get_statuseffect_by_id(targetchar.reflect).power
                counterDamage *= targetInfo[1]
                counterDamage = apply_affinities(counterDamage, target, combat.currCharIndex, ability.magicType)
                take_damage(combat.currCharIndex, counterDamage)
                append_message(f"{targetchar.char.name} REFLECTED the attack, {combat.charInstance.char.name} takes {counterDamage} damage")
                continue

            elif get_statuseffect_by_id(targetchar.riposte).chance >= d100 and ability.reach == MELEE:
                counterDamage = calculate_damage(target, combat.currCharIndex, basicMelee) * get_statuseffect_by_id(targetchar.riposte).power
                if combat.charInstance.char.get_pos == RANGED:
                    counterDamage *= 2
                take_damage(combat.currCharIndex, counterDamage)
                append_message(f"{targetchar.char.name} RIPOSTED the attack, {combat.charInstance.char.name} takes {counterDamage} damage")
                continue

            elif get_statuseffect_by_id(targetchar.parry).chance >= d100 and ability.reach == MELEE:
                append_message(f"{targetchar.char.name} PARRIED the attack")
                continue

            if debug:
                combat_log(f"Damage Fall off is: {targetInfo[1]}")
            damage *= targetInfo[1]
            damage = apply_affinities(damage, combat.currCharIndex, target, ability.magicType)
            if targetchar.char.get_pos == RANGED and ability.reach == MELEE:
                damage *= 2
            append_message(f"Dealing {damage} damage to {targetchar.char.name}")
            take_damage(target, damage)
            apply_status_effects(target, ability.statusEffects)

        return



    # Resolve the selected player ability and advance the turn.
    def execute_heroes_turn(targets):
        ability = get_ability_by_id(combat.chosenAbilityID)
        if ability.radius == SINGLE:
            targets = [(targets, 1.0)]
        combat.charInstance.mp -= ability.mp
        combat.charInstance.stamina -= ability.stamina

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
            raise TypeError("Ability type doesn't match")
        set_combat_text_pause(f"{combat.charInstance.char.name} uses {ability.name}")
        display_combat_messages()
        next_turn()

    # Hero recovery action
    def recover_heroes_turn():
        regenerate_hmp(combat.currCharIndex, 0.05, 0.05)
        set_combat_text_pause(f"{combat.charInstance.char.name} is Resting")
        next_turn()




    # Resolve a foe turn.
    def execute_foes_turn():
        foe_use_ability()
        next_turn()

    # Select and execute an ability for the active foe.
    def foe_use_ability():
        foeInstance = combat.units[combat.currCharIndex]
        foeIdentifier = f"{foeInstance.char.name}@Pos {combat.currCharIndex}"

        combat_log(f"Foe {foeIdentifier} choosing Ability.")
        d100loop = renpy.random.randint(1, 100)
        while True:
            if d100loop <= CHANCESTATUS:
                combat_log(f"Foe {foeIdentifier} using SupportAbility - d100loop= {d100loop}")
                supportAbilities = foeInstance.char.get_abilities(SUP)
                numAbilities = len(supportAbilities)
                if numAbilities == 0:
                    combat_log(f"Foe {foeIdentifier} doesn't have any StatusAbilities")
                    d100loop += CHANCESTATUS
                    continue
                randAbility = renpy.random.randint(0, numAbilities-1)

                for i in range(numAbilities):
                    ability = get_ability_by_id(supportAbilities[randAbility])
                    if ability.mp <= foeInstance.mp:
                        combat_log(f"Foe {foeIdentifier} has enough MP for Ability")
                        target = get_lowest_percent_health_foe()

                        if ability.category == HEAL and get_percent_health(target + combat.numHeroes) < 1.0:
                            combat_log(f"Foe {foeIdentifier} is using a Heal, and has found a target")
                            regenerate_hmp(target + combat.numHeroes, get_ability_by_id(supportAbilities[randAbility]).power)
                            foeInstance.mp -= ability.mp
                            return


                    randAbility = (randAbility + 1) % numAbilities
                    combat_log(f"Foe {foeIdentifier}: support ability unavailable, trying the next option")
                d100loop += CHANCESTATUS
                combat_log(f"No SupportAbility possible, moving on.")
                continue

            elif d100loop <= CHANCESPECIAL:
                combat_log(f"No Special ability implementation yet, moving on.")
                return
            elif d100loop <= CHANCEREST:
                combat_log(f"Foe {foeIdentifier} trying to rest - d100loop= {d100loop}")
                if get_percent_health(combat.currCharIndex) <= 0.5:
                    append_message(f"{foeInstance.char.name} is resting...")
                    recover_foe_turn()
                    return
                d100loop += CHANCEREST - CHANCESPECIAL
                combat_log(f"Foe {foeIdentifier} too healthy to rest, moving on.")
            else:
                combat_log(f"Foe {foeIdentifier} using DamageAbility - d100loop= {d100loop}")
                damageAbilities = foeInstance.char.get_abilities(OFF)
                numAbilities = len(damageAbilities)

                randAbility = renpy.random.randint(0, numAbilities-1)
                combat_log(f"numAbilities = {numAbilities}")
                check_remain_melee_foes()
                for i in range(numAbilities):
                    ability = get_ability_by_id(damageAbilities[randAbility])
                    combat_log(f"Foe {foeIdentifier} trying to choose DamageAbility in loop: {ability.name}")
                    if ability.mp <= foeInstance.mp and not (foeInstance.char.get_pos == RANGED and ability.reach == MELEE and combat.meleeFoesRemain):
                        combat.chosenAbilityID = ability.abilityID
                        break
                    randAbility = (randAbility + 1) % numAbilities
                append_message(f"{foeInstance.char.name} uses {ability.name}")
                foeInstance.mp -= ability.mp
                if foeInstance.taunter:
                    target = foeInstance.taunter
                else:
                    target = d100loop % combat.numHeroes

                check_remain_melee_heroes()
                while not combat.units[target].alive or (ability.reach < combat.units[target].char.get_pos and combat.meleeHeroesRemain):
                    target = (target + 1) % combat.numHeroes
                targets = None
                if ability.radius == SINGLE:
                    targets = [(target, 1.0)]
                else:
                    get_aoe_targets_heroes(target)
                    targets = combat.aoeTargets

                combat_log(f"Foe Targets are: {targets}")

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


    # Foe recovery action
    def recover_foe_turn():
        regenerate_hmp(combat.currCharIndex, 0.05, 0.05, 0.05)



label start_combat:
    if not debug:
        $ config.rollback_enabled = False
    else:
        "Feel free to jump back here"

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
            execute_heroes_turn(_result)
    return



label end_combat:
    $ config.rollback_enabled = True
    $ close_combat_screens()

    if combat.combatState == DEFEAT:
        $ reset_lootinventory()

    if currDungeon:
        if combat.combatState == VICTORY:
            $ currDungeon.next_phase()
        else:
            jump exit_dungeon

    $ renpy.call_screen("s_combat_exit")
    jump leave_combat
    return

label leave_combat:
    call hide_combat_screens from _call_hide_combat_screens
    $ tempstring = combat.cCallback
    $ combat = None
    if tempstring is not None:
        jump expression tempstring
    jump current_location

label hide_combat_screens():
    hide screen combat_main_screen
    hide screen combat_popups
    hide screen combat_text
    return
