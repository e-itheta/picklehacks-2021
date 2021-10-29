from typing import *
import math

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
        self._data = tuple(row.strip() for row in file.readlines())[::-1]
        self._nrows = len(self._data)
        self._ncols = len(self._data[0])

    @property
    def data(self):
        return self._data

    @property
    def nrows(self):
        return self._nrows
    
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

    