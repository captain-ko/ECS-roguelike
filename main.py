import tcod
import esper

from components import Position, Velocity, Renderable, PlayerInput, GameState, CreatureStats
from processors import MovementSystem, RenderSystem, InputSystem, CombatSystem, PathfindingSystem

from gamemap import GameMap
import cProfile


def main() -> None:
    screen_width, screen_height = 80, 50
    console = tcod.console.Console(screen_width, screen_height)
    
    game_map = GameMap(screen_width=screen_width, screen_height=screen_height)
    game_map.procgen(100, 7, 15)
   
    player = esper.create_entity(
        Position(game_map.rooms[0].center[0], game_map.rooms[0].center[1]),
        Renderable(char="@", color=(255, 255, 255), color_dark= (0,0,0)),
        PlayerInput(),
        CreatureStats(max_hp=10, current_hp=10, strength=6)
    )

    orc = esper.create_entity(
        Position(game_map.rooms[1].center[0], game_map.rooms[1].center[1]),
        Renderable(char="o", color=(106, 191, 80), color_dark=(0,0,0)),
        CreatureStats(max_hp=60, current_hp=60, strength=5)
    )
    

    game_state_entity = esper.create_entity(
        GameState(
            running=True
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
        
        
       
        esper.add_processor(InputSystem(game_state, player))
        esper.add_processor(CombatSystem())
        esper.add_processor(MovementSystem(screen_width, screen_height, game_map))
        esper.add_processor(PathfindingSystem(game_map))
        esper.add_processor(RenderSystem(game_map, console, context))
        

        
        while game_state.running:
            esper.process()


if __name__ == "__main__":
   main()