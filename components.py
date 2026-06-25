from dataclasses import dataclass


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
class Creature:

    max_hp: int
    current_hp: int
    strength: int

@dataclass
class PlayerInput:
   
    pass

@dataclass
class GameState:
    running: bool

@dataclass
class BlocksMovement:
    pass