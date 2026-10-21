"""
渗流网格

Modified by Claude, 2026-08-12

⚠️ **本目录 2026-10-16 由 ``zmlx.seepage_mesh`` 改名为 ``zmlx.seepage_meshes``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``demos`` / ``meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``渗流网格的构建与编辑``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.seepage_mesh`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.seepage_mesh`` 改为 ``zmlx.seepage_meshes``.
"""


from zmlx.exts import SelfPath
from zmlx.seepage_meshes.cube import (
    create_cube, create_xy, create_xz, create_xyz,
    create_cube as create_cube_seepage_mesh)
from zmlx.seepage_meshes.cylinder import create_cylinder
from zmlx.seepage_meshes.edit import add_cell_face
from zmlx.seepage_meshes.edit import scale as seepage_mesh_rescale
from zmlx.seepage_meshes.edit import (
    swap_yz, swap_xy, swap_xz,
    swap_yz as seepage_mesh_swap_yz,
    swap_xy as seepage_mesh_swap_xy,
    swap_xz as seepage_mesh_swap_xz)
from zmlx.seepage_meshes.wellbore import create_wellbore

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
