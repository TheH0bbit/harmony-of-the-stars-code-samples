"""
Progression flag storage and lookup helpers.
"""

default flags = FlagManager()

init python:

    def evaluate_flag(flag_construct):
        return flags.has_flag(flag_construct["category"], flag_construct["identifier"], flag_construct["flag"])

    class CharFlags:
        def __init__(self):
            self.flags = {}

        def get(self, identifier):
            if isinstance(identifier, Chara):
                identifier = identifier.cid
            return self.flags.setdefault(identifier, set())

        def set(self, identifier, flag):
            if isinstance(identifier, Chara):
                identifier = identifier.cid
            self.get(identifier).add(flag)

        def has(self, identifier, flag):
            if isinstance(identifier, Chara):
                identifier = identifier.cid
            return flag in self.get(identifier)

        def remove(self, identifier, flag):
            if isinstance(identifier, Chara):
                identifier = identifier.cid
            self.get(identifier).discard(flag)

        def has_all(self, identifier, requiredFlags):
            if isinstance(identifier, Chara):
                identifier = identifier.cid
            if not requiredFlags:
                return True
            return requiredFlags.issubset(self.get(identifier))
        
        def has_any(self, identifier, flags):
            if isinstance(identifier, Chara):
                identifier = identifier.cid
            if not flags:
                return True
            return bool(self.get(identifier).intersection(flags))


    class EntityFlags:
        def __init__(self):
            self.flags = {}

        def get(self, identifier):
            return self.flags.setdefault(identifier, set())

        def set(self, identifier, flag):
            self.get(identifier).add(flag)

        def has(self, identifier, flag):
            return flag in self.get(identifier)

        def remove(self, identifier, flag):
            self.get(identifier).discard(flag)

        def has_all(self, identifier, requiredFlags):
            if not requiredFlags:
                return True
            return requiredFlags.issubset(self.get(identifier))
        
        def has_any(self, identifier, flags):
            if not flags:
                return True
            return bool(self.get(identifier).intersection(flags))

    # identifier is accepted to keep the same interface as scoped flag stores.
    class SimpleFlags:
        def __init__(self):
            self.flags = set()

        def get(self, identifier):
            return self.flags

        def set(self, identifier, flag):
            self.flags.add(flag)

        def has(self, identifier, flag):
            return flag in self.flags

        def remove(self, identifier, flag):
            self.flags.discard(flag)

        def has_all(self, identifier, requiredFlags):
            if not requiredFlags:
                return True
            return requiredFlags.issubset(self.flags)
        
        def has_any(self, identifier, flags):
            if not flags:
                return True
            return bool(self.flags.intersection(flags))

    # Unified access to each flag category.
    
    class FlagManager:
        def __init__(self):
            self.char = CharFlags()
            self.loc = EntityFlags()
            self.map = EntityFlags()
            self.dungeons = EntityFlags()
            self.story = SimpleFlags()

        def apply_flags(self, newFlags):
            for _flag in newFlags:
                self.set_flag(_flag["category"], _flag["identifier"], _flag["flag"])

        def get(self, identifier):
            if identifier == CHAR:
                return self.char
            elif identifier == LOC:
                return self.loc
            elif identifier == MAP:
                return self.map
            elif identifier == STORY:
                return self.story
            elif identifier == DUNGEON:
                return self.dungeons
        
        # Generic access helpers used by systems that receive a category at runtime.
        def get_flags(self, category, identifier):
            return self.get(category).get(identifier)

        def set_flag(self, category, identifier, flag):
            self.get(category).set(identifier, flag)

        def has_flag(self, category, identifier, flag):
            return flag in self.get(category).get(identifier)

        def remove_flag(self, category, identifier, flag):
            self.get(category).remove(identifier, flag)

        def has_all(self, category, identifier, flags):
            if not flags:
                return True
            return self.get(category).has_all(identifier, flags)
        
        def has_any_flag(self, category, identifier, flags):
            if not flags:
                return True
            return self.get(category).has_any_flag(identifier, flags)
