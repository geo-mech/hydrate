from zml import SeepageMesh, Mesh3
from zmlx.geometry.base import point_distance


def face_centered(mesh, thick=1.0):
    """
    从Mesh3来创建SeepageMesh，将Mesh3的Face作为新建SeepageMesh的Cell，将Mesh3的Link作为新建SeepageMesh的Face。
        其中Mesh3中Face的厚度利用thick来给定.

    zzb. since 24-1-29
    """
    assert isinstance(mesh, Mesh3)
    assert thick > 0

    res = SeepageMesh()

    # 将Mesh3的Face作为SeepageMesh的Cell
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        cel = res.add_cell()
        cel.vol = face.area * thick
        cel.pos = face.pos

    # 将Mesh3的Link作为SeepageMesh的Face
    for link in mesh.links:
        assert isinstance(link, Mesh3.Link)
        if link.face_number < 2:
            continue
        # 新的face的面积
        area = link.length * thick
        pos = link.pos
        for i0 in range(link.face_number):
            face0 = link.get_face(i0)
            dist0 = point_distance(face0.pos, pos)
            for i1 in range(i0 + 1, link.face_number):
                face1 = link.get_face(i1)
                dist1 = point_distance(face1.pos, pos)
                dist = dist0 + dist1  # 总的流动距离
                fac = res.add_face(res.get_cell(face0.index),
                                   res.get_cell(face1.index))
                fac.area = area
                fac.length = dist

    # 成功
    return res


def test():
    mesh3 = Mesh3.create_cube(x1=-20, y1=-20, z1=0, x2=20, y2=20, z2=0, dx=1,
                              dy=1, dz=1)
    print(mesh3)

    mes = face_centered(mesh=mesh3, thick=1)
    print(mes)


if __name__ == '__main__':
    test()
