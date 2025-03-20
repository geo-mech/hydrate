import numpy as np

from zml import FractureNetwork, SeepageMesh
from zmlx import clamp
from zmlx.demo.hf2.dfn import create_dfn
from zmlx.demo.hf2.solid import create_solid
from zmlx.geometry.dfn2 import get_total_length


def create_mesh(network: FractureNetwork, width=0.01, z=0.0, show_clamp=False):
    """
    根据裂缝网络，创建对应的渗流网格。其中，
        width代表一个裂缝所影响的宽度 (默认大约支撑1cm)
        z是模型所在的z坐标 (默认为0)
    """
    mesh = SeepageMesh()

    for fracture in network.fractures:  # 添加单元
        assert isinstance(fracture, FractureNetwork.Fracture)
        length = fracture.length
        pos = fracture.center
        height = fracture.h  # 高度
        volume = length * width * height
        cell = mesh.add_cell()
        cell.pos = [pos[0], pos[1], z]  # 三维坐标
        cell.vol = volume

    for vertex in network.vertexes:  # 添加面
        assert isinstance(vertex, FractureNetwork.Vertex)
        for i0 in range(vertex.fracture_number):
            for i1 in range(i0 + 1, vertex.fracture_number):
                fracture0 = vertex.get_fracture(i0)
                fracture1 = vertex.get_fracture(i1)
                height = (fracture0.h + fracture1.h) / 2
                area = height * width
                dist = (fracture0.length + fracture1.length) / 2
                count = mesh.face_number
                face = mesh.add_face(fracture0.index, fracture1.index)
                assert count + 1 == mesh.face_number, 'Add face failed.'
                face.area = area
                face.dist = dist

    # 下面，对体积、面积、距离这三个变量进行标准化，避免极端的数值存在 (这对于后续计算的稳定性很重要)

    if mesh.cell_number > 0:
        avg_volume = np.mean([cell.vol for cell in mesh.cells])
        for cell in mesh.cells:
            assert isinstance(cell, SeepageMesh.Cell)
            backup = cell.vol
            cell.vol = clamp(cell.vol, avg_volume * 0.33, avg_volume * 3.3)  # 差距最大相差10倍
            if abs(backup - cell.vol) > backup * 1.0e-6 and show_clamp:
                print(f'Clamp volume: {backup} -> {cell.vol}')

    if mesh.face_number > 0:
        avg_area = np.mean([face.area for face in mesh.faces])
        avg_dist = np.mean([face.dist for face in mesh.faces])
        for face in mesh.faces:
            assert isinstance(face, SeepageMesh.Face)
            backup = face.area
            face.area = clamp(face.area, avg_area * 0.33, avg_area * 3.3)  # 差距最大相差10倍
            if abs(backup - face.area) > backup * 1.0e-6 and show_clamp:
                print(f'Clamp area: {backup} -> {face.area}')

            backup = face.dist
            face.dist = clamp(face.dist, avg_dist * 0.33, avg_dist * 3.3)  # 差距最大相差10倍
            if abs(backup - face.dist) > backup * 1.0e-6 and show_clamp:
                print(f'Clamp dist: {backup} -> {face.dist}')

    # 返回网格
    return mesh


def test():
    fractures = create_dfn()
    network = create_solid(fractures, lave=4)
    mesh = create_mesh(network)
    print(f'mesh = {mesh}.  {get_total_length(fractures)}')


if __name__ == '__main__':
    test()
