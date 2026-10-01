import esper
from components import Item, Position, WeaponStats, ArmorStats, Renderable
import json
import random

class Spawner():
    def __init__(self):
        with open('items.json', encoding = 'utf-8') as file:
                    self.items = json.load(file)
        self.common_items = []
        for item in self.items:
             self.common_items.append(item['name'])
             
        

    def random_item_spawn(self, rarity, x, y, z):
         match rarity:
              case 'common':
                   self.spawn_item(item_name=random.choice(self.common_items), x=x, y=y, z=z)
    
    def spawn_item(self, item_name, x, y, z):
        blueprint = next((item for item in self.items if item['name'] == item_name), None)

        if blueprint != None:
            new_item = esper.create_entity(
                Item(name=item_name, item_type=blueprint['type'], value=blueprint['value']),
                Position(x, y, z),
                Renderable(char=blueprint['char'], color=(255, 255, 255), color_dark= (0,0,0))
            )

            match esper.component_for_entity(new_item, Item).item_type:
                case 'weapon':
                    esper.add_component(new_item, WeaponStats(strength_bonus=blueprint['power']))

                case 'armor':
                    esper.add_component(new_item, ArmorStats(armor_rating=blueprint['armor rating']))