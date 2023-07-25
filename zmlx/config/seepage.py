from zml import *
from zmlx.config import capillary
from zmlx.config.attr_keys import *
from zmlx.alg.join_cols import join_cols
import numpy as np


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
        # 实施流体的注入操作.
        model.apply_injectors(dt)

    has_solid = model.has_tag('has_solid')

    if has_solid:
        # 此时，认为最后一种流体其实是固体，并进行备份处理
        model.pop_fluids(solid_buffer)

    if model.gr_number > 0:
        # 此时，各个Face的导流系数是可变的 (并且，这里由于已经弹出了固体，因此计算体积使用的是流体的数值).
        # 注意：
        #     在建模的时候，务必要设置Cell的v0属性，Face的g0属性和igr属性，并且，在model中，应该有相应的gr和它对应。
        ca_v0 = model.get_cell_key('fv0')
        fa_g0 = model.get_face_key('g0')
        fa_igr = model.get_face_key('igr')
        if ca_v0 is not None and fa_g0 is not None and fa_igr is not None:
            model.update_cond(ca_v0=ca_v0, fa_g0=fa_g0, fa_igr=fa_igr, relax_factor=0.3)

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

    # 执行毛管力相关的操作
    capillary.iterate(model, dt)

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


def create(mesh=None,
           disable_update_den=False, disable_update_vis=False, disable_ther=False, disable_heat_exchange=False,
           fludefs=None, has_solid=False, reactions=None,
           gravity=None,
           dt_max=None, dt_min=None, dt_ini=None, dv_relative=None,
           gr=None, bk_fv=None, bk_g=None, caps=None,
           **kwargs):
    """
    利用给定的网格来创建一个模型.
        其中gr用来计算孔隙体积变化之后的渗透率的改变量.  gr的类型是一个Interp1.
    """
    model = Seepage()

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

    # 添加流体的定义和反应的定义 (since 2023-4-5)
    model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
    if fludefs is not None:
        for flu in fludefs:
            model.add_fludef(Seepage.FluDef.create(flu))

    model.clear_reactions()  # 清空已经存在的定义.
    if reactions is not None:
        for r in reactions:
            model.add_reaction(r)

    # 设置重力
    if gravity is not None:
        assert len(gravity) == 3
        model.gravity = gravity

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

    if mesh is not None:
        add_mesh(model, mesh)

    if bk_fv is None:   # 未给定数值，则自动设定
        bk_fv = model.gr_number > 0

    if bk_g is None:   # 未给定数值，则自动设定
        bk_g = model.gr_number > 0

    set_model(model, igr=igr, bk_fv=bk_fv, bk_g=bk_g, **kwargs)

    # 添加毛管效应.
    if caps is not None:
        for cap in caps:
            capillary.add(model, **cap)

    return model


