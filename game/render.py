from typing import *
import math
import asyncio

if TYPE_CHECKING:
    from . import entity


VIEW_RADIUS = 30
BUFFER_RADIUS = 10

# Map data must match
OCCLUSION_CHARS = {"▄", "▐", "█"}
OCCLUDED_CHAR = "."
WALL_CHAR = "W"
TRAVERSABLE_CHARS = {" "}

# Derived
ARC_RADIANS = math.pi / (4 * VIEW_RADIUS)
ARC_FULL_REV = 8 * VIEW_RADIUS


class Map:

    lines = 0
    columns = 0

    def __init__(self, file: "TextIOWrapper"):
        self._orig = self._data = tuple(row.strip() for row in file.readlines())[::-1]
        self._nrows = len(self._data)
        self._ncols = len(self._data[0])

    @property
    def data(self):
        return self._data

    @property
    def nrows(self):
        return self._nrows
    
    def update_data(self, clients):
        tmp = [list(row) for row in self._orig]
        
        for client in clients.values():
            y, x = client["pos"]
            char = client["reprchar"]

            tmp[y][x] = char
        
        self._data = [ "".join(row) for row in tmp ]


    @property
    def ncols(self):
        return self._ncols
    
    
    def map_chunk(self, near_row, near_col) -> List[List[str]]:
        NROWS = Map.lines
        NCOLS = Map.columns

        for i in range(self._nrows // NROWS):
            if i * NROWS <= near_row < (i+1) * NROWS:
                row_start, row_end = (i * NROWS, (i+1) * NROWS)
                break
        else:
            row_start, row_end = (self._nrows - NROWS, self._nrows)
        
        for j in range(self._ncols // NCOLS):
            if j * NCOLS <= near_col < (j+1) * NCOLS:
                col_start, col_end = (j * NCOLS, (j+1) * NCOLS)
                break
        else:
            col_start, col_end = (self._ncols - NCOLS, self._ncols)
    
        return [
            list(self.data[i][col_start:col_end])
            for i in range(row_start, row_end)
        ]


class View:

    def __init__(self, pos: Tuple[int, int], mapdata: Map):
        NROWS, NCOLS = Map.lines, Map.columns
        row, col = pos

        if row + NROWS > mapdata.nrows:
            row = mapdata.nrows - NROWS
        if col + NCOLS > mapdata.ncols:
            col = mapdata.ncols - NCOLS

        
        assert VIEW_RADIUS * 2 <= NROWS, "Bigger terminal needed" 
        assert VIEW_RADIUS * 2 <= NCOLS, "Bigger terminal needed"

        if not row:
            free_move_row_offset = 0
            free_move_row_size = NROWS - VIEW_RADIUS
        elif row + NROWS == mapdata.nrows:
            free_move_row_offset = VIEW_RADIUS
            free_move_row_size = NROWS - VIEW_RADIUS
        else:
            free_move_row_offset = VIEW_RADIUS
            free_move_row_size = NROWS - VIEW_RADIUS * 2
        
        if not col:
            free_move_col_offset = 0
            free_move_col_size = NCOLS - VIEW_RADIUS
        elif col + NCOLS == mapdata.ncols:
            free_move_col_offset = VIEW_RADIUS
            free_move_col_size = NCOLS - VIEW_RADIUS
        else:
            free_move_col_offset = VIEW_RADIUS
            free_move_col_size = NCOLS - VIEW_RADIUS * 2

        self.free_move_offset = (free_move_row_offset, free_move_col_offset)
        self.free_move_size = (free_move_row_size, free_move_col_size)
        self.data = [
            [mapdata.data[i][j] for j in range(col, col + NCOLS)]
            for i in range(row, row + NROWS)
        ]


def apply_occlusion_layer(chunk: List[List[str]], pos: Tuple[int, int]):
    """
    Implement visual occlusion from the given position. Objects can only be seen
    if they are not blocked and within VIEW_RADIUS
    """
    
    def validate_pos(pos):
        row, col = pos
        max_row, max_col = len(chunk), len(chunk[0])
        return 0 <= row < max_row and 0 <= col < max_col   
    
    row, col = pos
    render_set = set()
    for s in range(ARC_FULL_REV):
        theta = s * ARC_RADIANS
        i_row, i_col = row, col
        for i in range(VIEW_RADIUS):            
            i_row += math.sin(theta)
            i_col += math.cos(theta)
            
            (r, c) = textpos = math.floor(i_row), math.floor(i_col)

            if not validate_pos(textpos):
                break

            render_set.add(textpos)
            if chunk[r][c] in OCCLUSION_CHARS:
                break
    
    for i in range(len(chunk)):
        for j in range(len(chunk[0])):
            if (i, j) not in render_set:
                chunk[i][j] = OCCLUDED_CHAR


class Camera:

    def __init__(self, entity: "entity.Entity", map: Map):
        self.bound_entity = entity
        self.bound_map = map
        self.position = [0, 0]
        self._free_move_offset = [0, 0]
        
    
    def _view(self):
        NROWS, NCOLS = Map.lines, Map.columns
        row, col = self.position
        return [
                [self.bound_map.data[i][j] for j in range(col, col + NCOLS)]
                for i in range(row, row + NROWS)
        ]

    def __iter__(self):
        while True:
            self.current_view = self._view()
            yield self.current_view

    def bind(self, entity):
        self.bound_entity = entity

    
    def relative_position(self, pos: Tuple[int, int], boundcheck=False):
        row, col = pos
        r_row, r_col = row - self.position[0], col - self.position[1]
        if boundcheck and not (0 <= r_row < len(self.current_view) and 0 <= r_col < len(self.current_view[0])):
            return None
        return int(r_row), int(r_col)
    

    async def update_box(self):
        while True:
            NROWS, NCOLS =  Map.lines, Map.columns
            row, col = self.position

            if row + NROWS > self.bound_map.nrows:
                row = self.bound_map.nrows - NROWS
            if col + NCOLS > self.bound_map.ncols:
                col = self.bound_map.ncols - NCOLS

            assert BUFFER_RADIUS * 2 <= NROWS, "Bigger terminal needed" 
            assert BUFFER_RADIUS * 2 <= NCOLS, "Bigger terminal needed"

            if not row:
                free_move_row_offset = 0
                free_move_row_size = NROWS - BUFFER_RADIUS
            elif row + NROWS == self.bound_map.nrows:
                free_move_row_offset = BUFFER_RADIUS
                free_move_row_size = NROWS - BUFFER_RADIUS
            else:
                free_move_row_offset = BUFFER_RADIUS
                free_move_row_size = NROWS - BUFFER_RADIUS * 2
            
            if not col:
                free_move_col_offset = 0
                free_move_col_size = NCOLS - BUFFER_RADIUS
            elif col + NCOLS == self.bound_map.ncols:
                free_move_col_offset = BUFFER_RADIUS
                free_move_col_size = NCOLS - BUFFER_RADIUS
            else:
                free_move_col_offset = BUFFER_RADIUS
                free_move_col_size = NCOLS - BUFFER_RADIUS * 2

            self._free_move_offset = (free_move_row_offset, free_move_col_offset)
            self.free_move_size = (free_move_row_size, free_move_col_size)
            await asyncio.sleep(1/60)
    


    @property
    def free_move_position(self):
        return (
            self.position[0] + self._free_move_offset[0],
            self.position[1] + self._free_move_offset[1],
        )
    

    def entity_in_free_move(self):
        b_row, b_col = self.free_move_position
        b_row_end, b_col_end = b_row + self.free_move_size[0], b_col + self.free_move_size[1]
        return b_row <= self.bound_entity.row < b_row_end and b_col <= self.bound_entity.row < b_col_end
    
    
    def entity_free_move_offset(self):

        b_row, b_col = self.free_move_position
        b_row_end, b_col_end = b_row + self.free_move_size[0], b_col + self.free_move_size[1]
        
        if b_row <= self.bound_entity.row < b_row_end and b_col <= self.bound_entity.col < b_col_end:
            return 0, 0
        
        if self.bound_entity.row < b_row:
            row_offset =  self.bound_entity.row - b_row
            assert row_offset < 0
        elif self.bound_entity.row > b_row_end:
            row_offset = self.bound_entity.row - b_row_end
            assert row_offset > 0 
        else:
            row_offset = 0
        
        if self.bound_entity.col < b_col:
            col_offset =  self.bound_entity.col - b_col
            assert col_offset < 0
        elif self.bound_entity.col > b_col_end:
            col_offset = self.bound_entity.col - b_col_end
            assert col_offset > 0
        else:
            col_offset = 0
        
        return row_offset, col_offset


    
    def relative_entity_position(self):
        return self.bound_entity.row - self.position[0], self.bound_entity.col - self.position[1]


    async def update_position(self):
        while True:
            try:
                row_offset, col_offset = self.entity_free_move_offset()
                self.position[0] += row_offset
                self.position[1] += col_offset
                await asyncio.sleep(1/30)
            except:
                exit()
