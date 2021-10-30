from typing import *

if TYPE_CHECKING:
    from pickle import render


_id = 0
def _next_id():
    global _id
    yield _id
    _id += 1

nextid = _next_id()


class BaseEntity:

    def __init__(self, reprchar, name):
        self.reprchar = reprchar
        self.name = name
        self.position = [0.0, 0.0]
        self.id = next(nextid)
     
    def __repr__(self):
        return f"<{type(self).__name__} : {self.id}>('{self.reprchar}', '{self.name}')"


    @property
    def row(self):
        return int(self.position[0])
    
    @property
    def col(self):
        return int(self.position[1])


    def render(self, camera: "render.Camera"):
        view = camera.current_view
        pos = camera.relative_position(self.position)
        if pos is None:
            return
        y, x = pos
            
        # TODO copy into camera

        view[y][x] = self.reprchar


class Entity(BaseEntity):

    def __init__(self, reprchar, name):
        super().__init__(reprchar, name)
        self.throttle = [0, 0]


class Player(Entity):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        