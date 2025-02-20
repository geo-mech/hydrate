"""
用以交换mesh的坐标，从而实现不同的方向的模拟。

since 2025-2-6
"""


def swap_yz(mesh):
    """
    交换y和z坐标
    """
    for cell in mesh.cells:
        x, y, z = cell.pos
        cell.pos = [x, z, y]


def swap_xz(mesh):
    """
    交换x和z坐标
    """
    for cell in mesh.cells:
        x, y, z = cell.pos
        cell.pos = [z, y, x]


def swap_xy(mesh):
    """
    交换x和y坐标
    """
    for cell in mesh.cells:
        x, y, z = cell.pos
        cell.pos = [y, x, z]
