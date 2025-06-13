"""
考虑储层和井筒的计算。
"""

from zmlx import *


def create_cylinder(z, r, offset=None):
    """
    创建圆柱形状的mesh
    """
    from zmlx import create_cylinder as impl
    mesh = impl(x=z, r=r)
    if offset is None:
        offset = [0, 0, 0]
    for cell in mesh.cells:
        x, y, z = cell.pos
        cell.pos = y + offset[0], z + offset[1], x + offset[2]
    return mesh


def create_mesh(radius, hyd_bottom, under_h, hyd_h):
    """
    创建网格.
    其中：
        radius：     模型的范围
        hyd_bottom： 水合物底部的z
        under_h：    下伏层厚度
        hyd_h：      水合物层的厚度
    """
    z = [hyd_bottom - under_h, hyd_bottom - 10, hyd_bottom + hyd_h + 10, 0]
    z1 = np.linspace(z[0], z[1], 10)
    z2 = np.linspace(z[1], z[2], 50)
    z3 = np.linspace(z[2], z[3], 50)
    mesh = create_cylinder(
        z=np.concatenate((z1, z2[1:], z3[1:])),
        r=np.linspace(0, radius, 30))
    wel = create_cylinder(
        z=np.concatenate((z2, z3[1:])),
        r=[0, 1], offset=[0, -100, 0])

    cell_n0 = mesh.cell_number
    for c0 in wel.cells:
        assert isinstance(c0, SeepageMesh.Cell)
        c1 = mesh.add_cell()
        c1.pos = c0.pos
        c1.vol = c0.vol

    face_n0 = mesh.face_number
    for f0 in wel.faces:
        assert isinstance(f0, SeepageMesh.Face)
        c0 = f0.get_cell(0)
        c1 = f0.get_cell(1)
        f1 = mesh.add_face(cell_n0 + c0.index, cell_n0 + c1.index)
        f1.area = f0.area
        f1.length = f0.length

    for idx in range(cell_n0, mesh.cell_number):
        c0 = mesh.get_cell(idx)
        x, y, z = c0.pos
        assert abs(y + 100) < 0.1
        c1 = mesh.get_nearest_cell(pos=[x, 0, z])
        face = mesh.add_face(c0, c1)
        face.area = 1
        face.length = 1

    assert face_n0 + wel.face_number + wel.cell_number == mesh.face_number
    return mesh


def create_ini(
        mesh, hyd_bottom, hyd_h, t_seabed, p_seabed, grad_t,
        perm, porosity, pore_modulus, reset_sh=False):
    """
    创建初始场.
    其中：
        mesh：      渗流网格
        hyd_bottom：水合物底部的z
        hyd_h：     水合物层的厚度
        t_seabed:   海底温度
        p_seabed：  海底压力
        grad_t:     地温梯度(每下降1m，温度升高的幅度).
        perm：      渗透率
        porosity：  孔隙度
        reset_sh:   是否生成随机的饱和度
    """
    fname = opath('res_well', 'res_well_z2s.txt')
    if not path.isfile(fname):
        reset_sh = True
    if reset_sh:
        from zmlx.alg.base import join_cols
        vz = np.linspace(
            hyd_bottom - 20, hyd_bottom + hyd_h + 20, 100)
        vs = np.random.uniform(low=0.1, high=0.5, size=vz.size)
        dat = join_cols(vz, vs)
        np.savetxt(fname, dat, fmt='%.3f')
    else:
        dat = np.loadtxt(fname)
        vz, vs = dat[:, 0], dat[:, 1]

    from scipy.interpolate import interp1d
    z2s = interp1d(vz, vs)

    def get_s(x, y, z):
        """
        初始饱和度
        """
        if y < -1:
            return 0, 1.0, (0.0, 0)
        if hyd_bottom <= z <= hyd_bottom + hyd_h:
            s = clamp(z2s(z), 0.0, 0.5)
            return 0, 1 - s, (s, 0)
        else:
            return 0, 1.0, (0.0, 0)

    z_min, z_max = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        """
        储层土体的密度乘以比热（在顶部和底部，将它设置为非常大以固定温度）
        """
        if y < -1:
            return 3e6
        else:
            return 3e6 if z_min + 0.1 < z < z_max - 0.1 else 1e20

    def get_fai(x, y, z):
        """
        孔隙度（在顶部，将孔隙度设置为非常大，以固定压力）
        """
        if z > z_max - 0.1:  # 顶部固定压力
            return 1.0e9
        else:
            return porosity

    t_ini = LinearField(v0=t_seabed, z0=0, dz=-grad_t)
    p_ini = LinearField(v0=p_seabed, z0=0, dz=-0.01e6)

    t0 = t_ini(0, 0, hyd_bottom)
    p0 = p_ini(0, 0, hyd_bottom)

    from zmlx.react import ch4_hydrate

    teq = ch4_hydrate.get_t(p0)
    peq = ch4_hydrate.get_p(t0)
    print(f'At bottom of hydrate layer: '
          f't = {t0 - 273.15}, p = {p0 / 1e6} MPa, teq = {teq - 273.15}, '
          f'peq = {peq / 1e6} MPa')

    def get_p(x, y, z):
        if y < -1 and z > z_max - 0.1:
            return 3e6
        else:
            return p_ini(x, y, z)

    def get_k(x, y, z):
        if y < -99:
            return 1.0e-8
        if y > -1:
            return perm
        if hyd_bottom + 10 < z < hyd_bottom + hyd_h - 10:
            return perm * 100
        else:
            return 0

    def get_dist(x, y, z):
        if y > -1:
            return 0.1
        else:
            return 0.01

    return {'porosity': get_fai, 'pore_modulus': pore_modulus,
            'p': get_p, 'temperature': t_ini,
            'denc': get_denc, 's': get_s, 'perm': get_k,
            'heat_cond': 2, 'dist': get_dist}


