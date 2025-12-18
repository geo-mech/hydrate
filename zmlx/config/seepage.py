"""
基于Seepage，定义热-流-化耦合的公共的函数.

模型的属性关键词有：
    dt: 时间步长
    time: 时间
    step: 迭代步
    dv_relative：每一步走过的距离与网格尺寸的比值（用以控制时间步长），默认0.1
    dt_min：时间步长的最小值，单位：秒；默认：1.0e-15
    dt_max：时间步长的最大值，单位：秒；默认：1.0e10

模型的tag：
    disable_update_den：是否禁止更新密度
    disable_update_vis：是否禁止更新粘性
    has_solid：是否有固体；如果有，那么只能允许最后一个流体为固体
    disable_flow：是否禁止流动计算
    disable_ther：是否禁止传热计算
    disable_heat_exchange：禁止流体和固体之间的热交换
    disable_update_dt：禁止更新时间不长dt

流体的属性关键词:
    temperature: 温度
    specific_heat: 比热

Cell的属性:
    temperature: 温度
    mc：质量和比热的乘积
    pre：流体的压力：用来存储迭代计算的压力结果，可能和利用流体体积和孔隙弹性计算的压力略有不同
    fv0：流体体积的初始值（和初始的g0对应的数值）
    g_heat：流体和固体热交换的系数
    vol：网格的体积(此体积乘以孔隙度，得到孔隙的体积)
    temp_variable: 临时变量，用来存储迭代计算的中间结果

Face的属性：
    area：横截面积。（当考虑流体的惯性的时候，也将使用此面积来计算作用在流体上的“冲量”，从而改变流体的动量）;
    length：长度（流体经过这个face需要流过的距离）;
    g0：初始时刻的导流系数;
    igr：导流系数的相对曲线的id（用来修正孔隙空间大小改变所带来的渗透率的改变）;
    g_heat：用于传热计算的导流系数（注意，并非热传导系数。这个系数，已经考虑了face的横截面积和长度）;
    perm: face位置的渗透率;
    rate: 流体流动的速率(用以计算流体的惯性);
    inertia: 惯性系数. 使用速率rate乘以此系数，则得到流体的动量（=m*v）. 根据Face的area*Face两侧的压力差，计算作用力，从而计算动量的
             变量速度。当Face同时定义了rate和inertia之后，才可以去考虑惯性效应。
"""
from collections.abc import Iterable
from typing import Optional

from zml import (
    get_average_perm, Tensor3, make_parent, SeepageMesh)
from zmlx.alg.base import clamp, join_cols
from zmlx.alg.fsys import join_paths, print_tag
from zmlx.base.seepage import *
from zmlx.config import (
    capillary, prod, fluid_heating, timer,
    sand, step_iteration, diffusion, solid_buffer, fluid, injector, cond
)
from zmlx.config.alg import merge_opts
from zmlx.config.attr_keys import cell_keys, face_keys, flu_keys
from zmlx.geometry.base import point_distance
from zmlx.plt.cells import show_cells
from zmlx.react.alg import add_reaction
from zmlx.ui import gui
from zmlx.utility.fields import Field
from zmlx.utility.gui_iterator import GuiIterator
from zmlx.utility.save_manager import SaveManager
from zmlx.utility.seepage_cell_monitor import SeepageCellMonitor


@clock
def _apply_diffusions(*models):
    """
    应用模型中的扩散计算

    Args:
        *models: Seepage 模型对象列表

    Returns:
        None

    该函数通过遍历模型列表，检查每个模型是否有定义的扩散计算（通过检查 diffusions 是否为空）。
    如果满足条件，则调用模型的 get_diffusion 方法获取扩散计算对象，并使用模型的时间步长（dt）
    调用扩散计算对象的 react 方法进行扩散计算。
    """
    for model in models:
        diffusions = model.temps.get('diffusions')
        if diffusions is None:
            continue
        for update in diffusions:
            update(model, get_dt(model))


@clock
def _exchange_heat(*models, pool=None):
    """
    模型中流体和固体之间交换热

    Args:
        models: Seepage 模型对象列表
        pool: 可选的线程池对象，用于并行计算（默认为 None）

    Returns:
        None

    该函数通过遍历模型列表，检查每个模型是否启用了热交换功能（通过检查标签 'disable_heat_exchange'），
    并检查模型中是否有定义的流体定义（通过检查 fludef_number 是否大于 0）。如果满足条件，则调用模型的
    exchange_heat 方法进行热交换计算。计算时使用模型的时间步长（dt），以及热交换相关的单元格属性键
    （ca_g, ca_t, ca_mc）和流体属性键（fa_t, fa_c）。如果提供了线程池对象，则并行计算热交换。
    """
    if len(models) <= 1:
        pool = None

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        if model.not_has_tag('disable_heat_exchange') and model.fludef_number > 0:
            model.exchange_heat(
                dt=get_dt(model),
                ca_g=model.get_cell_key('g_heat'),
                ca_t=model.get_cell_key('temperature'),
                ca_mc=model.get_cell_key('mc'),
                fa_t=model.get_flu_key('temperature'),
                fa_c=model.get_flu_key('specific_heat'),
                pool=pool
            )

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕


@clock
def _apply_reactions(*models, pool=None):
    """
    应用模型中的化学反应

    Args:
        *models: Seepage 模型对象列表
        pool: 可选的线程池对象，用于并行计算（默认为 None）

    Returns:
        None

    该函数通过遍历模型列表，检查每个模型是否有定义的化学反应（通过检查 reaction_number 是否大于 0）。
    如果满足条件，则调用模型的 get_reaction 方法获取化学反应对象，并使用模型的时间步长（dt）和其他参数
    调用化学反应对象的 react 方法进行化学反应计算。如果提供了线程池对象，则并行计算化学反应。
    """
    if len(models) <= 1:
        pool = None

    reaction_number = 0
    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        reaction_number = max(reaction_number, model.reaction_number)

    for idx in range(reaction_number):
        for model in models:
            assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
            opts = model.temps['iterate_opts']
            if idx < model.reaction_number:
                reaction = model.get_reaction(idx)
                assert isinstance(reaction, Seepage.Reaction)
                react_bufs = opts.get('react_bufs')
                buf = None
                if react_bufs is not None:
                    if idx < len(react_bufs):
                        # 使用这个buf
                        #   (必须确保这个buf是一个double类型的指针，并且长度等于cell_number)
                        buf = react_bufs[idx]
                reaction.react(model, get_dt(model), buf=buf, pool=pool)

        if isinstance(pool, ThreadPool):
            pool.sync()  # 等待放入pool中的任务执行完毕


