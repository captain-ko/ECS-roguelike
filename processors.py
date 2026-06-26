import esper
import tcod
from tcod.console import Console
from components import Position, Velocity, Renderable, GameState, PlayerInput, CreatureStats
from gamemap import GameMap, TileType, wall, floor
import numpy as np

MOVE_KEYS = {
    tcod.event.KeySym.H: (-1, 0),
    tcod.event.KeySym.J: (0, 1),
    tcod.event.KeySym.K: (0, -1),
    tcod.event.KeySym.L: (1, 0),
    tcod.event.KeySym.Y: (-1, -1),
    tcod.event.KeySym.U: (1, -1),
    tcod.event.KeySym.B: (-1, 1),
    tcod.event.KeySym.N: (1, 1)
}


class MovementSystem(esper.Processor):
    

    def __init__(self, map_width: int, map_height: int, game_map: GameMap):
        self.map_width = map_width
        self.map_height = map_height
        self.game_map = game_map
    def process(self):
        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            if vel.dx == 0 and vel.dy == 0:
                continue  

            new_x = pos.x + vel.dx
            new_y = pos.y + vel.dy

            if 0 <= new_x < self.map_width and 0 <= new_y < self.map_height and self.game_map.tiles[new_x][new_y].walkable:
                pos.x = new_x
                pos.y = new_y
            

            esper.remove_component(ent, Velocity)   

class CombatSystem(esper.Processor):
    def process(self):
        for ent, (position, velocity, creature_stats) in esper.get_components(Position, Velocity, CreatureStats):
            for enemy, (enemy_position, enemy_creature_stats) in esper.get_components(Position, CreatureStats):
                if position.x + velocity.dx == enemy_position.x and position.y + velocity.dy == enemy_position.y:
                    enemy_creature_stats.current_hp -= creature_stats.strength
                    print("Enemy hp = " + str(enemy_creature_stats.current_hp))
                    esper.remove_component(ent, Velocity)
        

class RenderSystem(esper.Processor):
    def __init__(self, game_map: GameMap, console: Console, context: tcod.context):
        self.console = console
        self.context = context
        self.game_map = game_map
        self.transparency_map = np.full((game_map.screen_width, game_map.screen_height), True, dtype=bool)
        self.visible = np.full((game_map.screen_width, game_map.screen_height), True, dtype=bool)
        for position, tile in np.ndenumerate(game_map.tiles):
            if tile == wall:
                self.transparency_map[position] = False
        self.explored = np.full((game_map.screen_width, game_map.screen_height), False, dtype=bool)


    def compute_fov(self):
        for ent, (position, player_input) in esper.get_components(Position, PlayerInput):
            self.visible = tcod.map.compute_fov(self.transparency_map, (position.x, position.y), 8, light_walls=True, algorithm=tcod.FOV_BASIC)

    def process(self):
        self.console.clear()

        self.compute_fov()
        self.explored |= self.visible

        #PRINT TILES FROM TILEMAP
        for x in range(self.game_map.screen_width):
            for y in range(self.game_map.screen_height):
                if self.visible[x, y]:
                    self.console.print(x=x, y=y, text=self.game_map.tiles[x, y].char,fg=self.game_map.tiles[x, y].light, bg=self.game_map.tiles[x, y].bg)
                    continue
                if self.explored[x, y] and not self.visible[x, y]:
                    self.console.print(x=x, y=y, text=self.game_map.tiles[x, y].char,fg=self.game_map.tiles[x, y].dark, bg=self.game_map.tiles[x, y].bg_dark)
                

        #PRINT ESPER ENTITIES
        
        for ent, (pos, rend) in esper.get_components(Position, Renderable):
            if self.visible[pos.x, pos.y]:
                self.console.print(x=pos.x, y=pos.y, text=rend.char, fg=rend.color)

        self.context.present(self.console)

class InputSystem(esper.Processor):

    def __init__(self, game_state: GameState, player):
       super().__init__()
       self.game_state = game_state
       self.player = player

    def process(self):
        for event in tcod.event.wait():
            if isinstance(event, tcod.event.Quit):
                self.game_state.running = False
            
            elif isinstance(event, tcod.event.KeyDown):
                if event.sym == tcod.event.KeySym.ESCAPE:
                    self.game_state.running = False
                    continue

                #player_vel = esper.component_for_entity(self.player, Velocity)
                if event.sym in MOVE_KEYS:
                    dx, dy = MOVE_KEYS[event.sym]
                    esper.add_component(self.player, Velocity(dx=dx, dy=dy))

                


    
