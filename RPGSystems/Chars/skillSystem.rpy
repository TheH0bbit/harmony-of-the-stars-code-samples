"""
Skill Tree System
=================

Implements character-specific progression trees.

Responsibilities
----------------

• Skill tree definitions
• Skill node registration
• Unlock progression
• Dependency validation
• Character-specific progression paths

Architecture
------------

Skill trees are defined independently of runtime character state.

Each character owns a dedicated progression tree composed of
individual skill nodes. Unlocking nodes grants new gameplay
capabilities while allowing progression logic to remain separate
from combat behaviour and character statistics.

Collaborates with
-----------------

• Characters
• Stats
• Abilities
• Combat
"""

init python:
    SKILLNODES = {}
    SKILLTREES = {}

    def register_tree(tree):
        SKILLTREES[tree.charID] = tree

    def get_skillnode_by_id(nodeID):
        return SKILLNODES.get(nodeID)

    def register_node(node):
        SKILLNODES[node.nodeID] = node

    class SkillTree(object):
        def __init__(self, charID, root):
            self.charID = charID
            self.root = root
            self.nodes = [root]
            root.get_all_children(self.nodes)
            register_tree(self)

    class SkillNode(object):
        def __init__(self, nodeID, skill, name, descr, cost, pos):
            self.nodeID = nodeID
            self.skill = skill
            self.name = name
            self.descr = descr
            self.cost = cost
            self.pos = pos
            self.children = []
            self.parents = []
            register_node(self)

        def get_all_children(self, listRef):
            for node in self.children:
                if node in listRef:
                    continue
                listRef.append(node)
                node.get_all_children(listRef)
            return

        def set_children(self, children):
            for child in children:
                self.children.append(child)
                child.parents.append(self)

        def set_child(self, child):
            self.children.append(child)
            child.parents.append(self)

