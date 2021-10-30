import asyncio
import os
from . import render
from . import entity
import curses
import websockets
import json

@curses.wrapper
def main(stdscr: curses.window):
    stdscr.nodelay(1)
    
    with open("maps/mst_campus.txt", "r") as fp:
            mapdata = render.Map(fp)


    player = entity.Entity("@", "Player")
    player.position[:] = 3, 3
    camera = render.Camera(player, mapdata)
    camera.position[:] = 0, 0


    async def update_frame(ws):
        async for message in ws:
            data = json.loads(message)

            mapdata.update_data(data)
            

    async def _main():

        # Connect to Kevin's websocket server that he hosts
        async with websockets.connect("ws://e-itheta.com/picklehacks-2021") as ws:

            #Get entity data from server
            message = json.loads(await ws.recv())
            player.position[:] = message["pos"]
            player.reprchar = message["reprchar"]

            loop.create_task(update_frame(ws))

            for game_map in camera:
                
                # Update map if terminal size changes
                render.Map.lines, render.Map.columns = stdscr.getmaxyx()
                keysym = stdscr.getch()
                if keysym != curses.ERR: # in non blocking mode, curses.ERR
                    keysym = chr(keysym) # cast to a string
                else:
                    keysym = ""
                
                last_pos = list(player.position)

                # Update player position in 4 possible directions wasd
                if keysym == "w":
                    candidate = player.position[0] - 1
                    if mapdata.data[candidate][player.position[1]] in render.TRAVERSABLE_CHARS: # determine whether candidate position is legal, if not do nothing
                        player.position[0] -= 1
                elif keysym == "s":
                    candidate = player.position[0] + 1
                    if mapdata.data[candidate][player.position[1]] in render.TRAVERSABLE_CHARS:
                        player.position[0] += 1
                elif keysym == "a":
                    candidate = player.position[1] - 1
                    if mapdata.data[player.position[0]][candidate] in render.TRAVERSABLE_CHARS:
                        player.position[1] -= 1
                elif keysym == "d":
                    candidate = player.position[1] + 1
                    if mapdata.data[player.position[0]][candidate] in render.TRAVERSABLE_CHARS:
                        player.position[1] += 1
                
                if last_pos != player.position:
                    await ws.send(json.dumps(player.position))

                
                player_pos = camera.relative_entity_position()
                

                render.apply_occlusion_layer(game_map, player_pos)
                player.render(camera)
                stdscr.erase()
                for row in game_map:
                    try:
                        stdscr.addstr("".join(row))
                    except:
                        pass
                
                
                stdscr.refresh()
                await asyncio.sleep(1/60)
    
    render.Map.columns,  render.Map.lines, = os.get_terminal_size()
    
    loop = asyncio.get_event_loop()
    loop.create_task(camera.update_box())
    loop.create_task(camera.update_position())
    loop.create_task(_main())
    loop.run_forever()


# a bit redundant but whatever
if __name__ == "__main__":
    main()