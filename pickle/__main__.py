import asyncio
import os
from . import render
from . import entity

def main():
    
    async def _main():
        with open("maps/mst_campus.txt", "r") as fp:
            mapdata = render.Map(fp)
        player = entity.Entity("@", "Player")
        player.position[:] = 2, 2
        camera = render.Camera(player, mapdata)
        camera.position[:] = 0, 0

        for game_map in camera:
            print("\033c")
            player_pos = camera.relative_entity_position()
            
            
            render.apply_occlusion_layer(game_map, player_pos)
            player.render(camera)

            print("\n".join("".join(r for r in row) for row in game_map), end="")
            await asyncio.sleep(1/30)
    
    render.Map.columns,  render.Map.lines, = os.get_terminal_size()
    
    loop = asyncio.get_event_loop()
    loop.create_task(_main())
    loop.run_forever()


# a bit redundant but whatever
if __name__ == "__main__":
    main()