def create_model(
        radius=40., hyd_bottom=-300., under_h=100., hyd_h=60.,
        t_seabed=276.0826483615683, p_seabed=12e6, grad_t=0.04466,
        perm=1.0e-14, porosity=0.3, pore_modulus=200e6, p_prod=3e6
):
    """
    创建计算模型
    其中：
        radius：      模型的范围
        hyd_bottom：  水合物底部的z
        under_h：     下伏层厚度
        hyd_h：       水合物层的厚度
        upper_h：     上覆层厚度
        t_seabed:     海底温度
        p_seabed：    海底压力
        grad_t:       地温梯度(每下降1m，温度升高的幅度).
        perm：        渗透率
        porosity：    孔隙度
        pore_modulus: 孔隙刚度
        p_prod:       生产压力
    """
    mesh = create_mesh(
        radius=radius, hyd_bottom=hyd_bottom,
        under_h=under_h, hyd_h=hyd_h
    )
    ini = create_ini(
        mesh=mesh, hyd_bottom=hyd_bottom,
        hyd_h=hyd_h, t_seabed=t_seabed,
        p_seabed=p_seabed, grad_t=grad_t,
        perm=perm, porosity=porosity,
        pore_modulus=pore_modulus
    )
    gr = create_krf(
        0.1, 2,
        as_interp=True,
        k_max=1, s_max=1, count=200
    )
    kw = hydrate.create_kwargs(gr=gr)
    kw.update(ini)
    kw.update(dict(
        gravity=(0, 0, -10),
        dt_ini=1.0, dt_min=1.0, dt_max=24 * 3600 * 7, dv_relative=0.1
    ))

    # 创建模型
    model = seepage.create(mesh=mesh, **kw)

    # 设置相渗
    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    i_gas = model.find_fludef('gas')
    i_liq = model.find_fludef('liq')
    assert len(i_gas) == 1 and len(i_liq) == 1
    i_gas = i_gas[0]
    i_liq = i_liq[0]
    model.set_kr(i_gas, vs, kg)
    model.set_kr(i_liq, vs, kw)

    return model


