from zml import SeepageMesh


def add_cell_face(mesh: SeepageMesh, *, offset, pos=None, cell=None, vol=1, area=1, length=1):
    if cell is None:
        cell = mesh.get_nearest_cell(pos=pos)

    if cell is None:
        return
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
