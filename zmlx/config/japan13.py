"""
分层三维的模型.
"""
import os

import numpy as np

from zml import ConjugateGradientSolver, SeepageMesh, create_dict, is_windows, Tensor3, Interp1
from zmlx.alg.clamp import clamp
from zmlx.alg.time2str import time2str
from zmlx.config import hydrate, seepage, attr_keys
from zmlx.data.Ye2022 import load_curve, load_txt
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_fname import make_fname
from zmlx.filesys.opath import opath
from zmlx.filesys.tag import print_tag
from zmlx.kr.create_kr import create_kr
from zmlx.kr.create_krf import create_krf
from zmlx.plt.plot2 import plot2
from zmlx.plt.plotxy import plotxy
from zmlx.plt.tricontourf import tricontourf
from zmlx.react.ch4_hydrate import get_t as get_hyd_t
from zmlx.ui import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.LinearField import LinearField
from zmlx.utility.PressureController import PressureController
from zmlx.utility.SaveManager import SaveManager
from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor


def create_mesh(row_dist=75.0):
    """
    创建一个在试采模型中使用的三维的模型。其中 row_dist是注采两组井之间的距离.
    """
    z_min, z0, z1, z_max = -120.0, -90.0, -30.0, 0.0
    vx = np.linspace(0, row_dist, 38)
    vy = np.linspace(0, row_dist * (43. / 75.), 22)
    vz0 = np.linspace(z_min, z0, 8)
    vz1 = np.linspace(z0, z1, 40)
    vz2 = np.linspace(z1, z_max, 8)
    vz = np.concatenate((vz0, vz1[1:], vz2[1:]))
    return SeepageMesh.create_cube(vx, vy, vz)


def create_ini(z_bottom, z_top):
    """
    创建初始场，用于在建模的时候，对参数进行初始化。
        z2kh: 水平渗透率
        z2kv: 垂直渗透率
    """
    z2k = load_curve('perm.txt')

    def get_k(x, y, z):  # 在各个层位，均使用真实的渗透率
        k_min, k_max = 2.0e-15, 1.0e-13
        kh = clamp(z2k(z), k_min, k_max)
        kv = kh * 0.2
        return Tensor3(xx=kh, yy=kh, zz=kv)

    z0, z1 = -90.0, -30.0  # 水合物层
    p0 = 13.5e6  # 参考点的压力
    t0 = get_hyd_t(p0)  # 参考点的温度

    # 初始温度场
    t_ini = LinearField(v0=t0, z0=z0, dz=-0.04)

    # 初始压力场
    p_ini = LinearField(v0=p0, z0=z0, dz=-0.01e6)

    # 地层数据
    z2s = load_curve('sat_hyd.txt')

    def get_s(x, y, z):
        if z0 <= z <= z1:
            sh = clamp(z2s(z), 0.2, 0.9)  # 最小的饱和度设置为0.4
        else:
            sh = 0
        return (0, 0, 0), (1 - sh, 0), (sh, 0, 0)

    def get_denc(x, y, z):
        return 3e6 if z_bottom + 0.1 < z < z_top - 0.1 else 1e20

    z2f = load_curve('porosity.txt')

    def get_fai(x, y, z):
        if z_bottom + 0.1 < z < z_top - 0.1:
            return clamp(z2f(z), 0.2, 0.6)
        else:
            return 1e8

    return {'porosity': get_fai, 'pore_modulus': 100e6, 'p': p_ini, 'temperature': t_ini,
            'denc': get_denc, 's': get_s, 'perm': get_k, 'heat_cond': 2, 'sample_dist': 0.1}


