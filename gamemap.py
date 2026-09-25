from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from random import randint
import collections
import random
from scipy.spatial import Delaunay
from scipy.sparse.csgraph import minimum_spanning_tree
import tcod



@dataclass
class TileType:
    char: str
    light: tuple[int, int, int]
    dark: tuple[int, int, int]
    bg: tuple[int,int,int]
    bg_dark: tuple[int, int, int]
    walkable: bool

wall = TileType(char="^", light=(255,255,255), dark=(33, 71, 10), bg=(33, 71, 10), bg_dark=(78, 74, 99), walkable=False)
floor = TileType(char=" ", light=(185, 28, 199), dark=(185, 28, 199), bg=(70, 133, 53), bg_dark=(146, 139, 179), walkable=True)



class RectangularRoom:
    def __init__(self, x, y, width, height):
        self.x1 = x
        self.y1 = y
        self.width = width
        self.height = height
        self.tiles = np.full((self.width, self.height), fill_value=wall, dtype=object)
        self.tiles[1:width-1,1:height-1] = floor
        self.x2 = x + width - 1
        self.y2 = y + height - 1

        self.center: tuple[int, int] = (self.x1 + self.x2)//2, (self.y1 + self.y2)//2

        self.north = [(x, self.y1) for x in range(self.x1 + 1, self.x2)]
        self.east = [(self.x2, y) for y in range(self.y1 + 1, self.y2)]
        self.south = [(x, self.y2) for x in range(self.x1 + 1, self.x2)]
        self.west = [(self.x1, y) for y in range(self.y1 + 1, self.y2)]

    def make_doors(self, game_map: GameMap, max_doors: int) -> None:

        candidate_doors = []

        
        for position in self.north:
            x, y = position
            if game_map.tiles[x, y - 1] == floor:
                candidate_doors.append(position)
        
        for position in self.east:
            x, y = position
            if game_map.tiles[x + 1, y] == floor:
                candidate_doors.append(position)
        
        for position in self.south:
            x, y = position
            if game_map.tiles[x, y + 1] == floor:
                candidate_doors.append(position)
        
        for position in self.west:
            x, y = position
            if game_map.tiles[x - 1, y] == floor:
                candidate_doors.append(position)

        if not candidate_doors:
            return

        for i in range(randint(1,max_doors)):
            game_map.tiles[candidate_doors[randint(0, len(candidate_doors) - 1)]] = floor

            

@dataclass
class Level:
    depth: int
    tilemap: np.array
    transparency_map: np.array
    explored_map: np.array
    color_shift_map: np.array
    rooms: list[RectangularRoom]

