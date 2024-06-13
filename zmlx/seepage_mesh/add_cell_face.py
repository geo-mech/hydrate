from zml import SeepageMesh


def add_cell_face(mesh: SeepageMesh, pos, offset, vol=1, area=1, length=1):
    c = mesh.get_nearest_cell(pos=pos)

    if c is None:
        return
    index = c.index  # 需要去连接的cell的id，提前找到，避免后续找到新添加的cell

    # 添加虚拟的cell
    c = mesh.add_cell()
    c.pos = [pos[i] + offset[i] for i in range(3)]
    c.vol = vol

    # 添加虚拟的face来连接
    f = mesh.add_face(c, mesh.get_cell(index))
    f.area = area
    f.length = length

    # 返回连接的index
    return index