@clock
def _update_time_state(*models):
    """
    更新模型的时间状态

    Args:
        *models: Seepage 模型对象列表

    Returns:
        None

    该函数通过遍历模型列表，检查每个模型是否为 Seepage 类型。如果满足条件，则调用模型的 set_time 方法
    更新模型的时间为当前时间加上时间步长（dt），并调用 set_step 方法将模型的步数增加 1。
    """
    # 更新模型的状态
    for model in models:
        assert isinstance(model, Seepage)
        set_time(model, get_time(model) + get_dt(model))
        set_step(model, get_step(model) + 1)


@clock
def _update_dt(*models):
    """
    更新模型的时间步长（dt）

    Args:
        *models: Seepage 模型对象列表

    Returns:
        None

    该函数通过遍历模型列表，检查每个模型是否启用了更新时间步长功能（通过检查标签 'disable_update_dt'）。
    如果满足条件，则跳过该模型。否则，根据模型中定义的流、热和扩散等物理量，计算下一步建议的时间步长（dt）。
    建议的时间步长取所有计算结果中的最小值，并确保在最小和最大时间步长之间。最后，调用模型的 set_dt 方法
    更新模型的时间步长为建议值。
    """
    for model in models:
        assert isinstance(model, Seepage)
        if model.has_tag('disable_update_dt'):
            continue

        recommended_dts = []
        dt = get_flow_dt_next(model)
        if dt > 0:
            recommended_dts.append(dt)

        dt = get_thermal_dt_next(model)
        if dt > 0:
            recommended_dts.append(dt)

        dt = diffusion.get_dt_next(model)
        if dt > 0:
            recommended_dts.append(dt)

        if len(recommended_dts) > 0:
            if len(recommended_dts) > 1:
                recommended_dt = min(*recommended_dts)
            else:
                recommended_dt = recommended_dts[0]
            dt = max(get_dt_min(model), min(get_dt_max(model), recommended_dt))
            set_dt(model, dt)  # 修改dt为下一步建议使用的值


def iterate(*local_opts, pool=None, **global_opts):
    """
    在时间上向前并行地迭代一次

    Args:
        *local_opts: 每个模型的迭代选项字典，或者 Seepage 模型对象
        pool: 线程池对象，用于并行处理模型迭代
        **global_opts: 全局迭代选项字典

    Returns:
        int: 执行迭代的模型的数量
    """
    if gui.exists():  # 添加断点，从而使得在这里可以暂停和终止
        gui.break_point()

    models = []

    for local_opt in local_opts:
        # 解析出model
        if isinstance(local_opt, dict):
            local_opt = local_opt.copy()  # 使得这个列表，后续还可以使用
            model = local_opt.pop('model', None)
            assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        else:
            assert isinstance(local_opt, Seepage), f'The model is not Seepage. model = {local_opt}'
            model = local_opt
            local_opt = {}

        # 所有用来迭代的选项
        opts = merge_opts(global_opts, local_opt)

        # 判断是否满足迭代的条件
        condition = opts.pop('condition', None)
        if callable(condition):
            if not condition(model):  # 不满足需要迭代的条件，则直接退出迭代
                continue

        time_max = opts.pop('time_max', None)  # 允许时间的最大值
        if time_max is not None:
            if get_time(model) >= time_max:
                continue

        # 设置slots
        model.temps['slots'] = merge_opts(
            global_opts.get('slots'), local_opt.get('slots'))

        # 设置cond_updaters
        model.temps['cond_updaters'] = opts.get('cond_updaters')

        # 设置额外的diffusions
        model.temps['diffusions'] = opts.get('diffusions')

        # 迭代的选项
        model.temps['iterate_opts'] = opts

        dt = opts.get('dt')
        if dt is not None:  # 在参数中给定了dt，则直接使用给定的dt
            set_dt(model, dt)

        # 记录模型，这些模型将在后续被迭代
        models.append(model)

    if len(models) == 0:  # 不需要迭代
        return 0

    if len(models) <= 1:  # 不需要并行
        pool = None

    # 执行定时器函数 (此过程会读取model.temps['slots'])
    timer.iterate(*models)

    # 执行step迭代 (读取model.temps['slots'])
    step_iteration.iterate(*models)

    # 迭代流体的性质
    fluid.iterate(*models, pool=pool)

    # 流体注入
    injector.iterate(*models, pool=pool)

    # 尝试修改边界的压力，从而使得流体生产 (使用模型内部定义的time)
    #   since 2024-6-12
    prod.iterate(*models)

    # 对流体进行加热
    fluid_heating.iterate(*models)

    # 备份固体
    #  注意，在solid_buffer.backup和solid_buffer.restore之间，最后一种物质不存在
    solid_buffer.backup(*models, pool=pool)

    # 更新cond(基于gr以及cond_updaters)
    cond.iterate(*models, pool=pool)

    # 迭代流体
    iterate_flow(*models, pool=pool, recommend_dt=True)

    # 执行所有的扩散操作，这一步需要在没有固体存在的条件下进行
    _apply_diffusions(*models)

    # 执行毛管力相关的操作
    capillary.iterate(*models)

    # 执行新版本的扩散操作
    diffusion.iterate(*models, pool=pool, recommend_dt=True)

    # 恢复备份的固体
    solid_buffer.restore(*models, pool=pool)

    # 更新砂子的体积（检查在slots中是否有自定义的update_sand）
    sand.iterate(*models, check_slots=True)

    # 更新传热
    iterate_thermal(*models, pool=pool, recommend_dt=True)

    # 热交换
    _exchange_heat(*models, pool=pool)

    # 化学反应
    _apply_reactions(*models, pool=pool)

    # 更新模型的状态
    _update_time_state(*models)

    # 更新时间步长（设置动态时间步长）
    _update_dt(*models)

    return len(models)  # 执行迭代的model的数量


