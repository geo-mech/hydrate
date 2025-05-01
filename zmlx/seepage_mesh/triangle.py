from zml import SeepageMesh, Mesh3
from zmlx.geometry.utils import get_center
from zmlx.geometry.utils import point_distance


def split_triangles(vertexes: list, triangles: list):
    """
    将一个三角形分割成为4个(同样形状的);
    """
    v2 = vertexes.copy()
    t2 = [sorted(triangle) for triangle in triangles]

    lnk_ids = {}
    # 添加各个边的中心点 (并且获得点的id)
    for triangle in t2:
        for lk in [(triangle[0], triangle[1]), (triangle[0], triangle[2]), (triangle[1], triangle[2])]:
            p0 = v2[lk[0]]
            p1 = v2[lk[1]]
            lnk_ids[lk] = len(v2)
            v2.append(get_center(p0, p1))

    t3 = []
    for triangle in t2:
        a = triangle[0]
        b = lnk_ids.get((triangle[0], triangle[1]))
        c = lnk_ids.get((triangle[0], triangle[2]))
        t3.append(sorted([a, b, c]))

        a = triangle[1]
        b = lnk_ids.get((triangle[0], triangle[1]))
        c = lnk_ids.get((triangle[1], triangle[2]))
        t3.append(sorted([a, b, c]))

        a = triangle[2]
        b = lnk_ids.get((triangle[0], triangle[2]))
        c = lnk_ids.get((triangle[1], triangle[2]))
        t3.append(sorted([a, b, c]))

        a = lnk_ids.get((triangle[0], triangle[1]))
        b = lnk_ids.get((triangle[0], triangle[2]))
        c = lnk_ids.get((triangle[1], triangle[2]))
        t3.append(sorted([a, b, c]))

    return v2, t3


def create(x0, y0, x1, y1, x2, y2, n_max=None, n_split=None):
    """
    在一个三角形区域，通过不断的四等分，来获得三角形剖分；
    """
    v = [[x0, y0], [x1, y1], [x2, y2]]
    t = [[0, 1, 2]]

    # 给定默认的参数
    assert n_max is not None or n_split is not None
    if n_max is None:
        n_max = 9999999
    if n_split is None:
        n_split = 9999

    for step in range(n_split):
        if len(t) * 4 <= n_max:
            v, t = split_triangles(v, t)
        else:
            break

    mesh3 = Mesh3()

    for p in v:
        mesh3.add_node(x=p[0], y=p[1], z=0)

    for i, j, k in t:
        link_ids = []
        for i0, i1 in [(i, j), (j, k), (i, k)]:
            link = mesh3.add_link(nodes=[mesh3.get_node(i0), mesh3.get_node(i1)])
            link_ids.append(link.index)
        links = [mesh3.get_link(i) for i in link_ids]
        mesh3.add_face(links=links)

    mesh = SeepageMesh()

    for face in mesh3.faces:
        assert isinstance(face, Mesh3.Face)
        cell = mesh.add_cell()
        cell.pos = face.pos
        cell.vol = face.area

    for link in mesh3.links:
        assert isinstance(link, Mesh3.Link)
        if link.face_number == 2:
            c0 = mesh.get_cell(link.get_face(0).index)
            c1 = mesh.get_cell(link.get_face(1).index)
            face = mesh.add_face(c0, c1)
            face.area = link.length
            face.length = point_distance(c0.pos, c1.pos)

    return mesh


def test():
    mesh = create(0, 0, 1, 0, 0, 1, n_split=5)
    print(mesh)


if __name__ == '__main__':
    test()
