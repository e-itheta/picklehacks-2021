import websockets
import asyncio
import json

clients = {}
clients_ws = set()

idcounter = 0

def next_pos():
    while True:
        yield [2, 2]

def next_reprchar():
    while True:
        yield "@"

# Initialize the generator that produces the next spawn position
pos_gen = next_pos()

# Initialize the generator that produces the next 
char_gen = next_reprchar()

async def handler(ws, path):
    global idcounter
    print("client connected")

    tmp = idcounter

    # store player attributes keyed to id. this is the global state of the
    # multiplayer session
    init = clients[idcounter] = {
        "pos": next(pos_gen),
        "reprchar": next(char_gen),
        "id": tmp
    }

    await ws.send(json.dumps(init))



    clients_ws.add(ws)

    idcounter += 1


    try:
        async for message in ws:
            position = json.loads(message)
            # Copy in position data
            clients[tmp]["pos"][:] = position
            print(f"{tmp} - {clients[tmp]['reprchar']} - {position}")
    finally:
        del clients[tmp]
        clients_ws.remove(ws)
        print("client disconnected")
    




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
loop.run_forever()