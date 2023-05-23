from zml import *
from zmlx.alg.clamp import clamp

solid_buffer = Seepage.CellData()


class FluAttrs:
    def __init__(self, model):
        self.t = model.reg_flu_key('t')
        self.c = model.reg_flu_key('c')


class CellAttrs:
    def __init__(self, model):
        self.mc = model.reg_cell_key('mc')
        self.t = model.reg_cell_key('t')
        self.p = model.reg_cell_key('p')
        self.fv0 = model.reg_cell_key('fv0')
        self.g_heat = model.reg_cell_key('g_heat')
        self.vol = model.reg_cell_key('vol')
        self.fa = FluAttrs(model)

    def set_fv0(self, cell, fv0):
        """
        设置cell在原始状态下，和原始的导流能力相对应的流体体积
        """
        cell.set_attr(self.fv0, fv0)

    def set_vol(self, cell, vol):
        """
        设置Cell的网格体积
        """
        cell.set_attr(self.vol, vol)

    def get_vol(self, cell):
        """
        Cell的网格体积
        """
        return cell.get_attr(self.vol)

    def set_g_heat(self, cell, g_heat):
        """
        设置固体和流体进行热交换的时候的系数g. 这里g的定义为
            heat[J] = g * dT * dt
        其中dT为固液的温度差，dt为时间步，利用这个g来计算传输的热量[单位焦耳]
        """
        cell.set_attr(self.g_heat, g_heat)

    def get_p(self, cell):
        """
        压力
        """
        return cell.get_attr(self.p)

    def set_ini(self, cell, pos=None, vol=None, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, temperature=280.0,
                p=1.0, s=None, pore_modulus_range=None, dist=0.1):
        """
        设置Cell的初始状态.
        """
        assert isinstance(cell, Seepage.Cell)
        if pos is not None:
            cell.pos = pos
        if vol is not None:
            self.set_vol(cell, vol)

        pos = cell.pos
        vol = self.get_vol(cell)
        assert vol is not None

        cell.set_ini(ca_mc=self.mc, ca_t=self.t, fa_t=self.fa.t, fa_c=self.fa.c,
                     pos=pos, vol=vol, porosity=porosity,
                     pore_modulus=pore_modulus, denc=denc,
                     temperature=temperature, p=p, s=s,
                     pore_modulus_range=pore_modulus_range)
        # 初始的流体体积
        self.set_fv0(cell, cell.fluid_vol)
        self.set_g_heat(cell, vol / (dist ** 2))


class FaceAttrs:
    def __init__(self, model):
        self.igr = model.reg_face_key('igr')
        self.g0 = model.reg_face_key('g0')
        self.g_heat = model.reg_face_key('g_heat')
        self.s = model.reg_face_key('s')
        self.q = model.reg_face_key('q')
        self.k = model.reg_face_key('k')
        self.length = model.reg_face_key('length')
        self.perm = model.reg_face_key('perm')

    def set_g0(self, face, g0):
        """
        设置Face的原始的导流能力. 将和Cell的fv0属性进行配合，从而来计算孔隙度的变化量，并进而更新Face的导流能力.
        """
        face.set_attr(self.g0, g0)

    def set_igr(self, face, igr):
        """
        设置Face对应的动态渗透率的调整曲线。和Cell的fv0属性，以及Face的g0属性一起使用.
        """
        if igr is not None:
            face.set_attr(self.igr, igr)

    def set_perm(self, face, perm):
        """
        设置Face位置的渗透率
        """
        face.set_attr(self.perm, perm)

    def get_perm(self, face):
        return face.get_attr(self.perm)

    def set_g_heat(self, face, g_heat):
        """
        设置face的导热系数.
        """
        face.set_attr(self.g_heat, g_heat)

    def set_s(self, face, s):
        """
        设置face的面积
        """
        face.set_attr(self.s, s)

    def get_s(self, face):
        """
        face的面积
        """
        return face.get_attr(self.s)

    def set_length(self, face, length):
        """
        设置face的长度。face两侧的Cell之间的距离，也等于流体流过的距离.
        """
        face.set_attr(self.length, length)

    def get_length(self, face):
        """
        face的长度
        """
        return face.get_attr(self.length)

    def set_ini(self, face, area=None, length=None, perm=None, heat_cond=None, igr=None):
        assert isinstance(face, Seepage.Face)

        if area is not None:
            self.set_s(face, area)
        else:
            area = self.get_s(face)
            assert area is not None

        if length is not None:
            self.set_length(face, length)
        else:
            length = self.get_length(face)
            assert length is not None

        assert area > 0 and length > 0

        if perm is not None:
            self.set_perm(face, perm)
        else:
            perm = self.get_perm(face)
            assert perm is not None

        g0 = area * perm / length
        face.cond = g0

        self.set_g0(face, g0)
        if heat_cond is not None:
            self.set_g_heat(face, area * heat_cond / length)

        if igr is not None:
            self.set_igr(face, igr)


