"""测试裂缝 Face 面积修改是否正确."""
from zmlx import create_cube, linspace, tfc


def main():
    # 5x5 网格，易于追踪
    mesh = create_cube(
        x=linspace(0, 50, 6),
        y=linspace(0, 50, 6),
        z=(-0.5, 0.5),
    )
    print(f'网格: {mesh.cell_number} cells, {mesh.face_number} faces')

    # 记录修改前的面积
    face_info = {}
    for fi in range(mesh.face_number):
        f = mesh.get_face(ind=fi)
        face_info[fi] = f.area

    # 模拟裂缝处理：水平线 y=25
    frac_segs = [
        ((0, 25), (50, 25), 100),  # 水平裂缝，factor=100
    ]

    face_factors = {}
    for seg in frac_segs:
        p0, p1 = (seg[0][0], seg[0][1]), (seg[1][0], seg[1][1])
        factor = seg[2]
        p0_3d = (p0[0], p0[1], None)
        p1_3d = (p1[0], p1[1], None)
        ids = tfc.get_cells_along_seg(p0=p0_3d, p1=p1_3d, model=mesh)
        print(f'\n裂缝线段 ({p0}) -> ({p1}), factor={factor}')
        print(f'  穿过 cells: {ids}')
        for idx in range(len(ids) - 1):
            c0 = mesh.get_cell(ids[idx])
            c1 = mesh.get_cell(ids[idx + 1])
            face = mesh.get_face(cell_0=c0, cell_1=c1)
            if face is not None:
                fi = face.index
                face_factors[fi] = max(face_factors.get(fi, 0), factor)
                print(f'  cell {ids[idx]} -> {ids[idx+1]}: Face {fi}, factor={face_factors[fi]}')
            else:
                print(f'  cell {ids[idx]} -> {ids[idx+1]}: NO FACE!')

    print(f'\n受影响的 Face: {len(face_factors)} 个')

    # 应用面积放大
    max_limit = 10000
    for fi, factor in face_factors.items():
        face = mesh.get_face(ind=fi)
        old_area = face_info[fi]
        new_area = old_area * min(factor, max_limit)
        face.area *= min(factor, max_limit)
        print(f'  Face {fi}: area {old_area:.4f} -> {new_area:.4f} (x{min(factor, max_limit)})')

    # 验证
    for fi, factor in face_factors.items():
        face = mesh.get_face(ind=fi)
        expected = face_info[fi] * min(factor, max_limit)
        assert abs(face.area - expected) < 1e-10, \
            f'Face {fi}: expected {expected}, got {face.area}'

    print('\n所有 Face 面积修改正确!')


if __name__ == '__main__':
    main()
