from dataclasses import dataclass
import numpy as np

@dataclass
class Position:
    
    x: int
    y: int


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

@dataclass
class CreatureStats:

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
