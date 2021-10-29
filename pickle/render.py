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

    