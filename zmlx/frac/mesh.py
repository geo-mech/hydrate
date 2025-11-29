from zmlx.alg.base import clamp
from zmlx.exts.base import FractureNetwork, SeepageMesh, Coord3, Array3


def create_mesh(
        network: FractureNetwork, *, coord=None, height=None, thick=None,
        lmin=None, lmax=None) -> SeepageMesh:
    """根据裂缝网络创建渗流网格(单层的渗流网络)。

    Args:
        network (FractureNetwork): 裂缝网络对象
        coord: network所在的坐标体系
        height: 裂缝区域的高度(默认值为None，此时高度为1)
        thick: 裂缝区域的厚度(默认值为None，此时厚度为1)
        lmin: 允许的最小的长度(默认值为None，此时长度为lave/2)
        lmax: 允许的最大的长度(默认值为None，此时长度为lave*2)

    Returns:
        SeepageMesh: 生成的渗流网格对象
    """
    mesh = SeepageMesh()
    if network.fracture_number == 0:  # 没有裂缝，直接返回空网格
        return mesh

    # 计算单元长度的平均值
    if lmin is None or lmax is None:
        lave = 0.0
        for fracture in network.fractures:  # 添加单元
            assert isinstance(fracture, FractureNetwork.Fracture)
            length = fracture.length
            assert length > 0, f'Fracture length must > 0 but got {length}'
            lave += length
        lave /= network.fracture_number
        # 计算允许的最大的长度和最小的长度(限制在一定的范围内，从而保证计算的稳定性)
        lmax = lave * 2.0
        lmin = lave / 2.0
    else:
        assert 0 < lmin <= lmax, f'lmin must in (0, lmax] but got lmin={lmin}, lmax={lmax}'

    if height is None:
        height = 1.0
    else:
        assert height > 0, f'Fracture height must > 0 but got {height}'

    if thick is None:
        thick = 1.0
    else:
        assert thick > 0, f'Fracture thickness must > 0 but got {thick}'

    # 全局坐标系(在全局坐标系下创建Mesh)
    global_coord = Coord3()

    for fracture in network.fractures:  # 添加Cell
        assert isinstance(fracture, FractureNetwork.Fracture)
        cell = mesh.add_cell()
        x, y = fracture.center
        z = 0.0
        if coord is not None:
            assert isinstance(coord, Coord3)
            pos = global_coord.view(coord, Array3.from_list([x, y, z]))
            assert isinstance(pos, Array3)
            pos = pos.to_list()
        else:
            pos = [x, y, z]
        cell.pos = pos  # 三维坐标
        length = clamp(fracture.length, lmin, lmax)
        cell.vol = length * height * thick

    for vertex in network.vertexes:  # 添加Face
        assert isinstance(vertex, FractureNetwork.Vertex)
        for i0 in range(vertex.fracture_number):
            f0 = vertex.get_fracture(i0)
            assert isinstance(f0, FractureNetwork.Fracture)
            for i1 in range(i0 + 1, vertex.fracture_number):
                f1 = vertex.get_fracture(i1)
                assert isinstance(f1, FractureNetwork.Fracture)
                face = mesh.add_face(
                    f0.index,
                    f1.index
                )
                dist = clamp((f0.length + f1.length) / 2.0, lmin, lmax)
                face.dist = dist
                face.area = height * thick

    # 返回创建的网格
    return mesh
