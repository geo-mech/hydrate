from zml import FractureNetwork, SeepageMesh


def create_seepage_mesh(
        network: FractureNetwork, cell_vol, face_area, face_dist, z_coord=0.0):
    """根据裂缝网络创建渗流网格(单层的渗流网络)。

    Args:
        face_dist: Face的长度属性
        face_area: Face的面积
        cell_vol: Cell的体积
        network (FractureNetwork): 裂缝网络对象
        z_coord: network所在的z坐标

    Returns:
        SeepageMesh: 生成的渗流网格对象
    """
    mesh = SeepageMesh()

    for fracture in network.fractures:  # 添加单元
        assert isinstance(fracture, FractureNetwork.Fracture)
        cell = mesh.add_cell()
        x, y = fracture.center
        cell.pos = [x, y, z_coord]  # 三维坐标
        cell.vol = cell_vol

    for vertex in network.vertexes:  # 添加面
        assert isinstance(vertex, FractureNetwork.Vertex)
        for i0 in range(vertex.fracture_number):
            for i1 in range(i0 + 1, vertex.fracture_number):
                face = mesh.add_face(
                    vertex.get_fracture(i0).index,
                    vertex.get_fracture(i1).index
                )
                face.dist = face_dist
                face.area = face_area

    return mesh