def create_model(ty_inj=None, q_inj=0.0, t_inj=280.0):
    """
    创建模型. 当注入流体的时候，q_inj的单位是kg/s；当注热热量的时候（ty_inj == 'none'），q_inj的单位是瓦特；
    其中 row_dist是注采两组井之间的距离
    """

    # 创建mesh
    mesh = create_mesh()

    # 创建ini
    z_bottom, z_top = mesh.get_pos_range(2)
    ini = create_ini(z_bottom, z_top)

    # 创建gr
    x, y = create_krf(0.1, 3, k_max=1, s_max=1, count=300)
    gr = Interp1(x=x, y=y)

    # gr绘图
    if gui.exists():
        plotxy(x=x, y=y, caption='gr')

    kwargs = hydrate.create_kwargs(has_co2=True, has_steam=True, has_inh=True,
                                      support_ch4_hyd_form=False, gr=gr)
    kwargs.update(ini)

    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5, count=500)
    # 相渗绘图
    if gui.exists():
        def f(fig):
            ax = fig.subplots()
            ax.plot(vs, kg)
            ax.plot(1 - np.asarray(vs), kw)

        gui.plot(f, caption='kr')

    kwargs.update(create_dict(gravity=(0, 0, -10),
                              dt_max=3600.0 * 24.0, dt_min=10.0, dt_ini=0.01, dv_relative=0.1,
                              kr=[(0, vs, kg), (1, vs, kw)]
                              ))

    # 创建模型
    model = seepage.create(mesh=mesh, **kwargs)

    # 添加虚拟Cell用于生产
    #   注意：这里在x等于1.0e6的位置添加了虚拟裂缝，在后续绘图的时候，不能画这个点
    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)
    pos = (1.0e6, (y_min + y_max) / 2, -30)
    virtual_cell = seepage.add_cell(model, pos=pos, porosity=1.0e3, pore_modulus=100e6, vol=1.0,
                                    temperature=ini['temperature'](*pos), p=3e6,
                                    s=((0, 0, 0), (1, 0), (0, 0, 0)))

    for z in np.linspace(-73, -35, 100):  # 38米的生产区间
        pos = (x_max, y_max, z)
        seepage.add_face(model, virtual_cell, model.get_nearest_cell(pos),
                         heat_cond=0, perm=1.0e-12, area=1.0, length=1.0)

    # 创建压力控制
    t2p = load_txt('pressure_prod_smooth.txt')
    t = t2p[:, 0].flatten()
    p = t2p[:, 1].flatten()
    pre_ctrl = PressureController(virtual_cell, t=t, p=p)
    if gui.exists():
        plotxy(x=t, y=p, caption='t2p')

    # 添加一个单元的监视，以输出生产曲线(注意：这里传递给monitor的时间的单位为天)
    # 必须将pre_ctrl一起监控
    monitor = SeepageCellMonitor(get_t=lambda: seepage.get_time(model),
                                 cell=(virtual_cell, pre_ctrl))

    # 用于流体注入的Cell
    flu_keys = attr_keys.flu_keys(model)
    cell_keys = attr_keys.cell_keys(model)
    if ty_inj is not None:
        cell_ids = []
        for z in np.linspace(-70, -40, 100):
            pos = (x_min, y_min, z)
            id = model.get_nearest_cell(pos).index
            if id not in cell_ids:
                cell_ids.append(id)
        assert len(cell_ids) > 0
        if ty_inj == 'h2o':
            inds = model.find_fludef('h2o')
            assert len(inds) > 0
            q_inj /= len(cell_ids)  # 注意此时是质量流量 kg/s
            for cell_id in cell_ids:
                flu = model.get_cell(cell_id).get_component(inds)
                inj = model.add_injector(cell=cell_id, fluid_id=inds, flu=flu)
                if t_inj is not None:
                    inj.flu.set_attr(flu_keys.temperature, t_inj)
                inj.add_oper(0, q_inj / flu.den)
            assert model.injector_number == len(cell_ids)
        elif ty_inj == 'co2':
            # 注入co2
            inds = model.find_fludef('co2')
            q_inj /= len(cell_ids)  # 注意此时是质量流量 kg/s
            print(f'ty_inj is co2. fluid id is {inds}. count of cells: {len(cell_ids)}. q_inj per cell: {q_inj} kg/s')
            for cell_id in cell_ids:
                flu = model.get_cell(cell_id).get_component(inds)
                inj = model.add_injector(cell=cell_id, fluid_id=inds, flu=flu)
                if t_inj is not None:
                    inj.flu.set_attr(flu_keys.temperature, t_inj)
                inj.add_oper(0, q_inj / flu.den)
            assert model.injector_number == len(cell_ids)
        elif ty_inj == 'none':
            # 仅仅注热
            q_inj /= len(cell_ids)  # 此时是功率
            for cell_id in cell_ids:
                inj = model.add_injector(cell_id, ca_mc=cell_keys.mc, ca_t=cell_keys.temperature)
                inj.add_oper(0, q_inj)
            assert model.injector_number == len(cell_ids)
        else:
            assert False, f'ty_inj = <{ty_inj}> while it should be h2o or co2 or none'

    return model, pre_ctrl, monitor


