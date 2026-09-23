import tcod
import esper
import numpy as np

from components import Position, Velocity, Renderable, PlayerInput, GameState, CreatureStats, HasVision
from processors import MovementSystem, RenderSystem, InputSystem, CombatSystem, PathfindingSystem, AISystem

from messagelog import MessageLog, Message
from gamemap import GameMap
import cProfile


def main() -> None:

    screen_width, screen_height = 100, 60
    map_width, map_height = 80, 50
    map_console = tcod.console.Console(map_width, map_height)
    sidebar_console = tcod.console.Console(screen_width - map_width,map_height)
    log_console = tcod.console.Console(screen_width, screen_height - map_height)

    game_map = GameMap(screen_width=map_width, screen_height=map_height)
    game_map.procgen(100, 7, 15)

    message_log = MessageLog()
    
   
    player = esper.create_entity(
        Position(game_map.rooms[0].center[0], game_map.rooms[0].center[1], 1),
        Renderable(char="@", color=(255, 255, 255), color_dark= (0,0,0)),
        PlayerInput(),
        CreatureStats(name='player', max_hp=100, current_hp=100, strength=6)
    )

    wolf = esper.create_entity(
        Position(game_map.rooms[1].center[0], game_map.rooms[1].center[1], 1),
        Renderable(char="w", color=(92, 73, 47), color_dark=(0,0,0)),
        CreatureStats(name='wolf', max_hp=60, current_hp=60, strength=5),
        HasVision(4, np.zeros((game_map.screen_width, game_map.screen_height)))
    )
    


#This seems a little bit unnecessary, making an esper object with one referenced component, but I thought it might be more consistent. Maybe improve later.
    game_state_entity = esper.create_entity(
        GameState(
            running=True,
            turn_passed=True
            )
    )

    game_state = esper.component_for_entity(game_state_entity, GameState)

    
    tileset = tcod.tileset.load_tilesheet(
        "Nice_curses_12x12.png", 16, 16, tcod.tileset.CHARMAP_CP437
    )



    with tcod.context.new(
        columns=screen_width,
        rows=screen_height,
        tileset=tileset,
        title="ECS Roguelike",
    ) as context:
        
        
       
        input_system = InputSystem(game_state=game_state, player=player, game_map=game_map)
       
        
        pathfinding_system = PathfindingSystem(game_map)
        esper.add_processor(pathfinding_system)
        ai_system = AISystem(game_map)
        esper.add_processor(ai_system)
        combat_system = CombatSystem(message_log)
        esper.add_processor(combat_system)
        movement_system = MovementSystem(map_width, map_height, game_map)
        esper.add_processor(movement_system)
        
        
        render_system = RenderSystem(game_map, map_console, sidebar_console, log_console, context, player, message_log)
        esper.add_processor(render_system)
        
        esper.process()
        
        while game_state.running:
            input_system.process()
            if game_state.turn_passed:
                #TEMPORARY BANDAID FIX
                #Instead of running esper.process every turn, we call the combat and movement systems twice so that the player moves before the enemies. Maybe in the future change this so there is a unique process for player movement and enemy movement? 
                #Without this fix, the enemy gets "attacks of opportunity" and can hit the player as they're moving away.
                combat_system.process()
                movement_system.process()
                pathfinding_system.process()
                ai_system.process()
                combat_system.process()
                movement_system.process()
                render_system.process()

                print(game_map.color_shift_map)

                
            

if __name__ == "__main__":
   main()