def parallel_iterate(*args, **kwargs):
    warnings.warn(
        'parallel_iterate is deprecated (will be removed after 2026-12-9), use iterate instead',
        DeprecationWarning, stacklevel=2)
    return iterate(*args, **kwargs)


def iterate_until(*local_opts, pool=None, target_time=None, n_loop_max=None, **global_opts):
    """
    并行地迭代，直到给定的目标时间
    """
    if target_time is not None:
        def condition(m: Seepage):
            return get_time(m) < target_time
    else:
        condition = None

    if n_loop_max is None:
        n_loop_max = 9999999999

    n_iter = 0
    for n_loop in range(n_loop_max):
        n = iterate(*local_opts, pool=pool, condition=condition, **global_opts)
        if n == 0:
            return n_loop, n_iter
        else:
            n_iter += n
    return n_loop_max, n_iter


def parallel_sync(*args, **kwargs):
    """
    并行地迭代，直到给定的目标时间
    """
    warnings.warn(
        'parallel_sync is deprecated (will be removed after 2026-12-9), use iterate_until instead',
        DeprecationWarning, stacklevel=2)
    return iterate_until(*args, **kwargs)


def print_cells(path, model, ca_keys=None, fa_keys=None,
                fmt='%.18e', export_mass=False):
    """
    输出cell的属性（前三列固定为x y z坐标）. 默认第4列为pre，
            第5列温度，第6列为流体总体积，后面依次为各流体组分的体积饱和度.
    最后是ca_keys所定义的额外的Cell属性.

    注意：
        当export_mass为True的时候，则输出质量（第6列为总质量），
        后面的饱和度为质量的比例 （否则为体积）.
    """
    assert isinstance(model, Seepage)
    if path is None:
        return

    # 找到所有的流体的ID
    fluid_ids = []
    for i0 in range(model.fludef_number):
        f0 = model.get_fludef(i0)
        if f0.component_number == 0:
            fluid_ids.append([i0, ])
            continue
        for i1 in range(f0.component_number):
            assert f0.get_component(i1).component_number == 0
            fluid_ids.append([i0, i1])

    cells = as_numpy(model).cells
    v = cells.fluid_mass if export_mass else cells.fluid_vol

    vs = []
    for fluid_id in fluid_ids:
        f = as_numpy(model).fluids(*fluid_id)
        s = (f.mass if export_mass else f.vol) / v
        vs.append(s)

    # 返回温度(未必有定义)
    ca_t = model.get_cell_key('temperature')
    if ca_t is not None:
        t = cells.get(ca_t)
    else:
        t = np.zeros(shape=v.shape)

    # 即将保存的数据
    d = join_cols(
        cells.x, cells.y, cells.z, cells.pre, t, v, *vs,
        *([] if ca_keys is None else
          [cells.get(key) for key in ca_keys]),
        *([] if fa_keys is None else
          [as_numpy(model).fluids(*idx).get(key) for idx, key in
           fa_keys]),
    )

    # 保存数据
    np.savetxt(path, d, fmt=fmt)


def _prepare_model(model=None, folder=None, fname=None):
    if model is None:
        if fname is not None:
            assert os.path.isfile(fname), f'The file not exist: {fname}'
            model = Seepage(path=fname)
            if folder is None:
                folder = os.path.splitext(fname)[0]
    else:
        if fname is not None:  # 此时，尝试保存到此文件
            model.save(make_parent(fname))  # 保存
            if folder is None:
                folder = os.path.splitext(fname)[0]

    # 打印标签
    if folder is not None:
        print_tag(folder=folder)

    return model, folder


