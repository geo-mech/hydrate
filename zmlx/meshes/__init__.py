"""Mesh3 网格生成工具（长方体、矩形、圆形三角形网格）.

Modified by Claude, 2026-08-12

⚠️ **本目录 2026-10-16 由 ``zmlx.mesh`` 改名为 ``zmlx.meshes``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``demos`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``Mesh3 网格生成工具``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.mesh`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.mesh`` 改为 ``zmlx.meshes``.
"""
from zmlx.exts import SelfPath
from zmlx.meshes._clean import remove_orphan_faces, remove_orphan_links, remove_orphan_nodes
from zmlx.meshes._cube import create_cube_mesh
from zmlx.meshes._filter import filter_mesh
from zmlx.meshes._rect import create_rect_mesh

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
