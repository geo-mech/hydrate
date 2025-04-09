"""
用以交换mesh的坐标，从而实现不同的方向的模拟。

since 2025-2-6
"""
from zml import SeepageMesh


def add_cell_face(mesh: SeepageMesh, *, offset, pos=None, cell=None, vol=1.0,
                  area=1.0, length=1.0):
    """
    找到位于pos位置的Cell，并在pos + offset的位置添加新的Cell，并将此Cell的体积设置为vol。
    然后在两个Cell之间建立新的Face，并将新Face的面积设置为area，流动距离设置为length
    """
    if cell is None:
        cell = mesh.get_nearest_cell(pos=pos)

    if cell is None:
        return None

    index = cell.index  # 需要去连接的cell的id，提前找到，避免后续找到新添加的cell
    pos = cell.pos

    # 添加虚拟的cell
    cell = mesh.add_cell()
    cell.pos = [pos[i] + offset[i] for i in range(3)]
    cell.vol = vol

    # 添加虚拟的face来连接
    f = mesh.add_face(cell, mesh.get_cell(index))
    f.area = area
    f.length = length

    # 返回连接的index
    return index


def scale(mesh: SeepageMesh, factor: float, on_pos=True, on_area=True,
          on_vol=True, on_dist=True):
    """
    对渗流的网格进行缩放.
    """
    if on_pos or on_vol:
        for cell in mesh.cells:
            assert isinstance(cell, SeepageMesh.Cell)
            if on_pos:
                pos = [v * factor for v in cell.pos]
                cell.pos = pos
            if on_vol:
                cell.vol *= factor ** 3

    if on_area or on_dist:
        for face in mesh.faces:
            assert isinstance(face, SeepageMesh.Face)
            if on_area:
                face.area *= factor ** 2
            if on_dist:
                face.dist *= factor

    return mesh


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
