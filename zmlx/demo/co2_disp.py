# ** desc = 'co2置换ch4水合物. 竖向二维模型 (水平井注采模型).'
"""
co2置换ch4水合物. 竖向二维模型 (水平井注采模型).

模型的边界：
    模型顶部：海底；
       底部：甲烷水合物储层下底面以下大约50米

    左右两侧：
        隔热、不透水

    底部：
        恒温、不透水

    顶部：
        恒温、透水
"""

from zmlx import *
from zmlx.config import hydrate_v2
from zmlx.config import seepage
from zmlx.filesys import path
from zmlx.kr.create_kr import create_kr
from zmlx.kr.create_krf import create_krf
from zmlx.react.ch4_hydrate import get_p
from zmlx.utility.LinearField import LinearField
from zmlx.filesys.opath import opath
import numpy as np


def create_mesh():
    """
    创建网格. 模型高度400米，宽度100米, 分为200*50个网格.
    """
    x = np.linspace(0, 100, 50)
    y = [-0.5, 0.5]
    z = np.linspace(-400, 0, 200)
    return SeepageMesh.create_cube(x, y, z)


def create_ini(mesh, z0=-300, t0=287.0, p0=get_p(287.0)):
    """
    创建初始场。其中t0和p0为z0深度对应的温度和压力（作为参考点），从而来设置全场的温度和压力。
    """
    z_min, z_max = mesh.get_pos_range(2)

    def get_k(x, y, z):
        """
        渗透率
        """
        return 1.0e-14

    def get_s(x, y, z):
        """
        初始饱和度()
        """
        if z0 <= z <= z0 + 60:
            return (0, 0), 0.5, (0.5, 0, 0)
        else:
            return (0, 0), 1, (0, 0, 0)

    def get_denc(x, y, z):
        """
        储层土体的密度乘以比热（在顶部和底部，将它设置为非常大以固定温度）
        """
        return 3e6 if z_min + 0.1 < z < z_max - 0.1 else 1e20

    def get_fai(x, y, z):
        """
        孔隙度（在顶部，将孔隙度设置为非常大，以固定压力）
        """
        return 1.0e6 if z > z_max - 0.1 else 0.3

    t_ini = LinearField(v0=t0, z0=z0, dz=-0.035)
    p_ini = LinearField(v0=p0, z0=z0, dz=-0.01e6)
    sample_dist = 1.0

    return {'porosity': get_fai, 'pore_modulus': 200e6, 'p': p_ini, 'temperature': t_ini,
            'denc': get_denc, 's': get_s, 'perm': get_k, 'heat_cond': 2,
            'sample_dist': sample_dist}


def create_model():
    """
    创建模型
    """
    mesh = create_mesh()
    ini = create_ini(mesh=mesh)

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)
    z_min, z_max = mesh.get_pos_range(2)

    gr = create_krf(0.1, 1.5, as_interp=True, k_max=1, s_max=1, count=200)
    kw = hydrate_v2.Config(has_co2=True, gr=gr).kwargs
    kw.update(ini)
    kw.update(create_dict(gravity=(0, 0, -10)))

    # 创建模型
    model = seepage.create(mesh=mesh, **kw)

    # 设置相渗
    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    igas = model.find_fludef('gas')
    iliq = model.find_fludef('liq')
    assert len(igas) == 1 and len(iliq) == 1
    igas = igas[0]
    iliq = iliq[0]
    model.set_kr(igas, vs, kg)
    model.set_kr(iliq, vs, kw)

    # 设置dt
    seepage.set_dv_relative(model, 0.1)  # 每一个时间步流过的距离与网格大小的比值
    seepage.set_dt(model, 0.01)  # 时间步长的初始值
    seepage.set_dt_max(model, 24 * 3600)  # 时间步长的最大值
    seepage.set_dt_min(model, 10)

    # 添加虚拟Cell用于生产
    pos = (x_min, -1000.0, -270)
    virtual_cell = seepage.add_cell(model, pos=pos, porosity=1.0e7, pore_modulus=100e6, vol=1.0,
                                    temperature=ini['temperature'](*pos), p=4e6,
                                    s=((0, 0), 1, (0, 0, 0)))
    cell = model.get_nearest_cell([x_min, 0, -270])
    virtual_face = seepage.add_face(model, virtual_cell, cell,
                                    heat_cond=0, perm=1.0e-14, area=1.0, length=1.0)

    # 添加注入co2
    pos = [x_max, 0, -150]
    cell = model.get_nearest_cell(pos)
    flu = cell.get_fluid(0, 1).get_copy()  # co2
    inj = model.add_injector(cell=cell, fluid_id=(0, 1), flu=flu, pos=pos, radi=3,
                             opers=[[0, (10 / flu.den) / (3600 * 24)]])

    return model


def plot_cells(model, folder=None):
    if not gui.exists():
        return
    from zmlx.plt.tricontourf import tricontourf
    assert isinstance(model, Seepage)

    time = time2str(seepage.get_time(model))
    year = seepage.get_time(model) / (3600 * 24 * 365)

    x = model.numpy.cells.x
    z = model.numpy.cells.z
    x = x[: -1]
    z = z[: -1]

    p = model.numpy.cells.get(-12)
    p = p[: -1]
    tricontourf(x, z, p, caption='pressure', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'pressure'), '.jpg', 'y'))

    t = model.numpy.cells.get(model.get_cell_key('temperature'))
    t = t[: -1]
    tricontourf(x, z, t, caption='temperature', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'temperature'), '.jpg', 'y'))

    m = model.numpy.fluids(0, 0).mass
    m = m[: -1]
    tricontourf(x, z, m, caption='ch4', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'ch4'), '.jpg', 'y'))

    m = model.numpy.fluids(0, 1).mass
    m = m[: -1]
    tricontourf(x, z, m, caption='co2', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'co2'), '.jpg', 'y'))

    m = model.numpy.fluids(2, 0).mass
    m = m[: -1]
    tricontourf(x, z, m, caption='ch4_hyd', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'ch4_hyd'), '.jpg', 'y'))

    m = model.numpy.fluids(2, 2).mass
    m = m[: -1]
    tricontourf(x, z, m, caption='co2_hyd', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'co2_hyd'), '.jpg', 'y'))


def solve(model: Seepage, time_max=3600 * 24 * 365 * 30, folder=None):
    if folder is not None:
        print(f'Solve. folder = {folder}')
        if gui.exists():
            gui.title(f'Data folder = {folder}')

    solver = ConjugateGradientSolver(tolerance=1.0e-14)
    iterate = GuiIterator(seepage.iterate, lambda: plot_cells(model, folder=path.join(folder, 'figures')))

    while seepage.get_time(model) < time_max:
        iterate(model, solver=solver)
        step = seepage.get_step(model)
        if step % 10 == 0:
            time = time2str(seepage.get_time(model))
            dt = time2str(seepage.get_dt(model))
            print(f'step = {step}, dt = {dt}, time = {time}')


def _test1():
    mesh = create_mesh()
    print(mesh)


def _test2():
    from zmlx.react.ch4_hydrate import get_t, get_p
    t = 285.0
    p = get_p(t)
    print(f't = {t}, p = {p}, t2 = {get_t(p)}')


def _test3():
    model = create_model()
    print(model)
    solve(model, folder=opath('co2_disp'))


if __name__ == '__main__':
    gui.execute(_test3, close_after_done=False)
