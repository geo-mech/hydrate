"""Mesh3 网格生成工具（长方体、矩形、圆形三角形网格）.

Modified by Claude, 2026-08-12
"""
from zmlx.exts import SelfPath
from zmlx.mesh._clean import remove_orphan_faces, remove_orphan_links, remove_orphan_nodes
from zmlx.mesh._cube import create_cube_mesh
from zmlx.mesh._filter import filter_mesh
from zmlx.mesh._rect import create_rect_mesh

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