def solve(
        model=None, folder=None, fname=None, gui_mode=None,
        close_after_done=None,
        extra_plot=None,
        show_state=True, gui_iter=None, state_hint=None,
        save_dt=None,
        export_mass=True, export_fa_keys=None,
        time_unit='y',
        slots=None,
        opt_iter=None,  # 用于在iterate的时候的额外的关键词参数.
        hide_console_when_done=False,
        **opt_sol
):
    """
    求解模型，并尝试将结果保存到folder.
    """
    model, folder = _prepare_model(model=model, folder=folder, fname=fname)
    if not isinstance(model, Seepage):
        return

    # step 1. 读取求解选项
    text = model.get_text(key='solve')
    if len(text) > 0:
        opt1 = eval(text)
    else:
        opt1 = {}
    opt_sol = merge_opts(opt1, opt_sol)

    # 创建monitor(同时，还保留了之前的配置信息)
    monitors = opt_sol.get('monitor')
    if isinstance(monitors, dict):
        monitors = [monitors]
    elif monitors is None:
        monitors = []

    for item in monitors:
        if isinstance(item, dict):
            item['monitor'] = SeepageCellMonitor(
                get_t=lambda: get_time(model),
                cell=[model.get_cell(i) for i in item.get('cell_ids')])

    if save_dt is None:
        save_dt_min = opt_sol.get(
            'save_dt_min',
            0.01 * SaveManager.get_unit_length(
                time_unit=time_unit))
        save_dt_max = opt_sol.get(
            'save_dt_max',
            5 * SaveManager.get_unit_length(
                time_unit=time_unit))

        def save_dt(time):
            return clamp(time * 0.05, save_dt_min, save_dt_max)

    # 执行数据的保存
    save_model = SaveManager(
        join_paths(folder, 'models'), save=model.save,
        ext='.seepage',
        time_unit=time_unit,
        unit_length='auto',
        dtime=save_dt,
        get_time=lambda: get_time(model),
    )

    # 打印cell
    save_cells = SaveManager(
        join_paths(folder, 'cells'),
        save=lambda name: print_cells(
            name, model=model, export_mass=export_mass, fa_keys=export_fa_keys),
        ext='.txt',
        time_unit=time_unit,
        unit_length='auto',
        dtime=save_dt,
        get_time=lambda: get_time(model),
    )

    # 保存所有
    def save(*args, **kw):
        save_model(*args, **kw)
        save_cells(*args, **kw)

    # 用来绘图的设置(show_cells)
    data = opt_sol.get('show_cells')
    if isinstance(data, dict):
        def do_show():
            show_cells(model, folder=join_paths(folder, 'figures'), **data)
    else:
        do_show = None

    def plot():
        """
        所有需要绘图的操作
        """
        if do_show is not None:
            do_show()

        try:
            for index in range(len(monitors)):
                item1 = monitors[index]
                assert isinstance(item1, dict)
                monitor = item1.get('monitor')
                assert isinstance(monitor, SeepageCellMonitor)
                plot_rate = item1.get('plot_rate')
                if plot_rate is not None:
                    for idx in plot_rate:
                        monitor.plot_rate(
                            index=idx,
                            caption=f'Rate_{index}.{idx}')  # 显示生产曲线
        except Exception as e:
            print(f'Error when plot the monitor. Error = {e}')

        if extra_plot is not None:  # 一些额外的，非标准的绘图操作
            if callable(extra_plot):
                try:
                    extra_plot()
                except Exception as err:
                    print(f'Error when run the extra plot. Function = {extra_plot.__name__}, Error = {err}')
            elif isinstance(extra_plot, Iterable):
                for extra_plot_i in extra_plot:
                    if callable(extra_plot_i):
                        try:
                            extra_plot_i()
                        except Exception as err:
                            print(f'Error when run the extra plot. Function = {extra_plot_i.__name__}, Error = {err}')

    def save_monitors():
        if folder is not None:
            for index in range(len(monitors)):
                item2 = monitors[index]
                assert isinstance(item2, dict)
                monitor = item2.get('monitor')
                assert isinstance(monitor, SeepageCellMonitor)
                monitor.save(join_paths(folder, f'monitor_{index}.txt'))

    # 执行最终的迭代
    if gui_iter is None:
        gui_iter = GuiIterator(iterate, plot=plot)
    else:  # 使用已有的配置(这样，方便多个求解过程，使用全局的iter)
        assert isinstance(gui_iter, GuiIterator)
        gui_iter.iterate = iterate
        gui_iter.plot = plot

    # 求解到的最大的时间
    time_max = opt_sol.get('time_max')
    if time_max is None:
        time_forward = opt_sol.get('time_forward')
        if time_forward is not None:
            time_max = get_time(model) + time_forward
    if time_max is None:  # 给定默认值
        time_max = 1.0e100

    # 求解到的最大的step
    step_max = opt_sol.get('step_max')
    if step_max is None:
        step_forward = opt_sol.get('step_forward')  # 向前迭代的步数
        if step_forward is not None:
            step_max = get_step(model) + step_forward
    if step_max is None:  # 给定默认值
        step_max = 999999999999

    # 状态提示
    if state_hint is None:
        state_hint = ''
    else:
        state_hint = state_hint + ': '

    def do_show_state():
        if show_state:
            print(
                f'{state_hint}step={get_step(model)}, dt={get_dt(model, as_str=True)}, '
                f'time={get_time(model, as_str=True)}')

    # 准备iterate的参数
    if opt_iter is None:  # 用于迭代的额外的参数
        opt_iter = {}
    if slots is not None:  # 优先级高于opt_iter
        opt_iter['slots'] = slots

    def main_loop():  # 主循环
        if folder is not None:  # 显示求解的目录
            if gui.exists():
                gui.title(f'Solve seepage: {folder}')

        while get_time(model) < time_max and get_step(model) < step_max:
            gui_iter(model, **opt_iter)
            save()

            for item3 in monitors:  # 更新所有的监控点
                monitor = item3.get('monitor')
                monitor.update(dt=3600.0)

            if get_step(model) % 20 == 0:
                do_show_state()
                save_monitors()

        # 显示并保存最终的状态
        do_show_state()
        save_monitors()
        if hide_console_when_done:  # 求解完成后，隐藏控制台
            gui.hide_console()
        plot()
        save(check_dt=False)  # 保存最终状态

    if close_after_done is not None and gui_mode is None:
        # 如果指定了close_after_done，那么一定是要使用界面
        gui_mode = True

    if gui_mode is None:  # 默认不使用界面
        gui_mode = False

    if close_after_done is None:  # 默认计算技术要关闭界面
        close_after_done = True

    gui.execute(func=main_loop, close_after_done=close_after_done,
                disable_gui=not gui_mode)


