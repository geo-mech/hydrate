from zml import *


def set_dt(model, dt):
    """
    设置模型的时间步长
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dt')
    model.set_attr(key, dt)


def get_dt(model):
    """
    返回模型内存储的时间步长
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dt')
    value = model.get_attr(key)
    if value is None:
        return 1.0e-10
    else:
        return value


def get_time(model):
    """
    返回模型的时间
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('time')
    value = model.get_attr(key)
    if value is None:
        return 0
    else:
        return value


def set_time(model, value):
    """
    设置模型的时间
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('time')
    model.set_attr(key, value)


def update_time(model, dt=None):
    """
    更新模型的时间
    """
    if dt is None:
        dt = get_dt(model)
    set_time(model, get_time(model) + dt)


def get_step(model):
    """
    返回模型迭代的次数
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('step')
    value = model.get_attr(key)
    if value is None:
        return 0
    else:
        return int(value)


def set_step(model, step):
    """
    设置模型迭代的步数
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('step')
    model.set_attr(key, step)


def get_recommended_dt(model, previous_dt, dv_relative=0.1, using_flow=True, using_ther=True):
    """
    在调用了iterate函数之后，调用此函数，来获取更优的时间步长.
    """
    assert using_flow or using_ther
    if using_flow:
        dt1 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=dv_relative)
    else:
        dt1 = 1.0e100

    if using_ther:
        ca_t = model.reg_cell_key('temperature')
        ca_mc = model.reg_cell_key('mc')
        dt2 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=dv_relative,
                                       ca_t=ca_t, ca_mc=ca_mc)
    else:
        dt2 = 1.0e100
    return min(dt1, dt2)


def get_dv_relative(model):
    """
    每一个时间步dt内流体流过的网格数. 用于控制时间步长. 正常取值应该在0到1之间.
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dv_relative')
    value = model.get_attr(key)
    if value is None:
        return 0.1
    else:
        return value


def set_dv_relative(model, value):
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dv_relative')
    model.set_attr(key, value)


def get_dt_min(model):
    """
    允许的最小的时间步长
        注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dt_min')
    value = model.get_attr(key)
    if value is None:
        return 1.0e-15
    else:
        return value


def set_dt_min(model, value):
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dt_min')
    model.set_attr(key, value)


def get_dt_max(model):
    """
    允许的最大的时间步长
        注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
    """
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dt_max')
    value = model.get_attr(key)
    if value is None:
        return 1.0e10
    else:
        return value


def set_dt_max(model, value):
    assert isinstance(model, Seepage)
    key = model.reg_model_key('dt_max')
    model.set_attr(key, value)


solid_buffer = Seepage.CellData()


def iterate(model, dt=None, solver=None, fa_s=None, fa_q=None, fa_k=None, cond_updaters=None, diffusions=None):
    """
    在时间上向前迭代。其中
        dt:     时间步长,若为None，则使用自动步长
        solver: 线性求解器，若为None,则使用内部定义的共轭梯度求解器.
        fa_s:   Face自定义属性的ID，代表Face的横截面积（用于计算Face内流体的受力）;
        fa_q：   Face自定义属性的ID，代表Face内流体在通量(也将在iterate中更新)
        fa_k:   Face内流体的惯性系数的属性ID (若fa_k属性不为None，则所有Face的该属性需要提前给定).
    """
    assert isinstance(model, Seepage)
    if dt is not None:
        set_dt(model, dt)

    dt = get_dt(model)
    assert dt is not None, 'You must set dt before iterate'

    if model.not_has_tag('disable_update_den') and model.fludef_number > 0:
        fa_t = model.reg_flu_key('temperature')
        model.update_den(relax_factor=0.3, fa_t=fa_t)

    if model.not_has_tag('disable_update_vis') and model.fludef_number > 0:
        ca_p = model.reg_cell_key('pre')
        fa_t = model.reg_flu_key('temperature')
        model.update_vis(ca_p=ca_p, fa_t=fa_t,
                         relax_factor=1.0, min=1.0e-7, max=1.0)

    if model.injector_number > 0:
        model.apply_injectors(dt)

    has_solid = model.has_tag('has_solid')

    if has_solid:
        # 此时，认为最后一种流体其实是固体，并进行备份处理
        model.pop_fluids(solid_buffer)

    if model.gr_number > 0:
        # 此时，各个Face的导流系数是可变的.
        # 注意：
        #   在建模的时候，务必要设置Cell的v0属性，Face的g0属性和ikr属性，并且，在model中，应该有相应的kr和它对应。
        #   为了不和真正流体的kr混淆，这个Face的ikr，应该大于流体的数量。
        v0 = model.reg_cell_key('fv0')
        g0 = model.reg_face_key('g0')
        igr = model.reg_face_key('igr')
        model.update_cond(v0=v0, g0=g0, krf=igr, relax_factor=0.3)

    # 施加cond的更新操作
    if cond_updaters is not None:
        for update in cond_updaters:
            update(model)

    # 当未禁止更新flow且流体的数量非空
    update_flow = model.not_has_tag('disable_flow') and model.fludef_number > 0

    if update_flow:
        ca_p = model.reg_cell_key('pre')
        if model.has_tag('has_inertia'):
            r1 = model.iterate(dt=dt, solver=solver, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)
        else:
            r1 = model.iterate(dt=dt, solver=solver, ca_p=ca_p)
    else:
        r1 = None

    # 执行所有的扩散操作，这一步需要在没有固体存在的条件下进行
    if diffusions is not None:
        for update in diffusions:
            update(model, dt)

    if has_solid:
        # 恢复备份的固体物质
        model.push_fluids(solid_buffer)

    update_ther = model.not_has_tag('disable_ther')

    if update_ther:
        ca_t = model.reg_cell_key('temperature')
        ca_mc = model.reg_cell_key('mc')
        fa_g = model.reg_face_key('g_heat')
        r2 = model.iterate_thermal(dt=dt, solver=solver, ca_t=ca_t, ca_mc=ca_mc, fa_g=fa_g)
    else:
        r2 = None

    # 不存在禁止标识且存在流体
    exchange_heat = model.not_has_tag('disable_heat_exchange') and model.fludef_number > 0

    if exchange_heat:
        ca_g = model.reg_cell_key('g_heat')
        ca_t = model.reg_cell_key('temperature')
        ca_mc = model.reg_cell_key('mc')
        fa_t = model.reg_flu_key('temperature')
        fa_c = model.reg_flu_key('specific_heat')
        model.exchange_heat(dt=dt, ca_g=ca_g, ca_t=ca_t, ca_mc=ca_mc, fa_t=fa_t, fa_c=fa_c)

    # 优先使用模型中定义的反应
    for idx in range(model.reaction_number):
        reaction = model.get_reaction(idx)
        assert isinstance(reaction, Reaction)
        reaction.react(model, dt)

    set_time(model, get_time(model) + dt)
    set_step(model, get_step(model) + 1)

    if not model.has_tag('disable_update_dt'):
        # 只要不禁用dt更新，就尝试更新dt
        if update_flow or update_ther:
            # 只有当计算了流动或者传热过程，才可以使用自动的时间步长
            dt = get_recommended_dt(model, dt, get_dv_relative(model),
                                    using_flow=update_flow,
                                    using_ther=update_ther
                                    )
        dt = max(get_dt_min(model), min(get_dt_max(model), dt))
        set_dt(model, dt)  # 修改dt为下一步建议使用的值

    return r1, r2
