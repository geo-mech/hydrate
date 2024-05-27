from zmlx.geometry.point_distance import point_distance
from zmlx.geometry.seg_point_distance import seg_point_distance


def get_faces_across(model, p0, p1):
    """
    获得给定的线段穿越的所有的face.
    返回list; list中的每一个元素都是face的序号

        since 2024-7-16
    """
    cell_beg = model.get_nearest_cell(pos=p0)
    cell_end = model.get_nearest_cell(pos=p1)

    def get_dist(cell_pos):
        return seg_point_distance([p0, p1], cell_pos) + point_distance(cell_pos, cell_end.pos)

    face_ids = []
    while cell_beg.index != cell_end.index:   # 遍历的目标，是利用这些face建立这两个cell之间的通道.
        dist = [get_dist(c.pos) for c in cell_beg.cells]
        idx = 0
        for i in range(1, len(dist)):
            if dist[i] < dist[idx]:
                idx = i
        cell = cell_beg.get_cell(idx)
        # face的数量(备份以供后续检查)
        face_n = model.face_number
        face = model.add_face(cell_beg, cell)   # 此时，一定不会创建新的face
        assert face_n == model.face_number
        face_ids.append(face.index)
        cell_beg = cell

    # 返回所有的face的index
    return face_ids


def test():
    """
    测试
    """
    from zmlx.seepage_mesh.cube import create_xz
    mesh = create_xz(x_min=0, dx=1, x_max=30, z_min=0, dz=1, z_max=30, y_min=-1, y_max=1)
    face_ids = get_faces_across(mesh, p0=[0, 0, 0], p1=[10, 0, 20])
    for idx in face_ids:
        face = mesh.get_face(idx)
        print(f'{idx}     {face.pos}')


if __name__ == '__main__':
    test()
