# ** desc = '测试：纵向二维。浮力作用下气体运移、水合物成藏过程模拟(基于 zmlx.config.seepage)'

from zmlx import *
from zmlx.filesys.make_fname import make_fname
from zmlx.config import hydrate_v2
from zmlx.config import seepage


def create():
    mesh = SeepageMesh.create_cube(np.linspace(0, 300, 150), np.linspace(0, 500, 250), (-0.5, 0.5))

    def get_initial_t(x, y, z):
        return 278 + 22.15 - 0.0443 * y

    def get_initial_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * y

    def get_initial_s(x, y, z):
        if get_distance((x, y, z), (150, 100, 0)) < 50:
            return (1,), (0,), (0, 0)
        else:
            return (0,), (1,), (0, 0)

    y0, y1 = mesh.get_pos_range(1)

    def get_denc(x, y, z):
        if abs(y - y0) < 0.1 or abs(y - y1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_perm(x, y, z):
        if abs(x - 150) < 20:
            return 1.0e-13
        else:
            return 1.0e-15

    cfg = hydrate_v2.Config(has_inh=True,  # 存在抑制剂
                            has_ch4_in_liq=True  # 存在溶解气
                            )
    kw = cfg.kwargs
    kw.update(create_dict(mesh=mesh, porosity=0.1, pore_modulus=100e6, denc=get_denc, dist=0.1,
                          temperature=get_initial_t, p=get_initial_p, s=get_initial_s,
                          perm=get_perm, heat_cond=2.0))
    return seepage.create(**kw)


def show(model: Seepage, folder=None):
    """
    绘图，且当folder给定的时候，将绘图结果保存到给定的文件夹
    """
    if not gui.exists():
        return
    time = seepage.get_time(model)
    kwargs = {'title': f'plot when model.time={time2str(time)}'}
    x = model.numpy.cells.x
    y = model.numpy.cells.y

    def fname(key):
        return make_fname(time / (3600 * 24 * 365), folder=join_paths(folder, key), ext='.jpg', unit='y')

    cell_keys = seepage.cell_keys(model)

    def show_key(key):
        tricontourf(x, y, model.numpy.cells.get(cell_keys[key]), caption=key,
                    fname=fname(key), **kwargs)

    show_key('pre')
    show_key('temperature')

    fv_all = model.numpy.cells.fluid_vol

    def show_s(flu_name):
        s = model.numpy.fluids(*model.find_fludef(flu_name)).vol / fv_all
        tricontourf(x, y, s, caption=flu_name, fname=fname(flu_name), **kwargs)

    for item in ['ch4', 'liq', 'ch4_hydrate']:
        show_s(item)


def solve(model, folder=None):
    """
    执行求解，并将结果保存到指定的文件夹
    """
    iterate = GuiIterator(seepage.iterate, plot=lambda: show(model, folder=join_paths(folder, 'figures')))

    # get_time: 返回当前时间，单元：年
    # dtime: 返回给定时刻保存数据的时间间隔<时间单元同get_time>. 此处为: 随着time增大，保存的间隔增大，但最大不超过5年，最小不小于0.1年
    save = SaveManager(join_paths(folder, 'seepage'), save=model.save, ext='.seepage', time_unit='y',
                       dtime=lambda time: min(5.0, max(0.1, time * 0.1)),
                       get_time=lambda: seepage.get_time(model) / (3600 * 24 * 365),
                       )

    for step in range(10000):
        iterate(model)
        save()
        if step % 10 == 0:
            dt = time2str(seepage.get_dt(model))
            time = time2str(seepage.get_time(model))
            print(f'step = {step}, dt = {dt}, time = {time}')
    show(model, folder=join_paths(folder, 'figures'))
    save(check_dt=False)  # 保存最终状态
    information('计算结束', iterate.time_info())


def execute(gui_mode=True, close_after_done=False):
    gui.execute(solve, close_after_done=close_after_done,
                args=(create(), 'HydForm'), disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
