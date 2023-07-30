"""
测试：纵向二维。浮力作用下气体运移成藏过程模拟。
"""

from zmlx import *
from zmlx.alg.make_fname import make_fname


def create():
    mesh = SeepageMesh.create_cube(np.linspace(0, 300, 150), np.linspace(0, 500, 250), (-0.5, 0.5))
    config = create_hydconfig(has_inh=True,  # 存在抑制剂
                              has_ch4_in_liq=True  # 存在溶解气
                              )
    config.dt_max = 3600 * 24

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

    model = config.create(mesh, porosity=0.1, pore_modulus=100e6, denc=get_denc, dist=0.1,
                          temperature=get_initial_t, p=get_initial_p, s=get_initial_s,
                          perm=get_perm, heat_cond=2.0)

    return config, model


def show(config, model, folder=None):
    """
    绘图，且当folder给定的时候，将绘图结果保存到给定的文件夹
    """
    time = config.get_time(model)
    kwargs = {'gui_only': True, 'title': f'plot when model.time={time2str(time)}'}
    x = model.numpy.cells.x
    y = model.numpy.cells.y

    def fname(key):
        return make_fname(time / (3600 * 24 * 365), folder=join_paths(folder, key), ext='.jpg', unit='y')

    tricontourf(x, y, model.numpy.cells.get(config.cell_keys['pre']), caption='压力',
                fname=fname('pressure'), **kwargs)
    tricontourf(x, y, model.numpy.cells.get(config.cell_keys['temperature']), caption='温度',
                fname=fname('temperature'), **kwargs)
    vg = model.numpy.fluids(config.igas).vol
    vl = model.numpy.fluids(config.iliq).vol
    vs = model.numpy.fluids(config.isol).vol
    vv = vg + vl + vs
    tricontourf(x, y, vg / vv, caption='气饱和度', fname=fname('gas'), **kwargs)
    tricontourf(x, y, vl / vv, caption='水饱和度', fname=fname('wat'), **kwargs)
    tricontourf(x, y, vs / vv, caption='水合物饱和度', fname=fname('hyd'), **kwargs)


def solve(config, model, folder=None):
    """
    执行求解，并将结果保存到指定的文件夹
    """
    iterate = GuiIterator(config.iterate, plot=lambda: show(config, model, folder=join_paths(folder, 'figures')))

    # get_time: 返回当前时间，单元：年
    # dtime: 返回给定时刻保存数据的时间间隔<时间单元同get_time>. 此处为: 随着time增大，保存的间隔增大，但最大不超过5年，最小不小于0.1年
    save = SaveManager(join_paths(folder, 'seepage'), save=model.save, ext='.seepage', time_unit='y',
                       dtime=lambda time: min(5.0, max(0.1, time * 0.1)),
                       get_time=lambda: config.get_time(model) / (3600 * 24 * 365),
                       )

    for step in range(10000):
        iterate(model)
        save()
        if step % 10 == 0:
            dt = time2str(config.get_dt(model))
            time = time2str(config.get_time(model))
            print(f'step = {step}, dt = {dt}, time = {time}')
    show(config, model, folder=join_paths(folder, 'figures'))
    save(check_dt=False)  # 保存最终状态
    information('计算结束', iterate.time_info())


def execute(gui_mode=True, close_after_done=False):
    config, model = create()
    if gui_mode:
        gui.execute(solve, close_after_done=close_after_done,
                    args=(config, model, 'HydForm'))
    else:
        solve(config, model, 'HydForm')


if __name__ == '__main__':
    execute()