def iterate(model, dt=None, solver=None, diffusions=None):
    """
    在时间上向前迭代。其中
        dt:     时间步长,若为None，则使用自动步长
        solver: 线性求解器，若为None,则使用内部定义的共轭梯度求解器.
    """
    assert isinstance(model, Seepage)

    # Cell的属性ID
    ca = CellAttrs(model)

    # Face的属性ID
    fa = FaceAttrs(model)

    # 流体的属性ID
    fk = FluAttrs(model)

    if dt is not None:
        set_dt(model, dt)

    dt = get_dt(model)
    assert dt is not None, 'You must set dt before iterate'

    if model.not_has_tag('disable_update_den'):
        model.update_den(relax_factor=0.3, fa_t=fk.t)

    if model.not_has_tag('disable_update_vis'):
        model.update_vis(ca_p=ca.p, fa_t=fk.t, relax_factor=1.0, min=1.0e-7, max=1.0)

    has_solid = model.has_tag('has_solid')

    if has_solid:
        # 此时，认为最后一种流体其实是固体，并进行备份处理
        model.pop_fluids(solid_buffer)

    if cond_variable(model):
        # 此时，各个Face的导流系数是可变的.
        # 注意：
        #   在建模的时候，务必要设置Cell的v0属性，Face的g0属性和ikr属性，并且，在model中，应该有相应的kr和它对应。
        #   为了不和真正流体的kr混淆，这个Face的ikr，应该大于流体的数量。
        model.update_cond(v0=ca.fv0, g0=fa.g0, krf=fa.igr, relax_factor=0.3)

    # 当未禁止更新flow且流体的数量非空
    update_flow = model.not_has_tag('disable_flow') and model.fludef_number > 0

    if update_flow:
        if model.has_tag('has_inertia'):
            r1 = model.iterate(dt=dt, solver=solver, fa_s=fa.s, fa_q=fa.q, fa_k=fa.k, ca_p=ca.p)
        else:
            r1 = model.iterate(dt=dt, solver=solver, ca_p=ca.p)
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
        r2 = model.iterate_thermal(dt=dt, solver=solver, ca_t=ca.t, ca_mc=ca.mc, fa_g=fa.g_heat)
    else:
        r2 = None

    # 不存在禁止标识且存在流体
    exchange_heat = model.not_has_tag('disable_heat_exchange') and model.fludef_number > 0

    if exchange_heat:
        model.exchange_heat(dt=dt, ca_g=ca.g_heat, ca_t=ca.t, ca_mc=ca.mc, fa_t=fk.t, fa_c=fk.c)

    for idx in range(model.reaction_number):
        model.get_reaction(idx).react(model, dt)

    add_time(model, dt)
    add_step(model)

    if model.not_has_tag('disable_update_dt'):
        # 只要不禁用dt更新，就尝试更新dt
        if update_flow or update_ther:
            dt = get_recommended_dt(model, dt, using_flow=update_flow, using_ther=update_ther)
        dt = clamp(dt, get_dt_min(model), get_dt_max(model))
        set_dt(model, dt)
    return r1, r2


def get_recommended_dt(model, previous_dt, using_flow=True, using_ther=True):
    """
    在调用了iterate函数之后，调用此函数，来获取更优的时间步长.
    """
    assert using_flow or using_ther
    if using_flow:
        dt1 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=get_dv_relative(model))
    else:
        dt1 = 1.0e100

    if using_ther:
        ca_mc = model.reg_cell_key('mc')
        ca_t = model.reg_cell_key('t')
        dt2 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=get_dv_relative(model),
                                       ca_t=ca_t, ca_mc=ca_mc)
    else:
        dt2 = 1.0e100
    return min(dt1, dt2)


def cond_variable(model):
    """
    设置一个标签，用于表示在iterate的时候，模型中各个Face的cond属性是否是可变的.
    """
    assert isinstance(model, Seepage)
    return model.gr_number > 0


def get_dt(model):
    """
    返回模型内存储的时间步长
    """
    value = model.get_attr(model.reg_model_key('dt'))
    if value is None:
        return 1.0e-10
    else:
        return value


