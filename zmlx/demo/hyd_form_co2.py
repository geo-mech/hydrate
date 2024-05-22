# ** desc = '测试：纵向二维。浮力作用下气体运移、水合物成藏过程模拟(co2)'

import numpy as np

from zml import get_distance, create_dict, Seepage, core
from zmlx.alg.time2str import time2str
from zmlx.config import hydrate, seepage
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_fname import make_fname
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui.GuiBuffer import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.SaveManager import SaveManager
from zmlx.utility.SeepageNumpy import as_numpy
from zmlx.seepage_mesh.cube import create_cube


def create():
    mesh = create_cube(x=np.linspace(0, 200, 100),
                       y=(-0.5, 0.5),
                       z=np.linspace(-300, 0, 150))

    def get_initial_t(x, y, z):
        return 275 - 0.0443 * z

    def get_initial_p(x, y, z):
        return 15e6 - 1e4 * z

    def get_initial_s(x, y, z):
        if get_distance((x, z), (100, -350)) < 80:
            return {'co2': 1}
        else:
            return {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_perm(x, y, z):
        if abs(x - 100) < 20:
            return 1.0e-14
        else:
            return 1.0e-15

    kw = hydrate.create_kwargs(has_inh=True,  # 存在抑制剂
                               gravity=[0, 0, -10],
                               has_co2=True,
                               has_co2_in_liq=True,
                               )
    kw.update(create_dict(mesh=mesh, porosity=0.1, pore_modulus=100e6,
                          denc=get_denc, dist=0.1,
                          temperature=get_initial_t,
                          p=get_initial_p,
                          s=get_initial_s,
                          perm=get_perm, heat_cond=2.0,
                          dt_max=3600*24*5,  # 允许的最大的时间步长
                          dv_relative=0.1,  # 每一步流体流体的距离与网格大小的比值
                          ))
    model = seepage.create(**kw)

    # 设置co2的溶解度
    key = model.get_cell_key('n_co2_sol')
    for cell in model.cells:
        cell.set_attr(key, 0.06)

    # 返回创建的模型.
    return model


def show(model: Seepage, folder=None):
    """
    绘图，且当folder给定的时候，将绘图结果保存到给定的文件夹
    """
    if not gui.exists():
        return
    time = seepage.get_time(model)
    kwargs = {'title': f'plot when time={time2str(time)}'}
    x = as_numpy(model).cells.x
    z = as_numpy(model).cells.z

    def fname(key):
        return make_fname(time / (3600 * 24 * 365),
                          folder=join_paths(folder, key),
                          ext='.jpg', unit='y')

    cell_keys = seepage.cell_keys(model)

    def show_key(key):
        tricontourf(x, z, as_numpy(model).cells.get(cell_keys[key]),
                    caption=key,
                    fname=fname(key), **kwargs)

    show_key('pre')
    show_key('temperature')

    fv_all = as_numpy(model).cells.fluid_vol

    def show_s(flu_name):
        s = as_numpy(model).fluids(*model.find_fludef(flu_name)).vol / fv_all
        tricontourf(x, z, s, caption=flu_name,
                    fname=fname(flu_name), **kwargs)

    for item in ['co2', 'co2_in_liq', 'liq', 'co2_hydrate']:
        show_s(item)


def solve(model, folder=None, step_max=None):
    """
    执行求解，并将结果保存到指定的文件夹
    """
    iterate = GuiIterator(seepage.iterate,
                          plot=lambda: show(model,
                                            folder=join_paths(folder, 'figures')))

    # get_time: 返回当前时间，单元：年
    # dtime: 返回给定时刻保存数据的时间间隔<时间单元同get_time>. 此处为: 随着time增大，保存的间隔增大，但最大不超过5年，最小不小于0.1年
    save = SaveManager(join_paths(folder, 'seepage'), save=model.save, ext='.seepage', time_unit='y',
                       dtime=lambda time: min(5.0, max(0.1, time * 0.1)),
                       get_time=lambda: seepage.get_time(model) / (3600 * 24 * 365),
                       )

    if step_max is None:
        step_max = 10000

    for step in range(step_max):
        iterate(model)
        save()
        if step % 10 == 0:
            print(f'step = {step}, dt = {seepage.get_dt(model, as_str=True)}, '
                  f'time = {seepage.get_time(model, as_str=True)}')
    show(model, folder=join_paths(folder, 'figures'))
    save(check_dt=False)  # 保存最终状态
    print(iterate.time_info())


def execute(folder=None, step_max=None, gui_mode=False,
            close_after_done=False):

    def f():
        model = create()
        solve(model, folder=folder, step_max=step_max)

    gui.execute(f, close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute(gui_mode=True)

