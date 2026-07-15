import esper
import tcod
from tcod.console import Console
from components import Position, Velocity, Renderable, GameState, PlayerInput, CreatureStats, Target, HasVision
from gamemap import GameMap, TileType, wall, floor
import numpy as np
from collections import deque
from messagelog import Message, MessageLog
from typing import Tuple

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
    def __init__(self, message_log: MessageLog):
        self.message_log = message_log
    def process(self):
        for ent, (position, velocity, creature_stats) in esper.get_components(Position, Velocity, CreatureStats):
            for enemy, (enemy_position, enemy_creature_stats) in esper.get_components(Position, CreatureStats):
                if ent == enemy:
                    continue
                if position.x + velocity.dx == enemy_position.x and position.y + velocity.dy == enemy_position.y:
                    enemy_creature_stats.current_hp -= creature_stats.strength
                    message = enemy_creature_stats.name + " was hit for " + str(creature_stats.strength) + 'damage.'
                    self.message_log.add_message(text=message)
                    esper.remove_component(ent, Velocity)
        

class RenderSystem(esper.Processor):
    def __init__(self, game_map: GameMap, map_console: Console, sidebar_console: Console, log_console: Console, context: tcod.context, player, message_log: MessageLog):
        self.map_console = map_console
        self.sidebar_console = sidebar_console
        self.log_console = log_console
        self.root_console = tcod.console.Console(log_console.width, map_console.height + log_console.height)
        self.context = context
        self.player = player
        self.message_log = message_log


        self.game_map = game_map
        self.transparency_map = np.full((game_map.screen_width, game_map.screen_height), True, dtype=bool)
        self.visible = np.full((game_map.screen_width, game_map.screen_height), True, dtype=bool)
        for position, tile in np.ndenumerate(game_map.tiles):
            if tile == wall:
                self.transparency_map[position] = False
        self.explored = np.full((game_map.screen_width, game_map.screen_height), False, dtype=bool)


    def compute_fov(self):
        for ent, (position, player_input) in esper.get_components(Position, PlayerInput):
            self.visible = tcod.map.compute_fov(self.transparency_map, (position.x, position.y), 40, light_walls=True, algorithm=tcod.FOV_BASIC)

    def process(self):
        self.map_console.clear()

        self.compute_fov()
        self.explored |= self.visible

        #This top section prints to the map_console

        #PRINT TILES FROM TILEMAP
        for x in range(self.game_map.screen_width):
            for y in range(self.game_map.screen_height):
                if self.visible[x, y]:
                    self.map_console.print(x=x, y=y, text=self.game_map.tiles[x, y].char,fg=self.game_map.tiles[x, y].light, bg=self.game_map.tiles[x, y].bg)
                    continue
                if self.explored[x, y] and not self.visible[x, y]:
                    self.map_console.print(x=x, y=y, text=self.game_map.tiles[x, y].char,fg=self.game_map.tiles[x, y].dark, bg=self.game_map.tiles[x, y].bg_dark)
                
        


        #PRINT ESPER ENTITIES
        
        for ent, (pos, rend) in esper.get_components(Position, Renderable):
            #THIS LETS YOU SEE THE DIJKSTRA MAP
            # if esper.has_component(ent, Target):
            #     dijkstra_map = esper.component_for_entity(ent, Target).dijkstra_map
            #     for x in range(self.game_map.screen_width):
            #         for y in range(self.game_map.screen_height):
            #             dist = dijkstra_map[x, y]
            #             if dist != float('inf') and self.visible[x,y]:
            #                 self.console.print(x, y, text=str(int(dist) % 10), fg = (255,255,255))

            if self.visible[pos.x, pos.y]:
                self.map_console.print(x=pos.x, y=pos.y, text=rend.char, fg=rend.color)

        #Constructing the sidebar
        max_hp = esper.component_for_entity(self.player, CreatureStats).max_hp
        current_hp = esper.component_for_entity(self.player, CreatureStats).current_hp
        strength = esper.component_for_entity(self.player, CreatureStats).strength

        x = 1
        y = 1
        self.sidebar_console.print(x, y, "HP", fg=(255,255,255))
        y += 1
        healthbar_width = self.sidebar_console.width//2
        self.sidebar_console.draw_rect(x, y, width=healthbar_width, height=1, bg=(135, 116, 114), ch = ord(' '))
        self.sidebar_console.draw_rect(x, y, width=int((current_hp/max_hp)*healthbar_width), height=1, bg=(209, 63, 48), ch=ord(' '))

        #Constructing the log console
        self.log_console.clear()
        y = 1
        for message in list(reversed(self.message_log.messages)):
            self.log_console.print(x=1,y=self.log_console.height - y, text=message.full_text, fg=message.color)
            y += 1
            



        self.map_console.blit(self.root_console, 0, 0)
        self.sidebar_console.blit(self.root_console, self.map_console.width, 0)
        self.log_console.blit(self.root_console, 0, self.map_console.height)
        self.context.present(self.root_console)

