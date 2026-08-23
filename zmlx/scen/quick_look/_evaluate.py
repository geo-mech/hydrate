"""
储层压力快速评估 — 2D 单相流计算.
"""

from zmlx import FluDef, create_cube, linspace, tfc


def evaluate(
        *,
        x_range=(0, 400),
        y_range=(0, 400),
        dx=None,
        dy=None,
        p=1e6,
        perm=1e-14,
        pore_modulus=100e6,
        viscosity=1e-3,
        control_p=None,
        time_forward=3600 * 24,
        step_max=100,
        acc_factor=1e6,
        frac_segs=None,
):
    """2D 单相流压力评估.

    在矩形区域内创建 SeepageMesh → tfc.create，基于 Darcy 渗透率
    计算 dt 时间后的孔隙压力分布。

    为加速计算，将 porosity 和 pore_modulus 放大 acc_factor 倍.

    Args:
        x_range: x 范围 (x_min, x_max) [m].
        y_range: y 范围 (y_min, y_max) [m].
        dx: x 网格尺寸 [m].
        dy: y 网格尺寸 [m], 默认 = dx.
        p: 初始压力 [Pa], 标量或 ``(x,y,z) -> p`` 函数.
        perm: 渗透率 [m^2].
        pore_modulus: 孔隙刚度 [Pa].
        viscosity: 流体粘度 [Pa·s].
        control_p: 控压点 [(x, y), ...]，压力取自 p 参数.
        time_forward: 总模拟时间 [s].
        step_max: 最大迭代步数.
        acc_factor: 加速因子，porosity 和 pore_modulus 的放大倍数.
        frac_segs: 裂缝线段 [(p0, p1, factor), ...]，p0/p1 为 2D (x,y) 坐标，
            factor 为 Face 面积放大倍率（多条裂缝经过同一 Face 时取最大值）.

    Returns:
        dict: {'x', 'y', 'p', 'model', 'n_step'}
    """
    if dx is None and dy is None:
        raise ValueError('dx or dy must be given')
    dx = dy if dx is None else dx
    dy = dx if dy is None else dy

    if acc_factor <= 0:
        raise ValueError(f'acc_factor must be positive, got {acc_factor}')

    x0, x1 = x_range
    y0, y1 = y_range
    nx = max(2, round((x1 - x0) / dx))
    ny = max(2, round((y1 - y0) / dy))

    # ── 1. 网格 ──
    mesh = create_cube(
        x=linspace(x0, x1, nx + 1),
        y=linspace(y0, y1, ny + 1),
        z=(-0.5, 0.5),
    )

    # ── 2. 定压边界 Cell ──
    if control_p:
        for item in control_p:
            x, y = item[0], item[1]
            cell = mesh.get_nearest_cell(pos=(x, y, 0))
            if cell is not None:
                cell.vol *= 1e10  # 放大体积以固定该 cell 压力

    # ── 3. 裂缝 ──
    if frac_segs:
        face_factors = {}  # Face index → max factor
        for seg in frac_segs:
            p0, p1 = (seg[0][0], seg[0][1]), (seg[1][0], seg[1][1])
            factor = seg[2] if len(seg) >= 3 else 1.0
            p0_3d = (p0[0], p0[1], None)
            p1_3d = (p1[0], p1[1], None)
            ids = tfc.get_cells_along_seg(p0=p0_3d, p1=p1_3d, model=mesh)
            for idx in range(len(ids) - 1):
                c0 = mesh.get_cell(ids[idx])
                c1 = mesh.get_cell(ids[idx + 1])
                face = mesh.get_face(cell_0=c0, cell_1=c1)
                if face is None:
                    face = mesh.add_face(cell_0=c0, cell_1=c1, area=1.0, dist=1.0)
                fi = face.index
                face_factors[fi] = max(face_factors.get(fi, 0), factor)
        # 应用面积放大（上限 10000 倍）
        max_factor = 10000
        for fi, factor in face_factors.items():
            face = mesh.get_face(ind=fi)
            if face is not None:
                face.area *= min(factor, max_factor)

    # ── 4. 模型 ──
    def _pm(x, y, z):
        return (pore_modulus(x, y, z) if callable(pore_modulus) else pore_modulus) * acc_factor

    model = tfc.create(
        mesh,
        fludefs=[FluDef(den=1000, vis=viscosity, name='h2o')],
        porosity=acc_factor,
        pore_modulus=_pm,
        p=p,
        s={'h2o': 1.0},
        perm=perm,
        disable_update_den=True,
        disable_update_vis=True,
        disable_ther=True,
        disable_heat_exchange=True,
        pore_modulus_range=[1e6, 1e20],
    )

    # ── 5. 迭代 ──
    tfc.set_dt(model, time_forward)
    step = 0
    for step in range(step_max):
        remaining = time_forward - tfc.get_time(model)
        if remaining <= time_forward * 1.0e-3:
            break
        tfc.set_dt_max(model, remaining)
        tfc.iterate(model)
        step += 1

    # ── 6. 返回 ──
    return {
        'x': tfc.get_x(model),
        'y': tfc.get_y(model),
        'p': tfc.get_p(model),
        'model': model,
        'n_step': step + 1,
    }
