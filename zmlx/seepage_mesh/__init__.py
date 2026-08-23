"""
渗流网格

Modified by Claude, 2026-08-12
"""


from zmlx.exts import SelfPath
from zmlx.seepage_mesh.cube import (
    create_cube, create_xy, create_xz, create_xyz,
    create_cube as create_cube_seepage_mesh)
from zmlx.seepage_mesh.cylinder import create_cylinder
from zmlx.seepage_mesh.edit import add_cell_face
from zmlx.seepage_mesh.edit import scale as seepage_mesh_rescale
from zmlx.seepage_mesh.edit import (
    swap_yz, swap_xy, swap_xz,
    swap_yz as seepage_mesh_swap_yz,
    swap_xy as seepage_mesh_swap_xy,
    swap_xz as seepage_mesh_swap_xz)
from zmlx.seepage_mesh.wellbore import create_wellbore

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