def solve(model, pre_ctrl, monitor, time_max, folder):
    """
    求解模型，并保存文件
    """
    if folder is not None:
        assert len(folder) > 0
        print_tag(folder)

    y_min, y_max = model.get_pos_range(1)
    cells_for_plot = []
    for cell in model.cells:
        x, y, z = cell.pos
        if abs(y - y_max) < 0.01 and abs(x) < 0.5e6:
            cells_for_plot.append(cell)

    solver = ConjugateGradientSolver()
    solver.set_tolerance(1e-13)

    cell_keys = attr_keys.cell_keys(model)

    iterate = GuiIterator(seepage.iterate,
                          lambda: plot_all(time=seepage.get_time(model),
                                           cells=cells_for_plot,
                                           monitor=monitor,
                                           folder=None,
                                           cell_keys=cell_keys))

    def get_day():
        """
        获得保存文件的时候所使用的时间（用于生成文件名）
        """
        return seepage.get_time(model) / (3600 * 24)

    def get_save_dday(days):
        """
        返回数据保存的时间间隔
        """
        if days < 7:
            return max(0.2, days * 0.1)
        else:
            return min(60.0, max(0.2, days * 0.2))

    save_model = SaveManager(join_paths(folder, 'model'),
                             get_save_dday,
                             get_day, save=model.save, ext='.dat', time_unit='d')

    save_cells = SaveManager(join_paths(folder, 'cells'),
                             get_save_dday,
                             get_day, save=lambda path: seepage.print_cells(path, model), ext='.txt', time_unit='d')

    save_figs = SaveManager(None,
                            get_save_dday,
                            get_day,
                            save=lambda _: plot_all(time=seepage.get_time(model),
                                                    cells=cells_for_plot,
                                                    monitor=monitor,
                                                    folder=folder,
                                                    cell_keys=cell_keys))

    save_prod = SaveManager(None,
                            get_save_dday,
                            get_day,
                            save=lambda _: monitor.save(join_paths(folder, 'prod.txt')))

    def save(**kwargs):
        save_model(**kwargs)
        save_cells(**kwargs)
        save_figs(**kwargs)
        save_prod(**kwargs)

    while seepage.get_time(model) < time_max:
        years = seepage.get_time(model) / (3600 * 24 * 365)
        seepage.set_dv_relative(model, clamp(years / 5, 0.1, 0.8))
        pre_ctrl.update(seepage.get_time(model))  # 确保边界压力
        if seepage.get_time(model) / (24 * 3600) > 10:
            iterate.ratio = 0.001
        else:
            iterate.ratio = 0.2
        r = iterate(model, solver=solver)
        monitor.update(dt=0.1)
        save()
        step = seepage.get_step(model)
        if step % 10 == 0:
            if gui.exists():
                print(
                    f'step = {step}, dt = {time2str(seepage.get_dt(model))}, '
                    f'time = {time2str(seepage.get_time(model))}, '
                    f'report={r}')
            else:
                print(
                    f'{folder}: step = {step}, '
                    f'dt = {time2str(seepage.get_dt(model))}, '
                    f'time = {time2str(seepage.get_time(model))}, '
                    f'report={r}')

    # 保存最终的状态
    save(check_dt=False)


