import websockets
import asyncio
import json
import random
import math

# if ghost within this radius, player gets more petrified
PETRIFIED_RADIUS = 4

# if more than 2 player within radius, repel ghosts
REPEL_RADIUS = 10

# If this count of ghost within PETRIFIED radius is reached, player can't move
GHOST_COUNT_FOR_PETRIFICATION = 4

clients = {}
clients_ws = set()
player_ids = set()
idcounter = 0

def next_pos():
    while True:
        yield [2, 2]

def next_reprchar():
    while True:
        yield "@"

def next_id():
    global idcounter
    while True:
        yield idcounter
        idcounter += 1

def distance(id1, id2):
    c1, c2 = clients[id1], clients[id2]
    y1, x1 = c1["pos"]
    y2, x2 = c2["pos"]
    return math.sqrt((y1 - y2)**2 + (x1 - x2)**2)

def closest_player(entity_id) -> dict:
    min_id = min(player_ids, key=lambda x: distance(entity_id, x))
    return clients[min_id]

# Next id
id_gen = next_id()

# Initialize the generator that produces the next spawn position
pos_gen = next_pos()

# Initialize the generator that produces the next 
char_gen = next_reprchar()

def count_ghosts_near_id(entity_id):
    count = 0
    for ghost_id in clients:
        if ghost_id not in player_ids and ghost_id != entity_id:
            if distance(entity_id, ghost_id) < PETRIFIED_RADIUS:
                count += 1
    return count

def count_players_near_id(entity_id):
    count = 0
    for player_id in player_ids:
        if player_id != entity_id:
            if distance(entity_id, player_id) < REPEL_RADIUS:
                count += 1
    return count


async def update_player_petrification_state(entity_id):

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
            print(f"{id} - {clients[id]['reprchar']} - {position}")
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

                    # if (count_players_near_id(closest) > 2):  # if the players are grouped, flip direction of ghost movement (repel)
                    #   dx = dx * -1
                    #   dy = dy * -1

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

    for _ in range(5):
        id = next(id_gen)
        clients[id] = {
            "pos": [2, id],
            "reprchar": "\u01EA",
            "id": id
        }
        await asyncio.sleep(1)
        loop.create_task(update_ghost_position(id))
        loop.create_task(randomized_movement(id))


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
loop.run_forever()