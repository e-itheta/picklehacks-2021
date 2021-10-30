import asyncio
import os
from . import render
from . import entity
import curses
import websockets

@curses.wrapper
def main(stdscr: curses.window):
    stdscr.nodelay(1)
    
    with open("maps/mst_campus.txt", "r") as fp:
            mapdata = render.Map(fp)


    player = entity.Entity("@", "Player")
    player.position[:] = 3, 3
    camera = render.Camera(player, mapdata)
    camera.position[:] = 0, 0

    async def _main():

        # Connect to Kevin's websocket server that he hosts
        async with websockets.connect("ws://e-itheta.com/picklehacks-2021") as ws:
            for game_map in camera:
                
                # Update map if terminal size changes
                render.Map.lines, render.Map.columns = stdscr.getmaxyx()

                keysym = stdscr.getch()
                if keysym != curses.ERR: # in non blocking mode, curses.ERR
                    keysym = chr(keysym) # cast to a string
                else:
                    keysym = ""

                if keysym == "w":
                    player.position[0] -= 1
                elif keysym == "s":
                    player.position[0] += 1
                elif keysym == "a":
                    player.position[1] -= 1
                elif keysym == "d":
                    player.position[1] += 1
                
                

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
                await asyncio.sleep(1/30)
    
    render.Map.columns,  render.Map.lines, = os.get_terminal_size()
    
    loop = asyncio.get_event_loop()
    loop.create_task(camera.update_box())
    loop.create_task(camera.update_position())
    loop.create_task(_main())
    loop.run_forever()


# a bit redundant but whatever
if __name__ == "__main__":
    main()