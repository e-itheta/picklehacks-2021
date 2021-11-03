import websockets
import asyncio
import json
import random
import math
from typing import *

'''

class InterfaceType(type): 

  def __init__(self, *args, **kwargs):
    annot = {}
    for base in self.__mro__[::1]:
      annot.update(getattr(base, "__annotations__", {}))

    self.anotations = annot

    def create_getset(name):
        def getter(obj):
            if name in obj:
                return obj[name]
            return None

        def setter(obj, value):
            obj[name] = value

        return getter, setter

    for name in annot.keys():
        setattr(self, name, property(*create_getset(name)))
    
    


class Interface(dict, metaclass=InterfaceType):

  if __debug__:
    def __getattr__(self, name):
      if name not in type(self)._annotations:
        raise AttributeError(f"{name} not defined in this interface")
      return super().__getattr__(name)

    def __setattr__(self, name, value):
      if name not in type(self)._annotations:
        raise AttributeError(f"{name} not defined in this interface")
      return super().__setattr__(name, value)


class Entity(Interface):
    id: int
    pos: List[int, int]
    reprchar: str # The character drawn to the screen


class Ghost(Entity):
    pass


class Items(Entity):
    owner_id: int
    on_ground: bool


class Player(Entity):
    petrified: bool
    inventory: List[Items]
'''


# if ghost within this radius, player gets more petrified
PETRIFIED_RADIUS = 4

# if more than 2 player within radius, repel ghosts
REPEL_RADIUS = 10

# If this count of ghost within PETRIFIED radius is reached, player can't move
GHOST_COUNT_FOR_PETRIFICATION = 4

# Perhaps better named "Entities". Stores all entities in { id: { state } } pair
clients = {}

clients_ws = set()
player_ids = set()
idcounter = 0


def next_pos():
    """
    Generate next spawn location for player
    """
    while True:
        yield [2, 2]

def next_reprchar():
    """
    Generate next repr char for player
    """
    while True:
        for character in [ "@", "#", "^", "%", "+", "?", "!", "&", "$" ]:
              yield character


def next_id():
    """
    Generate unique entity id
    """
    global idcounter
    while True:
        yield idcounter
        idcounter += 1



def entities_within_radius(origin: Tuple[int, int], radius: float) -> List[int]:
    """
    Return a sorted list of entity ids within <radius> of <origin> 
    """

    return sorted(
        (id for id in clients if distance(origin, clients[id]["pos"]) <= radius),
        key = lambda x: distance(origin,clients[id]["pos"])
    )

def distance(p1, p2):
    y1, x1 = p1
    y2, x2 = p2
    return math.sqrt((y1 - y2)**2 + (x1 - x2)**2)

def entity_distance(id1, id2):
    return distance(clients[id1]["pos"], clients[id2]["pos"])


def closest_player(entity_id) -> dict:
    min_id = min(player_ids, key=lambda x: entity_distance(entity_id, x))
    return clients[min_id]

# Next id
id_gen = next_id()

# Initialize the generator that produces the next spawn position
pos_gen = next_pos()

# Initialize the generator that produces the next 
char_gen = next_reprchar()

item_id = next(id_gen)

clients[ item_id ] = {
    "reprchar": "3",
    "pos":[4, 4],
    "type": "item",
    "id": item_id,
}


def count_ghosts_near_id(entity_id):
    count = 0
    for ghost_id in clients:
        if ghost_id not in player_ids and ghost_id != entity_id:
            if entity_distance(entity_id, ghost_id) < PETRIFIED_RADIUS:
                count += 1
    return count

def count_players_near_id(entity_id:int):
    count = 0
    for player_id in player_ids:
        if player_id != entity_id:
            if entity_distance(entity_id, player_id) < REPEL_RADIUS:
                count += 1
    return count


