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
    has_inertia：是否考虑流体的惯性，如果考虑，则需要额外的属性来存储（定义：fa_s, fa_q, fa_k）
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
    vol：体积

Face的属性：
    area：横截面积
    length：长度（流体经过这个face需要流过的距离）
    g0：初始时刻的导流系数
    igr：导流系数的相对曲线的id（用来修正孔隙空间大小改变所带来的渗透率的改变）
    g_heat：用于传热计算的导流系数（注意，并非热传导系数。这个系数，已经考虑了face的横截面积和长度）
    perm: face位置的渗透率
"""
from collections.abc import Iterable

from zml import (get_average_perm, Tensor3, ConjugateGradientSolver,
                 make_parent, SeepageMesh)
from zmlx.alg.base import clamp
from zmlx.alg.base import join_cols
from zmlx.alg.fsys import join_paths, make_fname, print_tag
from zmlx.base.seepage import *
from zmlx.config import (capillary, prod, fluid_heating, timer,
                         sand, step_iteration, adjust_vis)
from zmlx.config.attr_keys import cell_keys, face_keys, flu_keys
from zmlx.config.slots import standard_slots
from zmlx.geometry.base import point_distance
from zmlx.plt.fig2 import tricontourf
from zmlx.react.alg import add_reaction
from zmlx.ui import gui
from zmlx.utility.fields import Field
from zmlx.utility.gui_iterator import GuiIterator
from zmlx.utility.save_manager import SaveManager
from zmlx.utility.seepage_cell_monitor import SeepageCellMonitor


def show_cells(
        model: Seepage, dim0, dim1, mask=None, show_p=True, show_t=True,
        show_s=True, folder=None, use_mass=False, **opts):
    """
    二维绘图显示

    参数:
    - model: Seepage 模型对象
    - dim0: 第一个维度索引（0, 1, 2 分别对应 x, y, z 维度）
    - dim1: 第二个维度索引（0, 1, 2 分别对应 x, y, z 维度）
    - mask: 可选的掩码，用于筛选特定的单元格
    - show_p: 是否显示压力（默认为 True）
    - show_t: 是否显示温度（默认为 True）
    - show_s: 是否显示饱和度（默认为 True）
    - folder: 图像保存的文件夹路径（可选）
    - use_mass: 是否使用质量饱和度（默认为 False）

    返回值:
    - 无

    该函数通过获取模型中单元格的位置和属性值，使用 tricontourf 函数绘制二维等值线图，
    显示模型中单元格的压力、温度和饱和度分布。如果提供了文件夹路径，则将图像保存到指定文件夹中。
    """
    if not gui.exists():
        return

    x = get_cell_pos(model=model, dim=dim0, mask=mask)
    y = get_cell_pos(model=model, dim=dim1, mask=mask)

    kw = dict(title=f'time = {get_time(model, as_str=True)}')
    kw.update(opts)

    year = get_time(model) / (365 * 24 * 3600)

    if show_p:  # 显示压力
        v = get_cell_pre(model, mask=mask)
        tricontourf(
            x, y, v, caption='pressure',
            fname=make_fname(
                year, join_paths(folder, 'pressure'),
                '.jpg', 'y'),
            **kw)

    if show_t:  # 显示温度
        v = get_cell_temp(model, mask=mask)
        tricontourf(
            x, y, v, caption='temperature',
            fname=make_fname(
                year, join_paths(folder, 'temperature'),
                '.jpg', 'y'),
            **kw)

    if not isinstance(show_s, list):
        if show_s:  # 此时，显示所有组分的饱和度
            show_s = list_comp(model, keep_structure=False)  # 所有的组分名称

    if isinstance(show_s, list):
        if use_mass:  # 此时，显示质量饱和度
            get = get_cell_fm
        else:
            get = get_cell_fv

        fv_all = get(model=model, mask=mask)
        for name in show_s:
            assert isinstance(name, str)
            idx = model.find_fludef(name=name)
            assert idx is not None
            fv = get(model=model, fid=idx, mask=mask)  # 流体体积
            v = fv / fv_all
            # 绘图
            tricontourf(
                x, y, v, caption=name,
                fname=make_fname(
                    year, join_paths(folder, name),
                    '.jpg', 'y'),
                **kw)


def get_recommended_dt(
        model: Seepage, previous_dt,
        dv_relative=0.1,
        using_flow=True, using_ther=True):
    """
    在调用了 iterate 函数之后，调用此函数，来获取更优的时间步长。

    参数:
    - model: Seepage 模型对象
    - previous_dt: 之前的时间步长
    - dv_relative: 相对体积变化率，默认为 0.1
    - using_flow: 是否使用流动模型，默认为 True
    - using_ther: 是否使用热模型，默认为 True

    返回值:
    - 更优的时间步长

    该函数首先断言 `using_flow` 或 `using_ther` 至少有一个为真。
    然后，根据是否使用流动模型和热模型，分别计算推荐的时间步长 `dt1` 和 `dt2`。
    最后，返回 `dt1` 和 `dt2` 中的较小值。
    """
    assert using_flow or using_ther
    if using_flow:
        dt1 = model.get_recommended_dt(
            previous_dt=previous_dt,
            dv_relative=dv_relative)
    else:
        dt1 = 1.0e100

    if using_ther:
        ca_t = model.reg_cell_key('temperature')
        ca_mc = model.reg_cell_key('mc')
        dt2 = model.get_recommended_dt(
            previous_dt=previous_dt,
            dv_relative=dv_relative,
            ca_t=ca_t, ca_mc=ca_mc)
    else:
        dt2 = 1.0e100
    return min(dt1, dt2)


try:
    solid_buffer = Seepage.CellData()
except Exception as err:
    print(err)
    solid_buffer = None


def iterate(
        model: Seepage, dt=None, solver=None, fa_s=None,
        fa_q=None, fa_k=None,
        cond_updaters=None, diffusions=None,
        react_bufs=None,
        vis_max=None, vis_min=None, slots=None):
    """
    在时间上向前迭代。其中
        dt:     时间步长,若为None，则使用自动步长
        solver: 线性求解器，若为None,则使用内部定义的共轭梯度求解器.
        fa_s:   Face自定义属性的ID，代表Face的横截面积（用于计算Face内流体的受力）;
        fa_q：   Face自定义属性的ID，代表Face内流体在通量(也将在iterate中更新)
        fa_k:   Face内流体的惯性系数的属性ID
            (若fa_k属性不为None，则所有Face的该属性需要提前给定).
        react_bufs:  反应的缓冲区，用来记录各个cell发生的反应的质量，
            其中的每一个buf都应该是一个pointer，且长度等于cell的数量;
    """
    if gui.exists():  # 添加断点，从而使得在这里可以暂停和终止
        gui.break_point()

    if dt is not None:
        set_dt(model, dt)

    dt = get_dt(model)
    assert dt is not None, 'You must set dt before iterate'

    # 使得slots至少包含standard_slots
    temp = standard_slots.copy()
    if slots is not None:
        temp.update(slots)
    slots = temp

    # 执行定时器函数.
    timer.iterate(
        model, t0=get_time(model), t1=get_time(model) + dt,
        slots=slots)

    # 执行step迭代
    step_iteration.iterate(
        model=model,
        current_step=get_step(model),
        slots=slots)

    if model.not_has_tag('disable_update_den') and model.fludef_number > 0:
        fa_t = model.reg_flu_key('temperature')
        model.update_den(relax_factor=0.3, fa_t=fa_t)

    if model.not_has_tag('disable_update_vis') and model.fludef_number > 0:
        # 更新流体的粘性系数(注意，当有固体存在的时候，务必将粘性系数的最大值设置为1.0e30)
        if vis_min is None:
            # 允许的最小的粘性系数
            vis_min = 1.0e-7
        if vis_max is None:
            # !!
            # 自2024-5-23开始，将vis_max的默认值从1.0修改为1.0e30，即默认
            #                 不再对粘性系数的最大值进行限制.
            #                 !!
            vis_max = 1.0e30

        assert 1.0e-10 <= vis_min <= vis_max <= 1.0e40
        ca_p = model.reg_cell_key('pre')
        fa_t = model.reg_flu_key('temperature')
        model.update_vis(
            ca_p=ca_p,  # 压力属性
            fa_t=fa_t,  # 温度属性
            relax_factor=1.0, min=vis_min, max=vis_max)

    if model.injector_number > 0:
        # 实施流体的注入操作.
        model.apply_injectors(dt=dt, time=get_time(model))

    # 尝试修改边界的压力，从而使得流体生产 (使用模型内部定义的time)
    #   since 2024-6-12
    prod.iterate(model)

    # 对流体进行加热
    fluid_heating.iterate(model)

    has_solid = model.has_tag('has_solid')

    if has_solid:
        # 此时，认为最后一种流体其实是固体，并进行备份处理
        model.pop_fluids(solid_buffer)

    if model.gr_number > 0:
        # 此时，各个Face的导流系数是可变的
        #       (并且，这里由于已经弹出了固体，因此计算体积使用的是流体的数值).
        # 注意：
        #     在建模的时候，务必要设置Cell的v0属性，Face的g0属性和igr属性，
        #     并且，在model中，应该有相应的gr和它对应。
        ca_v0 = model.get_cell_key('fv0')
        fa_g0 = model.get_face_key('g0')
        fa_igr = model.get_face_key('igr')
        if ca_v0 is not None and fa_g0 is not None and fa_igr is not None:
            model.update_cond(
                ca_v0=ca_v0, fa_g0=fa_g0,
                fa_igr=fa_igr,
                relax_factor=0.3)

    if cond_updaters is not None:  # 施加cond的更新操作
        for update in cond_updaters:
            assert callable(
                update), f'The update in cond_updaters must be callable. However, it is: {update}'
            update(model)

    # 当未禁止更新flow且流体的数量非空
    update_flow = model.not_has_tag('disable_flow') and model.fludef_number > 0

    if update_flow:
        ca_p = model.reg_cell_key('pre')
        adjust_vis.adjust(model=model)  # 备份粘性，并且尝试调整
        if model.has_tag('has_inertia'):
            r1 = model.iterate(
                dt=dt, solver=solver, fa_s=fa_s,
                fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)
        else:
            r1 = model.iterate(
                dt=dt, solver=solver, ca_p=ca_p)
        adjust_vis.restore(model=model)  # 恢复之前备份的粘性
    else:
        r1 = None

    # 执行所有的扩散操作，这一步需要在没有固体存在的条件下进行
    if diffusions is not None:
        for update in diffusions:
            update(model, dt)

    # 执行毛管力相关的操作
    capillary.iterate(model)

    if has_solid:
        # 恢复备份的固体物质
        model.push_fluids(solid_buffer)

    # 更新砂子的体积（优先使用自定义的update_sand）
    update_sand = slots.get('update_sand')
    if update_sand is None:
        update_sand = sand.iterate  # 优先使用自定义的update_sand
    update_sand(model=model)

    # 是否禁用热力学过程
    update_ther = model.not_has_tag('disable_ther')

    r2 = None
    if update_ther:
        ca_t = model.get_cell_key('temperature')
        ca_mc = model.get_cell_key('mc')
        fa_g = model.get_face_key('g_heat')
        if ca_t is not None and ca_mc is not None and fa_g is not None:
            r2 = model.iterate_thermal(
                dt=dt, solver=solver, ca_t=ca_t,
                ca_mc=ca_mc, fa_g=fa_g)

    # 不存在禁止标识且存在流体
    exchange_heat = model.not_has_tag('disable_heat_exchange'
                                      ) and model.fludef_number > 0

    if exchange_heat:
        ca_g = model.get_cell_key('g_heat')
        ca_t = model.get_cell_key('temperature')
        ca_mc = model.get_cell_key('mc')
        fa_t = model.get_flu_key('temperature')
        fa_c = model.get_flu_key('specific_heat')
        if ca_g is not None and ca_t is not None and ca_mc is not None and \
                fa_t is not None and fa_c is not None:
            model.exchange_heat(
                dt=dt, ca_g=ca_g, ca_t=ca_t, ca_mc=ca_mc,
                fa_t=fa_t, fa_c=fa_c)
        else:
            warnings.warn('model.exchange_heat failed in seepage.iterate')

    # 反应
    for idx in range(model.reaction_number):
        reaction = model.get_reaction(idx)
        assert isinstance(reaction, Seepage.Reaction)
        buf = None
        if react_bufs is not None:
            if idx < len(react_bufs):
                # 使用这个buf
                #   (必须确保这个buf是一个double类型的指针，并且长度等于cell_number)
                buf = react_bufs[idx]
        reaction.react(model, dt, buf=buf)

    set_time(model, get_time(model) + dt)
    set_step(model, get_step(model) + 1)

    if not model.has_tag('disable_update_dt'):
        # 只要不禁用dt更新，就尝试更新dt
        if update_flow or update_ther:
            # 只有当计算了流动或者传热过程，才可以使用自动的时间步长
            dt = get_recommended_dt(
                model, dt, get_dv_relative(model),
                using_flow=update_flow,
                using_ther=update_ther
            )
        dt = max(get_dt_min(model), min(get_dt_max(model), dt))
        set_dt(model, dt)  # 修改dt为下一步建议使用的值

    return r1, r2


def get_inited(
        fludefs=None, reactions=None, gravity=None, path=None,
        time=None, dt=None, dv_relative=None,
        dt_max=None, dt_min=None,
        keys=None, tags=None, model_attrs=None):
    """
    创建一个模型，初始化必要的属性.
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
    向模型中添加注入器.
    Args:
        model: 渗流模型
        data: 注入器的定义

    Returns:
        None
    """
    if data is None:
        return
    elif isinstance(data, dict):
        injector = model.add_injector(**data)
        flu = data.get('flu')
        if flu == 'insitu' and model.cell_number > 0 and len(
                injector.fid) > 0:  # 找到要注入的那个cell
            cell_id = injector.cell_id
            if cell_id >= model.cell_number and point_distance(
                    injector.pos, [0, 0, 0]) < 1e10:
                cell = model.get_nearest_cell(pos=injector.pos)
                if point_distance(cell.pos, injector.pos) < injector.radi:
                    cell_id = cell.index
            if cell_id < model.cell_number:
                # 特别注意的是，这里找到的这个cell，和injector内部工作的时候的cell，可能并不完全相同.
                cell = model.get_cell(cell_id)
                temp = cell.get_fluid(*injector.fid)
                if temp is not None:
                    injector.flu.clone(temp)
    else:
        for item in data:
            add_injector(model, data=item)


def create(
        mesh=None,
        disable_update_den=False, disable_update_vis=False,
        disable_ther=False, disable_heat_exchange=False,
        fludefs=None, has_solid=False, reactions=None,
        gravity=None,
        dt_max=None, dt_min=None, dt_ini=None, dv_relative=None,
        gr=None, bk_fv=None, bk_g=None, caps=None,
        keys=None, tags=None, kr=None, default_kr=None,
        model_attrs=None, prods=None,
        warnings_ignored=None, injectors=None, texts=None,
        **kwargs):
    """
    利用给定的网格来创建一个模型.
        其中gr用来计算孔隙体积变化之后的渗透率的改变量.  gr的类型是一个Interp1.
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
            capillary.add(model, **cap)

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