def plot_cells(model: Seepage, monitor=None, folder=None):
    """
    在界面上绘图并且(在给定folder的时候)保存图片
    """
    if not gui.exists():
        return

    time = time2str(seepage.get_time(model))
    year = seepage.get_time(model) / (3600 * 24 * 365)

    x = as_numpy(model).cells.x
    y = as_numpy(model).cells.y
    z = as_numpy(model).cells.z
    p = as_numpy(model).cells.pre

    plot_xy(y=z[y < -1], x=p[y < -1], caption='well_pre',
            xlabel='pre', ylabel='depth',
            title=f'time = {time}')

    t = as_numpy(model).fluids(1).get(model.get_flu_key('temperature'))
    plot_xy(y=z[y < -1], x=t[y < -1], caption='well_T',
            xlabel='temperature', ylabel='depth',
            title=f'time = {time}')

    fv_all = as_numpy(model).cells.fluid_vol
    s = as_numpy(model).fluids(2, 0).vol / fv_all
    plot_xy(y=z[y < -1], x=s[y < -1], caption='well_sh',
            xlabel='sh', ylabel='depth',
            title=f'time = {time}')

    is_ok1 = y > -1
    x = x[is_ok1]
    z = z[is_ok1]

    def show_ca(idx, name):
        p = as_numpy(model).cells.get(idx)
        p = p[is_ok1]
        tricontourf(
            x, z, p, caption=name, title=f'time = {time}',
            fname=make_fname(
                year, path.join(folder, name), '.jpg',
                'y'))
        return p

    show_ca(-12, 'pressure')
    show_ca(model.get_cell_key('temperature'), 'temperature')

    fv_all = fv_all[is_ok1]

    def show_m(idx, name):
        v = as_numpy(model).fluids(*idx).vol
        v = v[is_ok1]
        tricontourf(
            x, z, v / fv_all, caption=name,
            title=f'time = {time}',
            fname=make_fname(
                year, path.join(folder, name), '.jpg',
                'y'))

    show_m([0], 'ch4')
    show_m([2, 0], 'ch4_hyd')

    # 显示生产曲线
    if monitor is not None:
        monitor.plot_prod(
            index=0, caption='ch4_prod',
            fname=make_fname(
                year, path.join(folder, 'ch4_prod'),
                '.jpg', 'y'))
        monitor.plot_rate(
            index=0, caption='ch4_rate',
            fname=make_fname(
                year, path.join(folder, 'ch4_rate'),
                '.jpg', 'y'))


def solve(model, time_forward=3600.0 * 24.0 * 365.0 * 10, folder=None,
          day_save=30.0):
    """
    求解给定的模型 model
        day_save：数据保存的时间间隔[单位：天];
        time_forward：向前求解的时间长度[单位: 秒]
    """
    assert isinstance(model, Seepage)
    if folder is not None:
        print_tag(folder)
        print(f'Solve. folder = {folder}')
        if gui.exists():
            gui.title(f'Data folder = {folder}')

    # 执行迭代
    iterate = GuiIterator(
        seepage.iterate,
        lambda: plot_cells(
            model, folder=path.join(folder, 'figures')))

    # 线性求解器.
    solver = ConjugateGradientSolver(tolerance=1.0e-15)

    # 自动保存模型
    save_model = SaveManager(
        folder=path.join(folder, 'models'),
        dtime=day_save,
        get_time=lambda: seepage.get_time(model) / (24 * 3600),
        save=model.save, ext='.seepage', time_unit='d',
        always_save=False)

    # 自动保存cells
    save_cells = SaveManager(
        folder=path.join(folder, 'cells'),
        dtime=day_save,
        get_time=lambda: seepage.get_time(model) / (24 * 3600),
        save=lambda name: seepage.print_cells(name, model),
        ext='.txt', time_unit='d', always_save=False)

    # 最终停止时的时间.
    time_max = time_forward + seepage.get_time(model)

    while seepage.get_time(model) < time_max:
        iterate(model, solver=solver)
        save_model()
        save_cells()
        step = seepage.get_step(model)
        if step % 10 == 0:
            time = time2str(seepage.get_time(model))
            dt = time2str(seepage.get_dt(model))
            print(f'step = {step}, dt = {dt}, time = {time}')


def execute(folder=None, time_forward=3600 * 24 * 365 * 20, **kwargs):
    """
    执行建模和计算的全过程
    """
    model = create_model(**kwargs)
    print(model)
    solve(model=model, time_forward=time_forward, folder=folder, day_save=1.0)


def _test3():
    gui.execute(lambda: execute(folder=opath('res_well', 'case_1')),
                close_after_done=False)


def case_2():
    gui.execute(lambda: execute(folder=opath('res_well', 'case_2')),
                close_after_done=False)


if __name__ == '__main__':
    _test3()