def plot_all(time, cells, monitor, folder, cell_keys):
    """
    在界面上绘图。如果给定了folder，则在folder内创建figures文件夹，并在文件夹内保存绘图文件
    """
    if not gui.exists() or not is_windows:
        # 如果不存在GUI界面，则没有执行此函数的必要(非GUI模式下，可能会有内存泄漏)
        return

    kwargs = {'gui_only': False, 'title': f'plot when model.time={time2str(time)}'}
    x, y = [cell.pos[0] for cell in cells], [cell.pos[2] for cell in cells]

    # 绘制云图
    def get_path(name):
        if folder is not None:
            return os.path.join(folder, 'figures', name)

    def fig_name(key):
        return make_fname(time / (3600 * 24), folder=get_path(key), ext='.jpg', unit='d')

    def get_s(c, i0, i1):
        f = c.get_fluid(i0)
        return f.vol_fraction * f.get_component(i1).vol / max(f.vol, 1.0e-20)

    vp = [c.get_attr(cell_keys['pre']) for c in cells]
    vt = [c.get_attr(cell_keys['temperature']) for c in cells]

    tricontourf(x, y,
                vp,
                caption='压力',
                fname=fig_name('pressure'), **kwargs)
    tricontourf(x, y,
                vt,
                caption='温度',
                fname=fig_name('temperature'),
                **kwargs)

    tricontourf(x, y, [get_s(c, 0, 0) for c in cells], caption='甲烷饱和度',
                fname=fig_name('s_ch4'),
                **kwargs)
    tricontourf(x, y, [get_s(c, 0, 1) for c in cells], caption='co2饱和度',
                fname=fig_name('s_co2'),
                **kwargs)
    tricontourf(x, y, [c.get_fluid(1).vol_fraction for c in cells], caption='水饱和度',
                fname=fig_name('s_liq'),
                **kwargs)
    # 固体和总的饱和度
    tricontourf(x, y, [get_s(c, 2, 0) for c in cells], caption='水合物饱和度',
                fname=fig_name('s_ch4_hyd'),
                **kwargs)
    tricontourf(x, y, [get_s(c, 2, 1) for c in cells], caption='冰饱和度',
                fname=fig_name('s_ice'),
                **kwargs)
    tricontourf(x, y, [get_s(c, 2, 2) for c in cells], caption='CO2水合物饱和度',
                fname=fig_name('s_co2_hyd'),
                **kwargs)

    # 产气速率
    rate_gas = load_txt('prod_rate_gas.txt')
    x1 = rate_gas[:, 0] / (3600 * 24)
    y1 = rate_gas[:, 1] * 3600 * 24 / 0.716
    x2, y2 = monitor.get_rate(0, np=np)
    x2 = x2 / (3600 * 24)
    y2 = y2 * 4 * 3600 * 24 / 0.716
    mask = x2 > 0.3
    if sum(mask) > 2:
        x2 = x2[mask]
        y2 = y2[mask]
        plot2(data=[{'name': 'plot', 'args': [x1, y1]},
                    {'name': 'plot', 'args': [x2, y2]}],
              caption='产气速率',
              fname=fig_name('gas_rate'), **kwargs)

    # 产水速率
    rate_wat = load_txt('prod_rate_water.txt')
    x1 = rate_wat[:, 0] / (3600 * 24)
    y1 = rate_wat[:, 1] * 3600 * 24 / 1000.0
    x2, y2 = monitor.get_rate(3, np=np)
    x2 = x2 / (3600 * 24)
    y2 = y2 * 4 * 3600 * 24 / 1000.0
    mask = x2 > 0.3
    if sum(mask) > 2:
        x2 = x2[mask]
        y2 = y2[mask]
        plot2(data=[{'name': 'plot', 'args': [x1, y1]},
                    {'name': 'plot', 'args': [x2, y2]}],
              caption='产水速率',
              fname=fig_name('wat_rate'), **kwargs)


def flu_inj(power=0.0, q_inj=0.0, time_max=3600 * 24 * 365 * 5,
            ty_inj='h2o', inj_t0=285.0, folder=None):
    """
    利用给定的注入功率和流体注入流量来运行注入流体的开发过程.
    这里power的单位kw；qinj的单位为m^3/day (注意，这里的体积，是按照标准大气压下的密度来计算的);
    其中inj_t0为注入流体在加热之前的温度，这个非常重要，直接决定了加热之后的温度多高;
    """
    assert 0.0 <= power <= 10000
    if ty_inj == 'h2o' or ty_inj == 'co2':
        assert 0.0 <= q_inj <= 1.0e8, f'The q_inj <{q_inj} m^3/day> is not permitted'

    # 将单位转化为标准单位
    power *= 1.0e3

    if ty_inj == 'h2o' or ty_inj == 'co2':
        specific_heat, density = (4200.0, 1000.0) if ty_inj == 'h2o' else (2844.8, 1.997)  # 按照标准大气压下面的密度来计算
        q_inj *= (density / (24 * 3600))
        q_inj = max(1.0e-3, q_inj)
        tinj = power / (q_inj * specific_heat) + inj_t0
    else:
        assert ty_inj == 'none'
        q_inj = power  # qinj代表功率
        tinj = None

    print(f'folder=<{folder}>, q_inj={q_inj}, tinj={tinj}')

    if gui.exists():
        gui.title(f'Output: {folder}')

    model, pre_ctrl, monitor = create_model(ty_inj=ty_inj, q_inj=q_inj, t_inj=tinj)
    solve(model, pre_ctrl, monitor, folder=folder, time_max=time_max)


def h2o_inj(**kwargs):
    kwargs['ty_inj'] = 'h2o'
    return flu_inj(**kwargs)


def vap_inj(power=0.0, **kwargs):
    qinj = (power * 1.0e3 * 24 * 3600 / 2.26e6) / 1000.0
    kwargs['power'] = power
    kwargs['q_inj'] = qinj
    h2o_inj(**kwargs)


def co2_inj(**kwargs):
    kwargs['ty_inj'] = 'co2'
    return flu_inj(**kwargs)


def heat_inj(**kwargs):
    """
    执行注热：此时qinj代表加热的功率
    """
    kwargs['ty_inj'] = 'none'
    return flu_inj(**kwargs)


if __name__ == '__main__':
    gui.execute(h2o_inj, close_after_done=False, kwargs=create_dict(folder=opath('japan13', 'test'),
                                                                    time_max=3600 * 24 * 7),
                disable_gui=False)