def add_mesh(model: Seepage, mesh):
    """
    根据给定的mesh，添加Cell和Face. 并对Cell和Face设置基本的属性.
        对于Cell，仅仅设置位置和体积这两个属性.
        对于Face，仅仅设置面积和长度这两个属性.

    参数:
    - model: Seepage 模型对象
    - mesh: 要添加的网格对象

    返回值:
    - 无

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


class AttrId:
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
        model: Seepage, porosity=0.1,
        pore_modulus=1000e6, denc=1.0e6, dist=0.1,
        temperature=280.0, p=None,
        s=None, perm=1e-14, heat_cond=1.0,
        sample_dist=None, pore_modulus_range=None,
        igr=None, bk_fv=True,
        bk_g=True, mesh=None, **ignores):
    """
    设置模型的网格，并顺便设置其初始的状态.
    --
    注意各个参数的含义：
        porosity: 孔隙度；
        pore_modulus：空隙的刚度，单位Pa；正常取值在100MPa到1000MPa之间；
        denc：土体的密度和比热的乘积；
                假设土体密度2000kg/m^3，比热1000，denc取值就是2.0e6；
        dist：一个单元包含土体和流体两个部分，dist是土体和流体换热的距离。
                这个值越大，换热就越慢。如果希望土体和流体的温度非常接近，
                就可以把dist设置得比较小。一般，可以设置为网格大小的几分之一；
        temperature: 温度K
        p：压力Pa
        s：各个相的饱和度，tuple/list/dict；
        perm：渗透率 m^2
        heat_cond: 热传导系数
    -
    注意：
        每一个参数，都可以是一个具体的数值，或者是一个和x，y，z坐标相关的一个分布
            (判断是否定义了obj.__call__这样的成员函数，有这个定义，则视为一个分布，
            否则是一个全场一定的值)
    --
    注意:
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
        if isinstance(value, AttrId):
            return AttrId
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

        if isinstance(porosity, AttrId):
            assert mesh_c is not None
            porosity_val = porosity.get(mesh_c)
        else:
            porosity_val = porosity(*pos)

        if isinstance(pore_modulus, AttrId):
            assert mesh_c is not None
            pore_modulus_val = pore_modulus.get(mesh_c)
        else:
            pore_modulus_val = pore_modulus(*pos)

        if isinstance(denc, AttrId):
            assert mesh_c is not None
            denc_val = denc.get(mesh_c)
        else:
            denc_val = denc(*pos)

        if isinstance(temperature, AttrId):
            assert mesh_c is not None
            temperature_val = temperature.get(mesh_c)
        else:
            temperature_val = temperature(*pos)

        if isinstance(p, AttrId):
            assert mesh_c is not None
            p_val = p.get(mesh_c)
        else:
            p_val = p(*pos)

        if isinstance(dist, AttrId):
            assert mesh_c is not None
            dist_val = dist.get(mesh_c)
        else:
            dist_val = dist(*pos)

        if isinstance(bk_fv, AttrId):
            assert mesh_c is not None
            bk_fv_val = bk_fv.get_bool(mesh_c)
        else:
            bk_fv_val = bk_fv(*pos)

        if isinstance(heat_cond, AttrId):
            assert mesh_c is not None
            heat_cond_val = heat_cond.get(mesh_c)
        else:
            heat_cond_val = heat_cond(*pos)
            # todo: 当热传导系数各向异性的时候，取平均值，这可能并不是最合适的.  @2024-8-11
            if isinstance(heat_cond_val, Tensor3):
                heat_cond_val = (heat_cond_val.xx +
                                 heat_cond_val.yy +
                                 heat_cond_val.zz) / 3.0

        if isinstance(s, AttrId):
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

        if isinstance(perm, AttrId):
            assert mesh_f is not None
            perm_val = perm.get(mesh_f)
        else:
            perm_val = get_average_perm(p0, p1, perm, sample_dist)

        if isinstance(heat_cond, AttrId):
            assert mesh_f is not None
            heat_cond_val = heat_cond.get(mesh_f)
        else:
            heat_cond_val = get_average_perm(p0, p1, heat_cond, sample_dist)

        if isinstance(igr, AttrId):
            assert mesh_f is not None
            igr_val = igr.get_round(mesh_f)
        else:
            igr_val = igr(*face.pos)

        if isinstance(bk_g, AttrId):
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

    参数:
    - cell: Seepage.Cell 类型的单元格对象
    - pos: 单元格的位置，可选参数
    - vol: 单元格的体积，可选参数
    - porosity: 孔隙度，默认值为0.1
    - pore_modulus: 孔隙模量，默认值为1000e6
    - denc: 密度，默认值为1.0e6
    - dist: 距离，默认值为0.1
    - temperature: 温度，默认值为280.0
    - p: 压力，默认值为1.0
    - s: 饱和度，可选参数
    - pore_modulus_range: 孔隙模量范围，可选参数
    - bk_fv: 是否备份流体体积，默认值为True
    - heat_cond: 热传导系数，默认值为1.0

    返回值:
    - 无

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

    参数:
    - face: Seepage.Face 类型的面对象
    - area: 面的面积，可选参数
    - length: 面的长度，可选参数
    - perm: 渗透率，可选参数
    - heat_cond: 热传导系数，可选参数
    - igr: 未知参数，可选参数
    - bk_g: 是否备份渗透率，默认值为True

    返回值:
    - 无

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

    参数:
    - model: Seepage 模型对象
    - *args: 传递给 set_cell 函数的位置参数
    - **kwargs: 传递给 set_cell 函数的关键字参数

    返回值:
    - cell: 新添加的 Cell 对象

    该函数通过调用模型的 add_cell 方法创建一个新的单元格，
    然后使用 set_cell 函数设置该单元格的初始状态，并返回这个单元格对象。
    """
    cell = model.add_cell()
    set_cell(cell, *args, **kwargs)
    return cell


def add_face(model: Seepage, cell0, cell1, *args, **kwargs):
    """
    添加一个Face，并且返回

    参数:
    - model: Seepage 模型对象
    - cell0: 第一个单元格对象
    - cell1: 第二个单元格对象
    - *args: 传递给 set_face 函数的位置参数
    - **kwargs: 传递给 set_face 函数的关键字参数

    返回值:
    - face: 新添加的 Face 对象

    该函数通过调用模型的 add_face 方法创建一个新的面，
    然后使用 set_face 函数设置该面的初始状态，并返回这个面对象。
    """
    face = model.add_face(cell0, cell1)
    set_face(face, *args, **kwargs)
    return face


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


def solve(
        model=None, folder=None, fname=None, gui_mode=None,
        close_after_done=None,
        extra_plot=None,
        show_state=True, gui_iter=None, state_hint=None,
        save_dt=None,
        export_mass=True, export_fa_keys=None,
        time_unit='y',
        slots=None, solver=None,
        opt_iter=None,  # 用于在iterate的时候的额外的关键词参数.
        **opt_solve
):
    """
    求解模型，并尝试将结果保存到folder.
    """
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

    # step 1. 读取求解选项
    text = model.get_text(key='solve')
    if len(text) > 0:
        full_solve_options = eval(text)
    else:
        full_solve_options = {}

    # 更新
    full_solve_options.update(opt_solve)

    # 建立求解器
    if solver is None:  # 使用规定的精度
        solver = ConjugateGradientSolver(
            tolerance=full_solve_options.get('tolerance', 1.0e-25))

    # 创建monitor(同时，还保留了之前的配置信息)
    monitors = full_solve_options.get('monitor')
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
        save_dt_min = full_solve_options.get(
            'save_dt_min',
            0.01 * SaveManager.get_unit_length(
                time_unit=time_unit))
        save_dt_max = full_solve_options.get(
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
    data = full_solve_options.get('show_cells')
    if isinstance(data, dict):
        def do_show():
            show_cells(model, folder=join_paths(folder, 'figures'), **data)
    else:
        do_show = None

    def plot():
        if do_show is not None:
            do_show()
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
        if extra_plot is not None:  # 一些额外的，非标准的绘图操作
            if callable(extra_plot):
                try:
                    extra_plot()
                except:
                    pass
            elif isinstance(extra_plot, Iterable):
                for extra_plot_i in extra_plot:
                    if callable(extra_plot_i):
                        try:
                            extra_plot_i()
                        except:
                            pass

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
    time_max = full_solve_options.get('time_max')
    if time_max is None:
        time_forward = full_solve_options.get('time_forward')
        if time_forward is not None:
            time_max = get_time(model) + time_forward
    if time_max is None:  # 给定默认值
        time_max = 1.0e100

    # 求解到的最大的step
    step_max = full_solve_options.get('step_max')
    if step_max is None:
        step_forward = full_solve_options.get('step_forward')  # 向前迭代的步数
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
    if solver is not None:  # 优先级高于opt_iter
        opt_iter['solver'] = solver

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
