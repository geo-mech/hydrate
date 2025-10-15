# ** desc = '测试：纵向二维。浮力作用下co2及ch4气体运移、ch4水合物及co2水合物成藏过程模拟'

from zmlx import *


def create():
    # 创建网格：
    #   在x方向上，从-150到150的范围内，划分为150个网格
    #   在z方向上，从-400到0的范围内，划分为200个网格
    mesh = create_cube(
        x=np.linspace(-150, 150, 150),
        y=(-0.5, 0.5),
        z=np.linspace(-400, 0, 200))

    def get_initial_t(x, y, z):
        """
        初始的温度场
        """
        return 277 - z * 0.04

    def get_initial_p(x, y, z):
        """
        初始的压力场
        """
        return 15e6 - 1e4 * z

    def get_initial_s(x, y, z):
        """
        初始的饱和度场. 这里，假设在靠近底部的一个圆形区域内为气体，其它位置为液体
        """
        if get_distance((x, z), (0, -420)) < 80:
            return {'ch4': 0.6, 'co2': 0.4}  # 假设co2和ch4共存
        else:
            return {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        """
        土体密度和比热的乘积. 在模型的顶部和底部，将此设置为无穷大，来固定温度
        """
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    kw = hydrate.create_kwargs(
        has_inh=True,  # 存在抑制剂
        has_ch4_in_liq=True,  # 存在溶解气
        gravity=[0, 0, -10],
        has_co2=True,  # 存在co2
    )
    kw.update(dict(
        mesh=mesh, porosity=0.1,
        pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_initial_t,
        p=get_initial_p,
        s=get_initial_s,
        perm=1.0e-15,
        heat_cond=2.0,
        dv_relative=0.5,  # 一个时间步内，流体最多走过0.5个网格
        dt_max=3600 * 24 * 365,
    ))

    # 创建模型，返回Seepage对象
    return seepage.create(**kw)


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
        tricontourf(x, z,
                    as_numpy(model).cells.get(cell_keys[key]),
                    caption=key,
                    fname=fname(key), **kwargs)

    show_key('pre')
    show_key('temperature')

    fv_all = as_numpy(model).cells.fluid_vol

    def show_s(flu_name):
        s = as_numpy(model).fluids(*model.find_fludef(flu_name)).vol / fv_all
        tricontourf(x, z, s, caption=flu_name,
                    fname=fname(flu_name), **kwargs)

    for item in ['ch4', 'co2', 'liq', 'ch4_hydrate', 'co2_hydrate']:
        show_s(item)


def solve(model, folder=None, step_max=None):
    """
    执行求解，并将结果保存到指定的文件夹
    """
    solver = ConjugateGradientSolver(tolerance=1.0e-30)

    iterate = GuiIterator(
        lambda m: seepage.iterate(m, solver=solver),
        plot=lambda: show(
            model,
            folder=join_paths(folder, 'figures')))

    # get_time: 返回当前时间，单元：年
    # dtime: 返回给定时刻保存数据的时间间隔<时间单元同get_time>.
    #   此处为: 随着time增大，保存的间隔增大，但最大不超过5年，最小不小于0.1年
    save = SaveManager(
        join_paths(folder, 'seepage'),
        save=model.save,
        ext='.seepage',
        time_unit='y',
        dtime=lambda time: min(5.0, max(0.1, time * 0.1)),
        get_time=lambda: seepage.get_time(model) / (
                3600 * 24 * 365),
    )

    if step_max is None:
        step_max = 10000

    for step in range(step_max):
        iterate(model)
        save()
        if step % 10 == 0:
            print(f'step = {step}, '
                  f'dt = {seepage.get_dt(model, as_str=True)}, '
                  f'time = {seepage.get_time(model, as_str=True)}')
    show(model, folder=join_paths(folder, 'figures'))
    save(check_dt=False)  # 保存最终状态
    print(iterate.time_info())


def execute(folder=None, step_max=None, gui_mode=False,
            close_after_done=False,
            parallel_enabled=True):
    """
    执行建模和求解全过程
    """
    core.parallel_enabled = parallel_enabled

    def f():
        model = create()
        solve(model, folder=folder, step_max=step_max)

    gui.execute(f, close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute(gui_mode=True)