def add_mesh(model, mesh):
    """
    根据给定的mesh，添加Cell和Face. 并对Cell和Face设置基本的属性.
        对于Cell，仅仅设置位置和体积这两个属性.
        对于Face，仅仅设置面积和长度这两个属性.
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
            face = model.add_face(model.get_cell(f.link[0] + cell_n0), model.get_cell(f.link[1] + cell_n0))
            face.set_attr(fa_s, f.area)
            face.set_attr(fa_l, f.length)


def set_model(model, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, dist=0.1,
              temperature=280.0, p=None, s=None, perm=1e-14, heat_cond=1.0,
              sample_dist=None, pore_modulus_range=None, igr=None, bk_fv=True, bk_g=True):
    """
    设置模型的网格，并顺便设置其初始的状态.
    --
    注意各个参数的含义：
        porosity: 孔隙度；
        pore_modulus：空隙的刚度，单位Pa；正常取值在100MPa到1000MPa之间；
        denc：土体的密度和比热的乘积；假设土体密度2000kg/m^3，比热1000，denc取值就是2.0e6；
        dist：一个单元包含土体和流体两个部分，dist是土体和流体换热的距离。这个值越大，换热就越慢。如果希望土体和流体的温度非常接近，
            就可以把dist设置得比较小。一般，可以设置为网格大小的几分之一；
        temperature: 温度K
        p：压力Pa
        s：各个相的饱和度，tuple或者list；
        perm：渗透率 m^2
        heat_cond: 热传导系数
    -
    注意：
        每一个参数，都可以是一个具体的数值，或者是一个和x，y，z坐标相关的一个分布
        ( 判断是否定义了obj.__call__这样的成员函数，有这个定义，则视为一个分布，否则是一个全场一定的值)
    --
    注意:
        在使用这个函数之前，请确保Cell需要已经正确设置了位置，并且具有网格体积vol这个自定义属性；
        对于Face，需要设置面积s和长度length这两个自定义属性。否则，此函数的执行会出现错误.

    """
    porosity = Field(porosity)
    pore_modulus = Field(pore_modulus)
    denc = Field(denc)
    dist = Field(dist)
    temperature = Field(temperature)
    p = Field(p)
    s = Field(s)
    perm = Field(perm)
    heat_cond = Field(heat_cond)
    igr = Field(igr)
    bk_fv = Field(bk_fv)
    bk_g = Field(bk_g)

    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        pos = cell.pos
        set_cell(cell, porosity=porosity(*pos), pore_modulus=pore_modulus(*pos), denc=denc(*pos),
                 temperature=temperature(*pos), p=p(*pos), s=s(*pos),
                 pore_modulus_range=pore_modulus_range, dist=dist(*pos), bk_fv=bk_fv(*pos))

    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        p0 = face.get_cell(0).pos
        p1 = face.get_cell(1).pos
        set_face(face, perm=get_average_perm(p0, p1, perm, sample_dist),
                 heat_cond=get_average_perm(p0, p1, heat_cond, sample_dist), igr=igr(*face.pos), bk_g=bk_g(*face.pos))


def set_cell(cell, pos=None, vol=None, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, dist=0.1,
             temperature=280.0, p=1.0, s=None, pore_modulus_range=None, bk_fv=True):
    """
    设置Cell的初始状态.
    """
    assert isinstance(cell, Seepage.Cell)
    ca = cell_keys(cell.model)
    fa = flu_keys(cell.model)

    if pos is not None:
        cell.pos = pos
    else:
        pos = cell.pos

    if vol is not None:
        cell.set_attr(ca['vol'], vol)
    else:
        vol = cell.get_attr(ca['vol'])
        assert vol is not None

    cell.set_ini(ca_mc=ca['mc'], ca_t=ca['temperature'],
                 fa_t=fa['temperature'], fa_c=fa['specific_heat'],
                 pos=pos, vol=vol, porosity=porosity,
                 pore_modulus=pore_modulus,
                 denc=denc,
                 temperature=temperature, p=p, s=s,
                 pore_modulus_range=pore_modulus_range
                 )

    if bk_fv:   # 备份流体体积
        cell.set_attr(ca['fv0'], cell.fluid_vol)
    cell.set_attr(ca['g_heat'], vol / (dist ** 2))


def set_face(face, area=None, length=None, perm=None, heat_cond=None, igr=None, bk_g=True):
    """
    对一个Face进行配置
    """
    assert isinstance(face, Seepage.Face)
    fa = face_keys(face.model)

    if area is not None:
        assert 0 <= area <= 1.0e30
        face.set_attr(fa['area'], area)
    else:
        area = face.get_attr(fa['area'])
        assert area is not None
        assert 0 <= area <= 1.0e30

    if length is not None:
        assert 0 < length <= 1.0e30
        face.set_attr(fa['length'], length)
    else:
        length = face.get_attr(fa['length'])
        assert length is not None
        assert 0 < length <= 1.0e30

    assert area >= 0
    assert length > 0

    if perm is not None:
        assert 0 <= perm <= 1.0e10
        face.set_attr(fa['perm'], perm)
    else:
        perm = face.get_attr(fa['perm'])
        assert perm is not None
        assert 0 <= perm <= 1.0e10

    g0 = area * perm / length
    face.cond = g0

    if bk_g:
        face.set_attr(fa['g0'], g0)

    if heat_cond is not None:
        face.set_attr(fa['g_heat'], area * heat_cond / length)

    if igr is not None:
        face.set_attr(fa['igr'], igr)


def add_cell(model, *args, **kwargs):
    """
    添加一个新的Cell，并返回Cell对象
    """
    cell = model.add_cell()
    set_cell(cell, *args, **kwargs)
    return cell


def add_face(model, cell0, cell1, *args, **kwargs):
    """
    添加一个Face，并且返回
    """
    face = model.add_face(cell0, cell1)
    set_face(face, *args, **kwargs)
    return face


def print_cells(path, model, ca_keys=None, fa_keys=None, fmt='%.18e'):
    """
    输出cell的属性（前三列固定为x y z坐标）. 默认第4列为pre，第5列温度，第6列为流体总体积，后面依次为各流体组分的体积饱和度.
    最后是ca_keys所定义的额外的Cell属性.
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

    cells = model.numpy.cells
    v = cells.fluid_vol

    vs = []
    for fluid_id in fluid_ids:
        s = model.numpy.fluids(*fluid_id).vol / v
        vs.append(s)

    # 返回温度(未必有定义)
    ca_t = model.get_cell_key('temperature')
    if ca_t is not None:
        t = cells.get(ca_t)
    else:
        t = np.zeros(shape=v.shape)

    # 即将保存的数据
    d = join_cols(cells.x, cells.y, cells.z, cells.pre, t, v, *vs,
                  *([] if ca_keys is None else [cells.get(key) for key in ca_keys]),
                  *([] if fa_keys is None else [model.numpy.fluids(*idx).get(key) for idx, key in fa_keys]),
                  )

    # 保存数据
    np.savetxt(path, d, fmt=fmt)