def set_dt(model, dt):
    """
    设置模型的时间步长
    """
    model.set_attr(model.reg_model_key('dt'), dt)


def get_time(model):
    """
    返回模型的时间
    """
    value = model.get_attr(model.reg_model_key('time'))
    if value is None:
        return 0
    else:
        return value


def set_time(model, value):
    """
    设置模型的时间
    """
    model.set_attr(model.reg_model_key('time'), value)


def add_time(model, value):
    set_time(model, get_time(model) + value)


def get_step(model):
    """
    返回模型迭代的次数
    """
    value = model.get_attr(model.reg_model_key('step'))
    if value is None:
        return 0
    else:
        return int(value)


def set_step(model, step):
    """
    设置模型迭代的步数
    """
    model.set_attr(model.reg_model_key('step'), step)


def add_step(model):
    set_step(model, get_step(model) + 1)


def get_dv_relative(model):
    """
    每一个时间步dt内流体流过的网格数. 用于控制时间步长. 正常取值应该在0到1之间.
    """
    value = model.get_attr(model.reg_model_key('dv_max'))
    if value is None:
        return 0.1
    else:
        return value


def set_dv_relative(model, value):
    model.set_attr(model.reg_model_key('dv_max'), value)


def get_dt_min(model):
    """
    允许的最小的时间步长
        注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
    """
    value = model.get_attr(model.reg_model_key('dt_min'))
    if value is None:
        return 1.0e-15
    else:
        return value


def set_dt_min(model, value):
    model.set_attr(model.reg_model_key('dt_min'), value)


def get_dt_max(model):
    """
    允许的最大的时间步长
        注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
    """
    value = model.get_attr(model.reg_model_key('dt_max'))
    if value is None:
        return 1.0e10
    else:
        return value


def set_dt_max(model, value):
    model.set_attr(model.reg_model_key('dt_max'), value)


def create(mesh=None, disable_update_den=False, disable_update_vis=False, disable_ther=False,
           disable_heat_exchange=False,
           has_solid=False, fluids=None, reactions=None, gravity=None, dt_max=None, dt_min=None, dt_ini=None,
           dv_relative=None, model=None, gr=None,
           **kwargs):
    """
    创建一个模型，并进行初步的配置.
    """
    if model is None:
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
    if fluids is not None:
        model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
        for flu in fluids:
            model.add_fludef(Seepage.FluDef.create(flu))

    if reactions is not None:
        model.clear_reactions()  # 清空已经存在的定义.
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

    add_mesh(model, mesh)
    set_init(model, igr=igr, **kwargs)

    return model


def add_mesh(model, mesh):
    """
    根据给定的mesh，添加Cell和Face. 并对Cell和Face设置基本的属性.
        对于Cell，仅仅设置位置和体积这两个属性.
        对于Face，仅仅设置面积和长度这两个属性
    """
    assert isinstance(model, Seepage)
    if mesh is not None:
        # Cell的属性ID
        ca = CellAttrs(model)

        # Face的属性ID
        fa = FaceAttrs(model)

        cell_n0 = model.cell_number

        for c in mesh.cells:
            # 对于Cell，仅仅设置位置和体积这两个属性.
            cell = model.add_cell()
            cell.pos = c.pos
            ca.set_vol(cell, c.vol)

        for f in mesh.faces:
            # 对于Face，仅仅设置面积和长度这两个属性
            face = model.add_face(model.get_cell(f.link[0] + cell_n0), model.get_cell(f.link[1] + cell_n0))
            fa.set_s(face, f.area)
            fa.set_length(face, f.length)


def set_init(model, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, dist=0.1,
             temperature=280.0, p=None, s=None, perm=1e-14, heat_cond=1.0,
             sample_dist=None, pore_modulus_range=None, igr=None):
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
    assert isinstance(model, Seepage)

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

    # Cell的属性ID
    ca = CellAttrs(model)

    # Face的属性ID
    fa = FaceAttrs(model)

    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        pos = cell.pos
        ca.set_ini(cell, porosity=porosity(*pos), pore_modulus=pore_modulus(*pos), denc=denc(*pos),
                   temperature=temperature(*pos), p=p(*pos), s=s(*pos),
                   pore_modulus_range=pore_modulus_range, dist=dist(*pos))

    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        p0 = face.get_cell(0).pos
        p1 = face.get_cell(1).pos
        fa.set_ini(face, perm=get_average_perm(p0, p1, perm, sample_dist),
                   heat_cond=get_average_perm(p0, p1, heat_cond, sample_dist), igr=igr(*face.pos))
