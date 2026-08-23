"""测试 tfc.get_cells_along_seg 在 2D mesh 上的行为."""
from zmlx import SeepageMesh, create_cube, linspace, tfc


def main():
    # 创建 10x10 的 2D 网格
    mesh = create_cube(
        x=linspace(0, 100, 11),
        y=linspace(0, 100, 11),
        z=(-0.5, 0.5),
    )
    print(f'网格: {mesh.cell_number} cells')

    # 测试 1: z=None，忽略 z 维度
    p0 = (0.0, 0.0, None)
    p1 = (100.0, 100.0, None)
    ids = tfc.get_cells_along_seg(p0=p0, p1=p1, model=mesh)
    print(f'\n对角线 (z=None): {len(ids)} cells')
    for i in ids:
        c = mesh.get_cell(i)
        print(f'  cell {i}: pos=({c.pos[0]:.1f}, {c.pos[1]:.1f}, {c.pos[2]:.1f})')
    assert len(ids) == 10, f'Expected 10 cells along diagonal, got {len(ids)}'

    # 测试 2: z=0.0 对比
    p0 = (0.0, 0.0, 0.0)
    p1 = (100.0, 100.0, 0.0)
    ids2 = tfc.get_cells_along_seg(p0=p0, p1=p1, model=mesh)
    print(f'\n对角线 (z=0.0): {len(ids2)} cells')
    assert ids == ids2, 'z=None and z=0.0 should give same result'

    # 测试 3: 水平线段
    p0 = (0.0, 50.0, None)
    p1 = (100.0, 50.0, None)
    ids3 = tfc.get_cells_along_seg(p0=p0, p1=p1, model=mesh)
    print(f'\n水平线: {len(ids3)} cells')
    for i in ids3:
        c = mesh.get_cell(i)
        print(f'  cell {i}: pos=({c.pos[0]:.1f}, {c.pos[1]:.1f})')
    assert len(ids3) == 10, f'Expected 10 cells, got {len(ids3)}'

    # 测试 4: 检查相邻 cell 的连续性 — 是否每对相邻 cell 都是网格邻居
    print('\n检查相邻 cell 连续性:')
    for idx in range(len(ids3) - 1):
        c0 = mesh.get_cell(ids3[idx])
        c1 = mesh.get_cell(ids3[idx + 1])
        face = mesh.get_face(cell_0=c0, cell_1=c1)
        status = f'Face found' if face is not None else 'NO FACE'
        print(f'  {ids3[idx]} -> {ids3[idx+1]}: {status}')

    print('\n所有测试通过!')


if __name__ == '__main__':
    main()