class InputSystem():

    def __init__(self, game_state: GameState, player):
      
       self.game_state = game_state
       self.player = player
       

    def process(self):
        for event in tcod.event.wait():
            self.game_state.turn_passed = False
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
                    self.game_state.turn_passed = True
                
                else:
                    self.game_state.turn_passed = False

class PathfindingSystem(esper.Processor):
    def __init__(self, game_map: GameMap):
        self.game_map = game_map
    def process(self):
        for target, (position, input) in esper.get_components(Position, PlayerInput):
            
            x, y = position.x, position.y
            stack = deque()
            
            dijkstra_map = np.full((self.game_map.screen_width, self.game_map.screen_height), fill_value=float('inf'), dtype=float)
            dijkstra_map[x, y] = 0
            stack.append((x, y))

            while stack:
                current_x, current_y = stack.popleft()
                for dx, dy in ((1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)):
                    if (0 <= current_x + dx < self.game_map.screen_width) and (0 <= current_y + dy < self.game_map.screen_height) and self.game_map.tiles[current_x + dx, current_y + dy] == floor and dijkstra_map[current_x + dx, current_y + dy] == float('inf'):
                       dijkstra_map[current_x + dx, current_y + dy] = dijkstra_map[current_x, current_y] + 1
                       stack.append((current_x + dx, current_y + dy))
            
            if esper.has_component(target, Target):
                component = esper.component_for_entity(target, Target)
                component.dijkstra_map = dijkstra_map
            else:
                esper.add_component(target, Target(dijkstra_map=dijkstra_map))

class AISystem(esper.Processor):
    def __init__(self, game_map: GameMap):
        self.game_map = game_map
    
    def process(self):
        for ent, (position, creature_stats, vision) in esper.get_components(Position, CreatureStats, HasVision):
            vision = esper.component_for_entity(ent, HasVision)
            position = esper.component_for_entity(ent, Position)
            vision.visible = tcod.map.compute_fov(self.game_map.transparency_map, (position.x, position.y), vision.vision_radius, light_walls=True, algorithm=tcod.FOV_BASIC)

            if esper.has_component(ent, Velocity):
                    continue

            for enemy, (target) in esper.get_components(Position, Target):
                if ent == enemy:
                    continue
                enemy_x = esper.component_for_entity(enemy, Position).x
                enemy_y = esper.component_for_entity(enemy, Position).y

                

                dijkstra_map =  esper.component_for_entity(enemy, Target).dijkstra_map
                

                minimum = float('inf')
                target_tile = (position.x, position.y)
                movement = (0,0)

                if vision.visible[enemy_x, enemy_y]:
                    for dx, dy in ((1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)):
                        if (0 <= position.x + dx < self.game_map.screen_width) and (0 <= position.y + dy < self.game_map.screen_height):
                            if dijkstra_map[(position.x + dx, position.y + dy)] < minimum:
                                minimum = dijkstra_map[(position.x + dx, position.y + dy)]
                                movement = (dx, dy)
                
                dx, dy = movement

                #While I considered adding a 0,0 velocity to a non-moving creature, it currently causes issues with the combat system and movement system not removing the velocity, causing new ones to never get added, immobilizing the creature. For now we just avoid adding a (0,0) velocity and will idiot-proof that later
                if not esper.has_component(ent, Velocity) and movement != (0, 0):
                    esper.add_component(
                        ent,
                        Velocity(
                            dx, dy
                        )
                )
                        
                
                

               





    
