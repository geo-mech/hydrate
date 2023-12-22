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


def create_mesh(width=100.0, height=400.0):
    """
    创建网格. 模型高度height，宽度width. 单个网格的大小大约为2米. 模型在y方向的厚度为1m
    """
    assert 15.0 <= width <= 200.0 and 100.0 <= height <= 500.0
    jx = round(width/2)
    jz = round(height/2)
    x = np.linspace(0, width, jx)
    y = [-0.5, 0.5]
    z = np.linspace(-height, 0, jz)
    return SeepageMesh.create_cube(x, y, z)


def create_ini(mesh, under_h=100.0, hyd_h=60.0, t_top=274.0, p_top=10e6, grad_t=0.035, perm=1.0e-14, porosity=0.3):
    """
    创建初始场. 其中：
        under_h: 下伏层厚度
        hyd_h: 水合物层厚度
        t_top: 模型顶部温度
        grad_t: 地温梯度(每下降1m，温度升高的幅度).
    """
    assert 20.0 <= under_h <= 200.0
    assert 0.0 <= hyd_h <= 200.0
    assert 273.5 <= t_top <= 280.0
    assert 5e6 <= p_top <= 20e6
    assert 0.02 <= grad_t <= 0.06
    assert 1.0e-16 <= perm <= 1.0e-12
    assert 0.1 <= porosity <= 0.6

    z_min, z_max = mesh.get_pos_range(2)

    def get_k(x, y, z):
        """
        渗透率
        """
        return perm

    def get_s(x, y, z):
        """
        初始饱和度()
        """
        if z_min + under_h <= z <= z_min + under_h + hyd_h:
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
        if z > z_max - 0.1:  # 顶部固定压力
            return 1.0e7

        if z < z_min + 0.1:  # 底部(假设底部有500m的底水供给)
            return porosity * (500.0 / 2.0)

        else:
            return porosity

    t_ini = LinearField(v0=t_top, z0=z_max, dz=-grad_t)
    p_ini = LinearField(v0=p_top, z0=z_max, dz=-0.01e6)
    sample_dist = 1.0

    t0 = t_ini(0, 0, z_min + under_h)
    p0 = p_ini(0, 0, z_min + under_h)
    print(f'At bottom of hydrate layer: t = {t0}, p = {p0}, peq = {get_p(t0)}')

    return {'porosity': get_fai, 'pore_modulus': 200e6, 'p': p_ini, 'temperature': t_ini,
            'denc': get_denc, 's': get_s, 'perm': get_k, 'heat_cond': 2,
            'sample_dist': sample_dist}


def create_model(width=100.0, height=400.0,
                 under_h=100.0, hyd_h=60.0, t_top=274.0, p_top=10e6, grad_t=0.035, perm=1.0e-14, porosity=0.3,
                 kg_co2_day=10.0, x_inj=None, z_inj=None):
    """
    创建模型
    """
    mesh = create_mesh(width=width, height=height)
    ini = create_ini(mesh=mesh, under_h=under_h, hyd_h=hyd_h,
                     t_top=t_top, p_top=p_top, grad_t=grad_t, perm=perm, porosity=porosity)

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)
    z_min, z_max = mesh.get_pos_range(2)

    gr = create_krf(0.1, 1.5, as_interp=True, k_max=1, s_max=1, count=200)
    kw = hydrate_v2.Config(has_co2=True, gr=gr).get_kw(h2o_density=1.0e3)
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

    # 添加虚拟Cell用于生产 (最后一个cell为虚拟的).
    z_prod = z_min + under_h + hyd_h * 0.5
    pos = (x_min, -1000.0, z_prod)
    virtual_cell = seepage.add_cell(model, pos=pos, porosity=1.0e7, pore_modulus=100e6, vol=1.0,
                                    temperature=ini['temperature'](*pos), p=4e6,
                                    s=((0, 0), 1, (0, 0, 0)))
    cell = model.get_nearest_cell([x_min, 0, z_prod])
    virtual_face = seepage.add_face(model, virtual_cell, cell,
                                    heat_cond=0, perm=perm, area=1.0, length=1.0)

    # 添加注入co2.
    assert 0 <= kg_co2_day <= 1.0e5
    pos = [x_inj if x_inj is not None else x_max, 0.0, z_inj if z_inj is not None else z_max - 150.0]
    cell = model.get_nearest_cell(pos)
    flu = cell.get_fluid(0, 1).get_copy()  # co2
    inj = model.add_injector(cell=cell, fluid_id=(0, 1), flu=flu, pos=pos, radi=3,
                             value=(kg_co2_day / flu.den) / (3600 * 24))

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

    def show_ca(idx, name):
        p = model.numpy.cells.get(idx)
        p = p[: -1]
        tricontourf(x, z, p, caption=name, title=f'time = {time}',
                    fname=make_fname(year, path.join(folder, name), '.jpg', 'y'))

    show_ca(-12, 'pressure')
    show_ca(model.get_cell_key('temperature'), 'temperature')

    def show_m(idx, name):
        m = model.numpy.fluids(*idx).mass
        m = m[: -1]
        tricontourf(x, z, m, caption=name, title=f'time = {time}',
                    fname=make_fname(year, path.join(folder, name), '.jpg', 'y'))

    show_m([0, 0], 'ch4')
    show_m([0, 1], 'co2')
    show_m([2, 0], 'ch4_hyd')
    show_m([2, 2], 'co2_hyd')


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


def execute(folder=None, time_max=3600 * 24 * 365 * 30, **kwargs):
    """
    执行建模和计算的全过程
    """
    model = create_model(**kwargs)
    print(model)
    solve(model, folder=folder, time_max=time_max)


def _test3():
    execute(folder=opath('co2_disp'), p_top=6e6)


if __name__ == '__main__':
    gui.execute(_test3, close_after_done=False)
