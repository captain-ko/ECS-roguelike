from dataclasses import dataclass, field
import numpy as np


@dataclass
class Inventory:
    max_carry_weight: int
    bag: dict[int, int] = field(default_factory = dict)

@dataclass
class Item:
    name: str
    item_type: str
    value: int
    

@dataclass
class WeaponStats:
    strength_bonus: int
    
@dataclass
class ArmorStats:
    armor_rating: int


@dataclass
class Position:
    
    x: int
    y: int
    z: int


@dataclass
class Velocity:
    dx: int
    dy: int

@dataclass
class ColorScheme:
    fg: tuple[int, int, int] = (255,255,255)
    bg: tuple[int, int, int] = (0,0,0)

@dataclass
class Renderable:
   
    char: str
    color: ColorScheme 
    color_dark: ColorScheme
    render_priority: int = 0

@dataclass
class CreatureStats:

    name: str
    max_hp: int
    current_hp: int
    strength: int

@dataclass
class PlayerInput:
   
    pass

@dataclass
class GameState:
    running: bool
    turn_passed: bool

@dataclass
class BlocksMovement:
    pass

@dataclass
class Target:
    dijkstra_map: np.ndarray

@dataclass
class HasVision:
    vision_radius: int
    visible: np.ndarray