def get_inited(
        fludefs=None, reactions=None, gravity=None, path=None,
        time=None, dt=None, dv_relative=None,
        dt_max=None, dt_min=None,
        keys=None, tags=None, model_attrs=None):
    """
    创建一个模型，初始化必要的属性
    Args:
        fludefs: 流体定义列表，默认值为 None
        reactions: 化学反应定义列表，默认值为 None
        gravity: 重力向量，默认值为 None
        path: 模型路径，默认值为 None
        time: 初始时间，默认值为 None
        dt: 初始时间步长，默认值为 None
        dv_relative: 相对体积变化率，默认值为 None
        dt_max: 最大时间步长，默认值为 None
        dt_min: 最小时间步长，默认值为 None
        keys: 模型键值对，默认值为 None
        tags: 模型标签列表，默认值为 None
        model_attrs: 模型额外属性列表，默认值为 None

    Returns:
        Seepage 模型对象
    """
    model = Seepage(path=path)

    if keys is not None:
        # 预定义一些keys;
        # 主要目的是为了保证两个Seepage的keys的一致，
        # 在两个Seepage需要交互的时候，很重要.
        model.set_keys(**keys)

    if tags is not None:
        # 预定义的tags; since 2024-5-8
        model.add_tag(*tags)

    if model_attrs is not None:
        # 添加额外的模型属性  since 2024-5-8
        for key, value in model_attrs:
            set_attr(model, key=key, value=value)

    # 添加流体的定义和反应的定义 (since 2023-4-5)
    model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
    if fludefs is not None:
        for flu in fludefs:
            model.add_fludef(Seepage.FluDef.create(flu))

    model.clear_reactions()  # 清空已经存在的定义.
    if reactions is not None:
        for r in reactions:
            add_reaction(model, r)

    if gravity is not None:
        assert len(gravity) == 3
        model.gravity = gravity
        if point_distance(gravity, [0, 0, -10]) > 1.0:
            print(f'Warning: In general, gravity should be [0,0, -10], '
                  f'but here it is {gravity}, '
                  f'please make sure this is the setting you need')

    if time is not None:
        set_time(model, time)

    if dt is not None:
        set_dt(model, dt)

    if dt_min is not None:
        set_dt_min(model, dt_min)

    if dt_max is not None:
        set_dt_max(model, dt_max)

    if dv_relative is not None:
        set_dv_relative(model, dv_relative)

    return model


def add_injector(model: Seepage, data):
    """
    向模型中添加注入器
    Args:
        model: 渗流模型
        data: 注入器的定义字典

    Returns:
        None
    """
    if data is None:
        return
    elif isinstance(data, dict):
        inj = model.add_injector(**data)
        flu = data.get('flu')
        if flu == 'insitu' and model.cell_number > 0 and len(inj.fid) > 0:
            cell_id = inj.cell_id
            if cell_id >= model.cell_number and point_distance(
                    inj.pos, [0, 0, 0]) < 1e10:
                cell = model.get_nearest_cell(pos=inj.pos)
                if point_distance(cell.pos, inj.pos) < inj.radi:
                    cell_id = cell.index
            if cell_id < model.cell_number:
                # 特别注意的是，这里找到的这个cell，和injector内部工作的时候的cell，可能并不完全相同.
                cell = model.get_cell(cell_id)
                temp = cell.get_fluid(*inj.fid).get_copy()
                if temp is not None:
                    if temp.mass < 1.0e-10:
                        temp.mass = 1.0  # 将质量设置为宏观的量，确保属性可以被使用(since 2025-12-9)
                    inj.flu.clone(temp)
    else:
        for item in data:
            add_injector(model, data=item)


def create(
        mesh: Optional[SeepageMesh] = None,
        *,
        disable_update_den: bool = False,
        disable_update_vis: bool = False,
        disable_ther: bool = False,
        disable_heat_exchange: bool = False,
        fludefs=None,
        has_solid: bool = False,
        reactions=None,
        gravity=None,
        dt_max=None, dt_min=None, dt_ini=None, dv_relative=None,
        gr=None, bk_fv=None, bk_g=None, caps=None,
        keys: dict = None, tags: list[str] = None, kr=None, default_kr=None,
        model_attrs: Optional[dict[str, float]] = None,
        prods=None,
        warnings_ignored=None, injectors=None, texts=None,
        **kwargs) -> Seepage:
    """
    创建一个渗流模型。
    Args:
        mesh: SeepageMesh网格对象，默认值为 None
        disable_update_den: 是否禁用密度更新，默认值为 False
        disable_update_vis: 是否禁用粘度更新，默认值为 False
        disable_ther: 是否禁用热更新，默认值为 False
        disable_heat_exchange: 是否禁用热交换，默认值为 False
        fludefs: 流体定义列表，默认值为 None
        has_solid: 是否包含固体(将最后一种流体作为固体)，默认值为 False
        reactions: 化学反应定义列表，默认值为 None
        gravity: 重力向量，默认值为 None
        dt_max: 最大时间步长，默认值为 None
        dt_min: 最小时间步长，默认值为 None
        dt_ini: 初始时间步长，默认值为 None
        dv_relative: 在一个dt内，流过的最大体积和网格体积的比值，用以控制dt的大小，默认值为 None
        gr: 绝对渗透率随着孔隙度的变化曲线，默认值为 None
        bk_fv: 是否备份初始的流体体积，默认值为 None
        bk_g: 是否备份初始的导流能力，默认值为 None
        caps: 毛管压力的定义，默认值为 None
        keys: 模型键值对(预先定义好，不需要后续在动态添加了)，默认值为 None
        tags: 标签列表，默认值为 None
        kr: 渗透率变化率，默认值为 None
        default_kr: 默认渗透率变化率，默认值为 None
        prods: 控制流体的产出，默认值为 None
        warnings_ignored: 忽略的警告列表，默认值为 None
        injectors: 注入器定义列表，默认值为 None
        texts: 文本列表，默认值为 None
        model_attrs: 模型额外属性列表，默认值为 None

    Returns:
        Seepage 模型对象
    """
    model = Seepage()
    if warnings_ignored is None:  # 忽略掉的警告
        warnings_ignored = set()

    if keys is not None:
        # 预定义一些keys; 主要目的是为了保证两个Seepage的keys的一致，
        # 在两个Seepage需要交互的时候，很重要.
        model.set_keys(**keys)

    if tags is not None:
        # 预定义的tags; since 2024-5-8
        model.add_tag(*tags)

    if disable_update_den:
        model.add_tag('disable_update_den')

    if disable_update_vis:
        model.add_tag('disable_update_vis')

    if disable_ther:
        model.add_tag('disable_ther')

    if disable_heat_exchange:
        model.add_tag('disable_heat_exchange')

    if has_solid:
        model.add_tag('has_solid')

    if model_attrs is not None:
        # 添加额外的模型属性  since 2024-5-8
        for key, value in model_attrs:
            set_attr(model, key=key, value=value)

    # 添加流体的定义和反应的定义 (since 2023-4-5)
    model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
    if fludefs is not None:
        for flu in fludefs:
            model.add_fludef(Seepage.FluDef.create(flu))

    model.clear_reactions()  # 清空已经存在的定义.
    if reactions is not None:
        for r in reactions:
            add_reaction(model, r)

    # 设置重力
    if gravity is not None:
        assert len(gravity) == 3
        model.gravity = gravity
        if point_distance(gravity, [0, 0, -9.8]) > 1.0:
            if 'gravity' not in warnings_ignored:
                warnings.warn(f'In general, gravity should be [0, 0, -9.8], '
                              f'but here it is {gravity}, '
                              f'please make sure this is the setting you need',
                              stacklevel=2)

    if dt_max is not None:
        set_dt_max(model, dt_max)

    if dt_min is not None:
        set_dt_min(model, dt_min)

    if dt_ini is not None:
        set_dt(model, dt_ini)

    if dv_relative is not None:
        set_dv_relative(model, dv_relative)

    if gr is not None:
        igr = model.add_gr(gr, need_id=True)
    else:
        igr = None

    if kr is not None:  # since 2024-1-26
        # 设置相渗.
        for item in kr:
            if len(item) == 2:
                idx, val = item
                model.set_kr(index=idx, kr=val)
            else:
                assert len(item) == 3
                idx, x, y = item
                model.set_kr(index=idx, saturation=x, kr=y)

    if default_kr is not None:  # since 2024-5-8
        model.set_default_kr(default_kr)

    if mesh is not None:
        add_mesh(model, mesh)

    if bk_fv is None:  # 未给定数值，则自动设定
        bk_fv = model.gr_number > 0

    if bk_g is None:  # 未给定数值，则自动设定
        bk_g = model.gr_number > 0

    # 对模型的细节进行必要的配置
    set_model(
        model,
        mesh=mesh,  # Add mesh since 2025-6-23
        igr=igr, bk_fv=bk_fv, bk_g=bk_g, **kwargs)

    # 添加注入点 since 24-6-20
    add_injector(model, data=injectors)

    # 添加毛管效应.
    if caps is not None:
        for cap in caps:
            capillary.add_setting(model, **cap)

    if prods is not None:  # 添加用于生产的压力控制.
        if isinstance(prods, dict):
            prods = [prods, ]
        for item in prods:
            assert isinstance(item, dict)
            prod.add_setting(model, **item)

    # 添加文本属性
    if texts is not None:
        assert isinstance(texts, dict)
        for key, value in texts.items():
            model.set_text(key=key, text=value)

    return model


