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
