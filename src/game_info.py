"""
Constants and tiny utilites related to the game
"""

import enum

VIEW_BOUNDS = (1286, 725)

class FCObjectTraits(object):
    """
    Mask bits for various traits of FC object types
    """
    CIRCLE = 1 << 0 # is a circle
    UNROTATABLE = 1 << 1 # cannot be rotated
    MOVABLE = 1 << 2 # can move
    DESIGN = 1 << 3 # is a design piece
    JOINTABLE = 1 << 4 # can be jointed
    COLLIDES = 1 << 5 # collides with everything
    GOAL = 1 << 6 # goal piece/area
    POWERED = 1 << 7 # is powered
    CLOCKWISE = 1 << 8 # is a clockwise wheel
    NO_SELF_COLLIDE = 1 << 9 # does not collide with others of same type
    PIN = 1 << 10 # zero width, which causes pin behaviour

class FCObjectTypes(enum.Enum):
    """
    Enum of all standard FC object types
    """
    EMPTY = 0
    STATIC_RECT = FCObjectTraits.COLLIDES
    STATIC_CIRCLE = STATIC_RECT | FCObjectTraits.CIRCLE
    DYNAMIC_RECT = FCObjectTraits.COLLIDES | FCObjectTraits.MOVABLE
    DYNAMIC_CIRCLE = DYNAMIC_RECT | FCObjectTraits.CIRCLE
    GHOST = DYNAMIC_RECT | FCObjectTraits.PIN
    GOAL_RECT = FCObjectTraits.MOVABLE | FCObjectTraits.GOAL | FCObjectTraits.DESIGN | FCObjectTraits.JOINTABLE
    GOAL_CIRCLE = GOAL_RECT | FCObjectTraits.CIRCLE
    BUILD_AREA = FCObjectTraits.UNROTATABLE
    GOAL_AREA = FCObjectTraits.UNROTATABLE | FCObjectTraits.GOAL