def add_mesh(model: Seepage, mesh: SeepageMesh):
    """
    根据给定的mesh，添加Cell和Face到Model. 并对Cell和Face设置基本的属性.
        对于Cell，仅仅设置位置和体积这两个属性.
        对于Face，仅仅设置面积和长度这两个属性.

    Args:
        model (Seepage): Seepage 模型对象
        mesh (SeepageMesh): 要添加的网格对象

    Returns:
        None

    该函数通过遍历网格中的单元格和面，将它们添加到模型中，并设置相应的属性。
    """
    if mesh is not None:
        ca_vol = cell_keys(model).vol
        fa_s = face_keys(model).area
        fa_l = face_keys(model).length

        cell_n0 = model.cell_number

        for c in mesh.cells:
            cell = model.add_cell()
            cell.pos = c.pos
            cell.set_attr(ca_vol, c.vol)

        for f in mesh.faces:
            face = model.add_face(
                model.get_cell(f.link[0] + cell_n0),
                model.get_cell(f.link[1] + cell_n0))
            face.set_attr(fa_s, f.area)
            face.set_attr(fa_l, f.length)


class _AttrId:
    """
    Mesh的属性ID
    """

    def __init__(self, begin=None, end=None):
        """
        初始化属性ID的范围
        """
        self.begin = begin
        self.end = end

    def get(self, o):
        """
        获得属性值
        """
        assert self.begin is not None
        if self.end is None:
            return o.get_attr(self.begin)
        else:
            return [o.get_attr(i) for i in range(self.begin, self.end)]

    def get_bool(self, o):
        value = self.get(o)
        if isinstance(value, list):
            return [1.0e-10 <= abs(item) <= 1.0e10 for item in value]
        else:
            return 1.0e-10 <= abs(value) <= 1.0e10

    def get_round(self, o):
        value = self.get(o)
        if isinstance(value, list):
            return [round(item) for item in value]
        else:
            return round(value)


