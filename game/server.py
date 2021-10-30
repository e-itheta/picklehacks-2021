import websockets
import asyncio

clients = {}

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

    tmp = idcounter

    # store player attributes keyed to id
    clients[idcounter] = {
        "ws": ws,
        "pos": next(pos_gen) 
        "reprchar": 
    }
    
    pass


async def main():
    async with websockets.serve(handler, "localhost", 10000) as server:
        await asyncio.Future()


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()