class GameMap:
    def __init__(self, screen_width, screen_height):
        self.screen_height = screen_height
        self.screen_width = screen_width
        
        self.tiles = np.full((screen_width, screen_height), fill_value=wall, dtype=object)
        self.rooms: list[RectangularRoom] = []
        self.transparency_map = np.full((screen_width, screen_height), fill_value=True, dtype=bool)
        self.explored = np.zeros((screen_width, screen_height), dtype=bool)
        self.current_floor = 1
        self.levels: dict[int, Level] = {}

        self.color_shift_map = np.zeros((screen_width,screen_height, 3), dtype=np.uint8)

    
    def carve_from(self, start_x: int, start_y: int, visited: np.ndarray, rooms: list[RectangularRoom]):
        stack = [(start_x, start_y)]
        visited[(start_x, start_y)] = True
        self.tiles[(start_x, start_y)] = floor

        while stack:
            x, y = stack[-1]

            neighbors = []
            for dx, dy in [(2,0), (-2,0), (0,2), (0,-2)]:
                nx, ny = x + dx, y + dy

                if not (1 <= nx < self.screen_width - 1 and 1 <= ny < self.screen_height - 1):
                    continue

                if visited[(nx, ny)]:
                    continue

                in_room = False
                for room in rooms:
                    if room.x1 <= nx <= room.x2 and room.y1 <= ny <= room.y2:
                        in_room = True
                        break
                
                if in_room:
                    continue

                neighbors.append((nx, ny))

            if not neighbors:
                stack.pop()
                continue

            nx, ny = neighbors[randint(0, len(neighbors) - 1)]

            wall_x, wall_y = (x + nx) // 2, (y + ny) // 2
            self.tiles[wall_x, wall_y] = floor
            self.tiles[nx, ny] = floor
            visited[nx, ny] = True

            stack.append((nx, ny))

    def tunnel_between(self, start: tuple[int, int], end: tuple[int, int]):
        x1, y1 = start
        x2, y2 = end

        corner_x, corner_y = (x1, y2) if random.random() < .5 else (x2, y1)

        for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)):
            self.tiles[x, y] = floor
        for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)):
            self.tiles[x, y] = floor


    #NEW DELAUNAY METHOD
    def hallway_gen(self):
        

        #This array looks like [[x1, y1], [x2, y2], ...]
        centers = np.array([room.center for room in self.rooms])
        print("CENTERS = " + str(centers))

        #Delaunay returns an object that has a list of simplexes [a, b, c] where a, b, and c are the indexes of centers related by the algorithm
        tri = Delaunay(centers)
        print("TRI = " + str(tri))

        #We need an nxn matrix so that we can build an adjacency matrix
        n = len(centers)
        print("n = " + str(n))
        graph = np.zeros((n, n))
        print("GRAPH = " + str(graph))

        #For every simplex, grab all combinations of any two elements and calculate the distance between them. Put these in the adjacency matrix (which is of course symmetric about the diagonal)
        for simplex in tri.simplices:
            print("SIMPLEX = " + str(simplex))
            for i, j in [(0,1), (1,2), (0,2)]:
                a, b = simplex[i], simplex[j]
                dist = np.linalg.norm(centers[a] - centers[b])
                graph[a][b] = dist
                graph[b][a] = dist
        
        print("GRAPH = " + str(graph))

        #Now that we have an adjacency matrix with proper weights on the edges to find the MST. NOTE: THE MST NOW IS A CSR MATRIX, WHICH LOOKS LIKE (Tuple(int, int), Value) in each row, with all 0s removed
        MST = minimum_spanning_tree(graph)
        print("MST = " + str(MST))


        #We grab the complement of the MST and random sample it
        leftover = graph - MST.toarray()
        

        print("LEFTOVER = " + str(leftover) + "\n")
        
        #leftover is an adjacency matrix with 0s, so we use .nonzero() to remove non-edges and to get two arrays, one which lists the nonzero row indices and one which lists the nonzero column indices. These are then unpacked by the *, zipped together and repacked into a list for the sample.
        extra_connections = random.sample(list(zip(*leftover.nonzero())), int(len(leftover) * .15))

        print("EXTRA CONNECTIONS = " + str(extra_connections) + " \n")

        #Note that even though MST is in CRS form and has no zeros, the nonzero function is still used to grab the row and column indices. There may be a more elegant way to do this...
        paths = list(zip(*MST.nonzero())) + extra_connections

        for a, b in paths:
            self.tunnel_between(
                (int(centers[a][0]), int(centers[a][1])),
                (int(centers[b][0]), int(centers[b][1]))
            )


    def floodcheck(self):
        visited = np.full(self.tiles.shape, False, dtype=bool)
        regions = []
        
        for position, tile in np.ndenumerate(self.tiles):
            if visited[position]:
                continue
            if tile != floor:
                continue
            visited[position] = True
            stack = collections.deque()
            stack.append(position)
            region = []
            while stack:
                x, y = stack.popleft()
                region.append((x, y))
                
                for dx, dy in [(1,0), (0,1), (-1, 0), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx <= self.screen_width) and (0 <= ny <= self.screen_height):
                        continue
                    if visited[nx, ny]:
                        continue
                    if self.tiles[nx, ny] != floor:
                        continue
                    visited[nx, ny] = True
                    stack.append((nx, ny))


            regions.append(region)
        
        return regions

    def procgen(self, room_tries: int, min_room_size: int, max_room_size: int):
        for i in range(room_tries):
            overlap = False

            width = random.randrange(min_room_size, max_room_size, 2)
            height = random.randrange(min_room_size, 
            max_room_size, 2)

            max_x = self.screen_width - width - 1
            max_y = self.screen_height - height - 1

            if max_x < 1 or max_y < 1:
                continue

            x = random.randrange(2, max_x, 2)
            y = random.randrange(2, max_y, 2)

            new_room = RectangularRoom(x=x, y=y, width=width, height=height)

            for room in self.rooms:
                if new_room.x1 < room.x2 and new_room.x2 > room.x1 and new_room.y1 < room.y2 and new_room.y2 > room.y1:
                    overlap = True
                    break
            
            if overlap:
                continue

            self.tiles[new_room.x1: new_room.x2 + 1, new_room.y1: new_room.y2 + 1] = new_room.tiles[0: width, 0: height]

            self.rooms.append(new_room)

        self.hallway_gen()
        
        for x in range(self.screen_width):
            for y in range(self.screen_height):
                if self.tiles[(x, y)] == wall:
                    self.transparency_map[(x, y)] = False

                self.color_shift_map[x,y] = (np.random.randint(0,60),np.random.randint(0,60),np.random.randint(0,60))
           

        

        

    def floor_change(self, z_move):


        self.levels[self.current_floor] = Level(self.current_floor, self.tiles, self.transparency_map, self.explored,self.color_shift_map, self.rooms)

        self.tiles = np.full((self.screen_width, self.screen_height), fill_value=wall, dtype=object)
        self.rooms: list[RectangularRoom] = []
        self.transparency_map = np.full((self.screen_width, self.screen_height), fill_value=True, dtype=bool)
        self.current_floor = self.current_floor + z_move
        self.explored = np.zeros((self.screen_width, self.screen_height), dtype=bool)
        self.color_shift_map = np.zeros((self.screen_width,self.screen_height, 3), dtype=np.uint8)
        


        if self.current_floor in self.levels:
                self.tiles: np.array = self.levels[self.current_floor].tilemap
                self.transparency_map: np.array = self.levels[self.current_floor].transparency_map
                self.rooms: list[RectangularRoom] = self.levels[self.current_floor].rooms
                self.explored: np.array = self.levels[self.current_floor].explored_map
                self.color_shift_map: np.array = self.levels[self.current_floor].color_shift_map


        else: self.procgen(100,7,15)
        
    

            
    



        