def set_model(
        model: Seepage, *, porosity=0.1,
        pore_modulus=1000e6, denc=1.0e6, dist=0.1,
        temperature=280.0, p=None,
        s=None, perm=1e-14, heat_cond=1.0,
        sample_dist=None, pore_modulus_range=None,
        igr=None, bk_fv=True,
        bk_g=True, mesh=None, **ignores):
    """
    设置模型的网格，并顺便设置其初始的状态.

    Args:
        model (Seepage): Seepage 模型对象
        porosity: 孔隙度；
        pore_modulus: 空隙的刚度，单位Pa；正常取值在100MPa到1000MPa之间；
        denc: 土体的密度，单位kg/m^3；
                假设土体密度2000kg/m^3，比热1000，denc取值就是2.0e6；
        dist: 一个单元包含土体和流体两个部分，dist是土体和流体换热的距离。
                这个值越大，换热就越慢。如果希望土体和流体的温度非常接近，
                就可以把dist设置得比较小。一般，可以设置为网格大小的几分之一；
        temperature: 温度K
        p: 压力Pa
        s: 各个相的饱和度，tuple/list/dict；
        perm: 渗透率 m^2
        heat_cond: 热传导系数
        sample_dist: 样本距离，单位m；
        pore_modulus_range: 空隙的刚度范围，单位Pa；
        igr: 相对导流能力曲线的ID
        bk_fv: 是否备份初始的流体体积
        bk_g: 是否备份初始的face的导流系数
        mesh: 网格对象
        **ignores: 其他忽略的参数

    Notes:
        每一个参数，都可以是一个具体的数值，或者是一个和x，y，z坐标相关的一个分布
            (判断是否定义了obj.__call__这样的成员函数，有这个定义，则视为一个分布，
            否则是一个全场一定的值)

        在使用这个函数之前，请确保Cell需要已经正确设置了位置，并且具有网格体积vol这个自定义属性；
        对于Face，需要设置面积s和长度length这两个自定义属性。否则，此函数的执行会出现错误.

    """
    if len(ignores) > 0:
        print(f'Warning: The following arguments ignored in '
              f'zmlx.config.seepage.set_model: {list(ignores.keys())}')

    if mesh is not None:
        assert isinstance(mesh, SeepageMesh)
        assert mesh.cell_number == model.cell_number
        assert mesh.face_number == model.face_number

    def as_field(value):
        if isinstance(value, _AttrId):
            return _AttrId
        else:
            return Field(value)

    porosity = as_field(porosity)
    pore_modulus = as_field(pore_modulus)
    denc = as_field(denc)
    dist = as_field(dist)
    temperature = as_field(temperature)
    p = as_field(p)
    s = as_field(s)
    perm = as_field(perm)
    heat_cond = as_field(heat_cond)
    igr = as_field(igr)
    bk_fv = as_field(bk_fv)
    bk_g = as_field(bk_g)

    comp_names = list_comp(model)

    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        pos = cell.pos

        if mesh is not None:
            mesh_c = mesh.get_cell(cell.index)
        else:
            mesh_c = None

        if isinstance(porosity, _AttrId):
            assert mesh_c is not None
            porosity_val = porosity.get(mesh_c)
        else:
            porosity_val = porosity(*pos)

        if isinstance(pore_modulus, _AttrId):
            assert mesh_c is not None
            pore_modulus_val = pore_modulus.get(mesh_c)
        else:
            pore_modulus_val = pore_modulus(*pos)

        if isinstance(denc, _AttrId):
            assert mesh_c is not None
            denc_val = denc.get(mesh_c)
        else:
            denc_val = denc(*pos)

        if isinstance(temperature, _AttrId):
            assert mesh_c is not None
            temperature_val = temperature.get(mesh_c)
        else:
            temperature_val = temperature(*pos)

        if isinstance(p, _AttrId):
            assert mesh_c is not None
            p_val = p.get(mesh_c)
        else:
            p_val = p(*pos)

        if isinstance(dist, _AttrId):
            assert mesh_c is not None
            dist_val = dist.get(mesh_c)
        else:
            dist_val = dist(*pos)

        if isinstance(bk_fv, _AttrId):
            assert mesh_c is not None
            bk_fv_val = bk_fv.get_bool(mesh_c)
        else:
            bk_fv_val = bk_fv(*pos)

        if isinstance(heat_cond, _AttrId):
            assert mesh_c is not None
            heat_cond_val = heat_cond.get(mesh_c)
        else:
            heat_cond_val = heat_cond(*pos)
            # todo: 当热传导系数各向异性的时候，取平均值，这可能并不是最合适的.  @2024-8-11
            if isinstance(heat_cond_val, Tensor3):
                heat_cond_val = (heat_cond_val.xx +
                                 heat_cond_val.yy +
                                 heat_cond_val.zz) / 3.0

        if isinstance(s, _AttrId):
            assert mesh_c is not None
            s_val = s.get(mesh_c)
        else:
            s_val = s(*pos)
            if isinstance(s_val, dict):
                s_val = get_sat(comp_names, s_val)

        # 设置cell
        set_cell(
            cell,
            porosity=porosity_val,
            pore_modulus=pore_modulus_val,
            denc=denc_val,
            temperature=temperature_val,
            p=p_val,
            s=s_val,
            dist=dist_val,
            bk_fv=bk_fv_val,
            heat_cond=heat_cond_val,
            pore_modulus_range=pore_modulus_range,
        )

    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        p0 = face.get_cell(0).pos
        p1 = face.get_cell(1).pos

        if mesh is not None:
            mesh_f = mesh.get_face(face.index)
        else:
            mesh_f = None

        if isinstance(perm, _AttrId):
            assert mesh_f is not None
            perm_val = perm.get(mesh_f)
        else:
            perm_val = get_average_perm(p0, p1, perm, sample_dist)

        if isinstance(heat_cond, _AttrId):
            assert mesh_f is not None
            heat_cond_val = heat_cond.get(mesh_f)
        else:
            heat_cond_val = get_average_perm(p0, p1, heat_cond, sample_dist)

        if isinstance(igr, _AttrId):
            assert mesh_f is not None
            igr_val = igr.get_round(mesh_f)
        else:
            igr_val = igr(*face.pos)

        if isinstance(bk_g, _AttrId):
            assert mesh_f is not None
            bk_g_val = bk_g.get_bool(mesh_f)
        else:
            bk_g_val = bk_g(*face.pos)

        set_face(
            face, perm=perm_val,
            heat_cond=heat_cond_val,
            igr=igr_val, bk_g=bk_g_val
        )