async def update_player_petrification_state(entity_id):
    """Count the number of ghosts near entity and """
    while True:
        if entity_id in player_ids and entity_id in clients:
            if count_ghosts_near_id(entity_id) >= GHOST_COUNT_FOR_PETRIFICATION:
                clients[entity_id]["petrified"] = True
            else:
                clients[entity_id]["petrified"] = False
            await asyncio.sleep(1/10)
        else:
            break



async def handler(ws, path):
    print("client connected")

    id = next(id_gen)
    player_ids.add(id)

    # store player attributes keyed to id. this is the global state of the
    # multiplayer session

    reprchar = next(char_gen)

    init = clients[id] = {
        "pos": next(pos_gen),
        "reprchar": reprchar,
        "id": id,
        "petrified": False,
        "items": []
    }

    clients_ws.add(ws)
    
    loop.create_task(update_player_petrification_state(id))
    await ws.send(json.dumps(init))

    try:
        async for message in ws:
            position = json.loads(message)
            # Copy in position data
            if clients[id]["petrified"]:
                clients[id]["reprchar"] = "X"
            else:
                clients[id]["reprchar"] =  reprchar
            
            clients[id]["pos"][:] = position
            #print(f"{id} - {clients[id]['reprchar']} - {position}")
    finally:
        del clients[id]
        player_ids.remove(id)
        clients_ws.remove(ws)
        print("client disconnected")
    


async def generate_ghosts():

    async def update_ghost_position(id):
        while True:
            if id in clients:
                ghost = clients[id]
                y, x = ghost["pos"]
                # Initialize as no movement
                dy, dx = 0, 0 
                if player_ids:

                    # Move ghost towards closest player
                    closest = closest_player(id)
                    player_y, player_x = closest["pos"]

                    if player_y - y < 0:
                        dy = -1
                    elif player_y - y > 0:
                        dy = +1
                    
                    if player_x - x < 0:
                        dx = -1
                    elif player_x - x > 0:
                        dx = +1

                    if count_players_near_id(closest["id"]) > 0:  # if the players are grouped, flip direction of ghost movement (repel)                    
                        dx = dx * -1
                        dy = dy * -1

                # dy, dx = random.randint(-1, 1), random.randint(-1, 1)
                if 0 < y + dy < 160:
                    ghost["pos"][0] = y + dy
                if 0 < x + dx < 300:
                    ghost["pos"][1] = x + dx    
            else:
                break
            await asyncio.sleep(1/5)

    async def randomized_movement(id):
        """Apply brownian motion to ghosts so they don't stack on each other"""

        while True:
            if id in clients:
                ghost = clients[id]
                y, x = ghost["pos"]

                dy, dx = random.randint(-1, 1), random.randint(-1, 1)
                if 0 < y + dy < 160:
                    ghost["pos"][0] = y + dy
                if 0 < x + dx < 300:
                    ghost["pos"][1] = x + dx    
            else:
                break
            await asyncio.sleep(1/10)

    # Spawn 40 ghosts randomnly around map
    for _ in range(40):
        id = next(id_gen)
        clients[id] = {
            "pos": [random.randint(1, 159), random.randint(1, 299)],
            "reprchar": "\u01EA",
            "id": id
        }
        loop.create_task(update_ghost_position(id))
        loop.create_task(randomized_movement(id))

async def assign_item_to_player():
    while True:
        await asyncio.sleep(1/10)

        for item in list(clients):
            if clients[item].get("type", False) == "item":
                for player in player_ids:
                    if clients[player]["pos"] == clients[item]["pos"]:
                        clients[player]["items"].append(clients.pop(item))
                        break

async def main():
    async with websockets.serve(handler, "localhost", 10000) as server:
        while True:
            # Broadcast state of all clients
            message = json.dumps(clients)
            for client in clients_ws:
                await client.send(message)
            await asyncio.sleep(1/60)



loop = asyncio.get_event_loop()
loop.create_task(main())
loop.create_task(generate_ghosts())
loop.create_task(assign_item_to_player())
loop.run_forever()