def set_cell(
        cell: Seepage.Cell, pos=None, vol=None,
        porosity=0.1, pore_modulus=1000e6,
        denc=1.0e6, dist=0.1,
        temperature=280.0, p=1.0, s=None,
        pore_modulus_range=None, bk_fv=True, heat_cond=1.0):
    """
    设置Cell的初始状态.

    Args:
        cell: Seepage.Cell 类型的单元格对象
        pos: 单元格的位置，可选参数
        vol: 单元格的体积，可选参数
        porosity: 孔隙度，默认值为0.1
        pore_modulus: 孔隙模量，默认值为1000e6
        denc: 密度，默认值为1.0e6
        dist: 距离，默认值为0.1
        temperature: 温度，默认值为280.0
        p: 压力，默认值为1.0
        s: 饱和度，可选参数
        pore_modulus_range: 孔隙模量范围，可选参数
        bk_fv: 是否备份流体体积，默认值为True
        heat_cond: 热传导系数，默认值为1.0

    Returns:
        None

    该函数通过设置单元格的位置、体积、孔隙度、孔隙模量、密度、距离、温度、压力、饱和度等属性，
    来初始化单元格的状态。
    """
    assert isinstance(cell, Seepage.Cell)
    ca = cell_keys(cell.model)
    fa = flu_keys(cell.model)  # 流体的属性id

    if pos is not None:
        cell.pos = pos
    else:
        pos = cell.pos

    if vol is not None:
        cell.set_attr(ca.vol, vol)
    else:
        vol = cell.get_attr(ca.vol)
        assert vol is not None

    if isinstance(s, dict):  # 查表：应该尽量避免此语句执行，效率较低
        s = get_sat(list_comp(cell.model), s)

    cell.set_ini(
        ca_mc=ca.mc, ca_t=ca.temperature,
        fa_t=fa.temperature, fa_c=fa.specific_heat,
        pos=pos, vol=vol, porosity=porosity,
        pore_modulus=pore_modulus,
        denc=denc,
        temperature=temperature, p=p, s=s,
        pore_modulus_range=pore_modulus_range
    )

    if bk_fv:  # 备份流体体积
        cell.set_attr(ca.fv0, cell.fluid_vol)

    # 流体的固体之间的换热的系数
    cell.set_attr(ca.g_heat, vol * heat_cond / (dist ** 2))


def set_face(
        face: Seepage.Face, area=None, length=None,
        perm=None, heat_cond=None, igr=None, bk_g=True):
    """
    对一个Face进行配置

    Args:
        face: Seepage.Face 类型的面对象
        area: 面的面积，可选参数
        length: 面的长度，可选参数
        perm: 渗透率，可选参数
        heat_cond: 热传导系数，可选参数
        igr: 未知参数，可选参数
        bk_g: 是否备份渗透率，默认值为True
    Returns:
        None

    该函数通过设置面的面积、长度、渗透率、热传导系数等属性，来初始化面的状态。
    """
    assert isinstance(face, Seepage.Face)
    fa = face_keys(face.model)

    if area is not None:
        assert 0 <= area <= 1.0e30
        face.set_attr(fa.area, area)
    else:
        area = face.get_attr(fa.area)
        assert area is not None
        assert 0 <= area <= 1.0e30

    if length is not None:
        assert 0 < length <= 1.0e30
        face.set_attr(fa.length, length)
    else:
        length = face.get_attr(fa.length)
        assert length is not None
        assert 0 < length <= 1.0e30

    assert area >= 0
    assert length > 0

    if perm is not None:
        if callable(perm):
            # 当单独调用set_face的时候，可能会遇到这种情况
            p0 = face.get_cell(0).pos
            p1 = face.get_cell(1).pos
            perm = get_average_perm(p0, p1, perm, point_distance(p0, p1))

        if isinstance(perm, Tensor3):
            # 当单独调用set_face的时候，可能会遇到这种情况
            p0 = face.get_cell(0).pos
            p1 = face.get_cell(1).pos
            perm = perm.get_along([p1[i] - p0[i] for i in range(3)])
            perm = max(perm, 0.0)
        assert 0 <= perm <= 1.0e10
        face.set_attr(fa.perm, perm)
    else:
        perm = face.get_attr(fa.perm)
        assert perm is not None
        assert 0 <= perm <= 1.0e10

    g0 = area * perm / length
    face.cond = g0

    if bk_g:  # 备份初始时刻的cond，从而在后续可以根据gr去更新
        face.set_attr(fa.g0, g0)

    if heat_cond is not None:
        face.set_attr(fa.g_heat, area * heat_cond / length)

    if igr is not None:
        face.set_attr(fa.igr, igr)


def add_cell(model: Seepage, *args, **kwargs):
    """
    添加一个新的Cell，并返回Cell对象

    Args:
        model: Seepage 模型对象
        *args: 传递给 set_cell 函数的位置参数
        **kwargs: 传递给 set_cell 函数的关键字参数

    Returns:
        cell: 新添加的 Cell 对象

    该函数通过调用模型的 add_cell 方法创建一个新的单元格，
    然后使用 set_cell 函数设置该单元格的初始状态，并返回这个单元格对象。
    """
    cell = model.add_cell()
    set_cell(cell, *args, **kwargs)
    return cell


def add_face(model: Seepage, cell0, cell1, *args, **kwargs):
    """
    添加一个Face，并且返回

    Args:
        model: Seepage 模型对象
        cell0: 第一个单元格对象
        cell1: 第二个单元格对象
        *args: 传递给 set_face 函数的位置参数
        **kwargs: 传递给 set_face 函数的关键字参数

    Returns:
        face: 新添加的 Face 对象

    该函数通过调用模型的 add_face 方法创建一个新的面，
    然后使用 set_face 函数设置该面的初始状态，并返回这个面对象。
    """
    face = model.add_face(cell0, cell1)
    set_face(face, *args, **kwargs)
    return face


def append_cells_and_faces(model: Seepage, other: Seepage):
    """
    将另一个模型（other）中的所有的cell和face都追加到这个模型（model）后面;
        since 2024-5-18
    """
    # Add all the cells
    cell_n0 = model.cell_number
    for c in other.cells:
        model.add_cell(data=c)

    # Add all the faces
    for f in other.faces:
        assert isinstance(f, Seepage.Face)
        c0 = f.get_cell(0)
        c1 = f.get_cell(1)
        model.add_face(
            model.get_cell(cell_n0 + c0.index),
            model.get_cell(cell_n0 + c1.index), data=f)


def set_solve(model: Seepage, **kw):
    """
    设置用于求解的控制参数
    """
    text = model.get_text(key='solve')
    if len(text) > 0:
        options = eval(text)
    else:
        options = {}
    options.update(kw)
    model.set_text(key='solve', text=options)
