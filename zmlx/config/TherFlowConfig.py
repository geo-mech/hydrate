from zml import *


class TherFlowConfig(Object):
    """
    传热-渗流耦合模型的配置。假设流体的密度和粘性系数都是压力和温度的函数，并利用二维的插值体来表示。
    此类仅仅用于辅助Seepage类用于热流耦合模拟。
    """
    FluProperty = Seepage.FluDef

    def __init__(self, *args):
        """
        给定流体属性进行初始化. 给定的参数应该为流体属性定义(或者多个流体组成的混合物)、或者是化学反应的定义
        """
        self.fluids = []
        self.reactions = []  # 组分之间的反应
        for arg in args:
            self.add_fluid(arg)
        self.flu_keys = AttrKeys('specific_heat', 'temperature')
        # fv0: 初始时刻的流体体积<流体体积的参考值>
        # vol: 网格的几何体积。这个体积乘以孔隙度，就等于孔隙体积
        self.cell_keys = AttrKeys('mc', 'temperature', 'g_heat', 'pre', 'vol', 'fv0')
        # g0：初始时刻的导流系数<当流体体积为fv0的时候的导流系数>
        self.face_keys = AttrKeys('g_heat', 'area', 'length', 'g0', 'perm', 'igr')
        self.model_keys = AttrKeys('dt', 'time', 'step', 'dv_relative', 'dt_min', 'dt_max')
        # 用于更新流体的导流系数
        self.krf = None
        # 定义一些开关
        self.disable_update_den = False
        self.disable_update_vis = False
        self.disable_ther = False
        self.disable_heat_exchange = False
        # 一个在更新流体的时候，暂时存储固体的一个缓冲区（需要将固体定义为最后一种组分）
        self.has_solid = False
        self.solid_buffer = Seepage.CellData()
        # 流体的扩散. 在多相流操作之后被调用. （也可以用于其它和流动相关的操作）
        self.diffusions = []
        # 在每一步流体计算之前，对模型的cond属性进行更新.
        self.cond_updaters = []
        # 当gravity非None的时候，将设置模型的重力属性
        self.gravity = None
        # 允许的最大时间步长
        self.dt_max = None
        self.dt_min = None
        self.dt_ini = None
        self.dv_relative = None
        # 在更新流体的密度的时候，所允许的最大的流体压力
        self.pre_max = 100e6
        # 用以存储各个组分的ID. since 2023-5-30
        self.components = {}

    def set_specific_heat(self, elem, value):
        """
        设置比热
        """
        if isinstance(elem, Seepage.FluData):
            elem.set_attr(self.flu_keys['specific_heat'], value)
            return

    def get_specific_heat(self, elem):
        if isinstance(elem, Seepage.FluData):
            return elem.get_attr(self.flu_keys['specific_heat'])

    def set_temperature(self, elem, value):
        """
        设置温度
        """
        if isinstance(elem, Seepage.FluData):
            elem.set_attr(self.flu_keys['temperature'], value)
            return

        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['temperature'], value)
            return

    def get_temperature(self, elem):
        """
        设置温度
        """
        if isinstance(elem, Seepage.FluData):
            return elem.get_attr(self.flu_keys['temperature'])

        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['temperature'])

    set_flu_specific_heat = set_specific_heat
    set_flu_temperature = set_temperature

    def set_mc(self, elem, value):
        """
        质量乘以比热
        """
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['mc'], value)
            return

    def get_mc(self, elem):
        """
        质量乘以比热
        """
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['mc'])

    def set_fv0(self, elem, value):
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['fv0'], value)
            return

    def get_fv0(self, elem):
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['fv0'])

    set_cell_mc = set_mc
    set_cell_temperature = set_temperature

    def set_g_heat(self, elem, value):
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['g_heat'], value)
            return

        if isinstance(elem, Seepage.FaceData):
            elem.set_attr(self.face_keys['g_heat'], value)
            return

    def get_g_heat(self, elem):
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['g_heat'])

        if isinstance(elem, Seepage.FaceData):
            return elem.get_attr(self.face_keys['g_heat'])

    set_cell_g_heat = set_g_heat

    def set_vol(self, elem, value):
        """
        设置cell的体积
        """
        if isinstance(elem, Seepage.CellData):
            elem.set_attr(self.cell_keys['vol'], value)
            return

    def get_vol(self, elem):
        """
        设置cell的体积
        """
        if isinstance(elem, Seepage.CellData):
            return elem.get_attr(self.cell_keys['vol'])

    set_cell_vol = set_vol
    set_face_g_heat = set_g_heat

    def set_area(self, elem, value):
        """
        设置face的横截面积
        """
        elem.set_attr(self.face_keys['area'], value)

    def get_area(self, elem):
        """
        设置face的横截面积
        """
        return elem.get_attr(self.face_keys['area'])

    set_face_area = set_area

    def set_length(self, face, value):
        """
        设置face的长度
        """
        face.set_attr(self.face_keys['length'], value)

    def get_length(self, face):
        """
        设置face的长度
        """
        return face.get_attr(self.face_keys['length'])

    set_face_length = set_length

    def set_g0(self, face, value):
        """
        设置face的初始的导流系数（在没有固体存在的时候的原始值）
        """
        face.set_attr(self.face_keys['g0'], value)

    def get_g0(self, face):
        """
        设置face的初始的导流系数（在没有固体存在的时候的原始值）
        """
        return face.get_attr(self.face_keys['g0'])

    set_face_g0 = set_g0

    def add_fluid(self, flu):
        """
        添加一种流体(或者是一种混合物<此时给定一个list或者tuple>)，并且返回流体的ID
        """
        if not isinstance(flu, TherFlowConfig.FluProperty):
            for elem in flu:
                assert isinstance(elem, TherFlowConfig.FluProperty)
        index = len(self.fluids)
        self.fluids.append(flu)
        return index

    def get_fluid(self, index):
        """
        返回给定序号的流体定义
        """
        assert 0 <= index < self.fluid_number
        return self.fluids[index]

    @property
    def fluid_number(self):
        """
        流体的数量
        """
        return len(self.fluids)

    def set_cell(self, cell, pos=None, vol=None, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, dist=0.1,
                 temperature=280.0, p=1.0, s=None, pore_modulus_range=None):
        """
        设置Cell的初始状态.
        """
        if pos is not None:
            cell.pos = pos
        else:
            pos = cell.pos

        if vol is not None:
            cell.set_attr(self.cell_keys['vol'], vol)
        else:
            vol = cell.get_attr(self.cell_keys['vol'])
            assert vol is not None

        cell.set_ini(ca_mc=self.cell_keys['mc'], ca_t=self.cell_keys['temperature'],
                     fa_t=self.flu_keys['temperature'], fa_c=self.flu_keys['specific_heat'],
                     pos=pos, vol=vol, porosity=porosity,
                     pore_modulus=pore_modulus,
                     denc=denc,
                     temperature=temperature, p=p, s=s,
                     pore_modulus_range=pore_modulus_range)

        cell.set_attr(self.cell_keys['fv0'], cell.fluid_vol)
        cell.set_attr(self.cell_keys['g_heat'], vol / (dist ** 2))

    def set_face(self, face, area=None, length=None, perm=None, heat_cond=None, igr=None):
        """
        对一个Face进行配置
        """
        if area is not None:
            face.set_attr(self.face_keys['area'], area)
        else:
            area = face.get_attr(self.face_keys['area'])
            assert area is not None

        if length is not None:
            face.set_attr(self.face_keys['length'], length)
        else:
            length = face.get_attr(self.face_keys['length'])
            assert length is not None

        assert area > 0 and length > 0

        if perm is not None:
            face.set_attr(self.face_keys['perm'], perm)
        else:
            perm = face.get_attr(self.face_keys['perm'])
            assert perm is not None

        g0 = area * perm / length
        face.cond = g0

        face.set_attr(self.face_keys['g0'], g0)

        if heat_cond is not None:
            face.set_attr(self.face_keys['g_heat'], area * heat_cond / length)

        if igr is not None:
            face.set_attr(self.face_keys['igr'], igr)

    def set_model(self, model, porosity=0.1, pore_modulus=1000e6, denc=1.0e6, dist=0.1,
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

        for cell in model.cells:
            assert isinstance(cell, Seepage.Cell)
            pos = cell.pos
            self.set_cell(cell, porosity=porosity(*pos), pore_modulus=pore_modulus(*pos), denc=denc(*pos),
                          temperature=temperature(*pos), p=p(*pos), s=s(*pos),
                          pore_modulus_range=pore_modulus_range, dist=dist(*pos))

        for face in model.faces:
            assert isinstance(face, Seepage.Face)
            p0 = face.get_cell(0).pos
            p1 = face.get_cell(1).pos
            self.set_face(face, perm=get_average_perm(p0, p1, perm, sample_dist),
                          heat_cond=get_average_perm(p0, p1, heat_cond, sample_dist), igr=igr(*face.pos))

    def add_cell(self, model, *args, **kwargs):
        """
        添加一个新的Cell，并返回Cell对象
        """
        cell = model.add_cell()
        self.set_cell(cell, *args, **kwargs)
        return cell

    def add_face(self, model, cell0, cell1, *args, **kwargs):
        """
        添加一个Face，并且返回
        """
        face = model.add_face(cell0, cell1)
        self.set_face(face, *args, **kwargs)
        return face

    def add_mesh(self, model, mesh):
        """
        根据给定的mesh，添加Cell和Face. 并对Cell和Face设置基本的属性.
            对于Cell，仅仅设置位置和体积这两个属性.
            对于Face，仅仅设置面积和长度这两个属性.
        """
        if mesh is not None:
            ca_vol = self.cell_keys['vol']
            fa_s = self.face_keys['area']
            fa_l = self.face_keys['length']

            cell_n0 = model.cell_number

            for c in mesh.cells:
                cell = model.add_cell()
                cell.pos = c.pos
                cell.set_attr(ca_vol, c.vol)

            for f in mesh.faces:
                face = model.add_face(model.get_cell(f.link[0] + cell_n0), model.get_cell(f.link[1] + cell_n0))
                face.set_attr(fa_s, f.area)
                face.set_attr(fa_l, f.length)

    def create(self, mesh=None, model=None, **kwargs):
        """
        利用给定的网格来创建一个模型
        """
        if model is None:
            model = Seepage()

        if self.disable_update_den:
            model.add_tag('disable_update_den')

        if self.disable_update_vis:
            model.add_tag('disable_update_vis')

        if self.disable_ther:
            model.add_tag('disable_ther')

        if self.disable_heat_exchange:
            model.add_tag('disable_heat_exchange')

        if self.has_solid:
            model.add_tag('has_solid')

        # 添加流体的定义和反应的定义 (since 2023-4-5)
        model.clear_fludefs()  # 首先，要清空已经存在的流体定义.
        for flu in self.fluids:
            model.add_fludef(Seepage.FluDef.create(flu))

        model.clear_reactions()  # 清空已经存在的定义.
        for r in self.reactions:
            model.add_reaction(r)

        # 设置重力
        if self.gravity is not None:
            assert len(self.gravity) == 3
            model.gravity = self.gravity

        if self.dt_max is not None:
            self.set_dt_max(model, self.dt_max)

        if self.dt_min is not None:
            self.set_dt_min(model, self.dt_min)

        if self.dt_ini is not None:
            self.set_dt(model, self.dt_ini)

        if self.dv_relative is not None:
            self.set_dv_relative(model, self.dv_relative)

        if self.krf is not None:
            igr = model.add_gr(self.krf, need_id=True)
        else:
            igr = None

        if mesh is not None:
            self.add_mesh(model, mesh)

        self.set_model(model, igr=igr, **kwargs)

        return model

    def get_dt(self, model):
        """
        返回模型内存储的时间步长
        """
        value = model.get_attr(self.model_keys['dt'])
        if value is None:
            return 1.0e-10
        else:
            return value

    def set_dt(self, model, dt):
        """
        设置模型的时间步长
        """
        model.set_attr(self.model_keys['dt'], dt)

    def get_time(self, model):
        """
        返回模型的时间
        """
        value = model.get_attr(self.model_keys['time'])
        if value is None:
            return 0
        else:
            return value

    def set_time(self, model, value):
        """
        设置模型的时间
        """
        model.set_attr(self.model_keys['time'], value)

    def update_time(self, model, dt=None):
        """
        更新模型的时间
        """
        if dt is None:
            dt = self.get_dt(model)
        self.set_time(model, self.get_time(model) + dt)

    def get_step(self, model):
        """
        返回模型迭代的次数
        """
        value = model.get_attr(self.model_keys['step'])
        if value is None:
            return 0
        else:
            return int(value)

    def set_step(self, model, step):
        """
        设置模型迭代的步数
        """
        model.set_attr(self.model_keys['step'], step)

    def get_dv_relative(self, model):
        """
        每一个时间步dt内流体流过的网格数. 用于控制时间步长. 正常取值应该在0到1之间.
        """
        value = model.get_attr(self.model_keys['dv_relative'])
        if value is None:
            return 0.1
        else:
            return value

    def set_dv_relative(self, model, value):
        model.set_attr(self.model_keys['dv_relative'], value)

    def get_dt_min(self, model):
        """
        允许的最小的时间步长
            注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
        """
        value = model.get_attr(self.model_keys['dt_min'])
        if value is None:
            return 1.0e-15
        else:
            return value

    def set_dt_min(self, model, value):
        model.set_attr(self.model_keys['dt_min'], value)

    def get_dt_max(self, model):
        """
        允许的最大的时间步长
            注意: 这是对时间步长的一个硬约束。当利用dv_relative计算的步长不在此范围内的时候，则将它强制拉回到这个范围.
        """
        value = model.get_attr(self.model_keys['dt_max'])
        if value is None:
            return 1.0e10
        else:
            return value

    def set_dt_max(self, model, value):
        model.set_attr(self.model_keys['dt_max'], value)

    def iterate(self, model, dt=None, solver=None, fa_s=None, fa_q=None, fa_k=None):
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
            self.set_dt(model, dt)

        dt = self.get_dt(model)
        assert dt is not None, 'You must set dt before iterate'

        if model.not_has_tag('disable_update_den') and model.fludef_number > 0:
            model.update_den(relax_factor=0.3, fa_t=self.flu_keys['temperature'])

        if model.not_has_tag('disable_update_vis') and model.fludef_number > 0:
            model.update_vis(ca_p=self.cell_keys['pre'], fa_t=self.flu_keys['temperature'],
                             relax_factor=1.0, min=1.0e-7, max=1.0)

        if model.injector_number > 0:
            model.apply_injectors(dt)

        has_solid = model.has_tag('has_solid')

        if has_solid:
            # 此时，认为最后一种流体其实是固体，并进行备份处理
            model.pop_fluids(self.solid_buffer)

        if model.gr_number > 0:
            # 此时，各个Face的导流系数是可变的.
            # 注意：
            #   在建模的时候，务必要设置Cell的v0属性，Face的g0属性和ikr属性，并且，在model中，应该有相应的kr和它对应。
            #   为了不和真正流体的kr混淆，这个Face的ikr，应该大于流体的数量。
            model.update_cond(v0=self.cell_keys['fv0'], g0=self.face_keys['g0'], krf=self.face_keys['igr'],
                              relax_factor=0.3)

        # 施加cond的更新操作
        for update in self.cond_updaters:
            update(model)

        # 当未禁止更新flow且流体的数量非空
        update_flow = model.not_has_tag('disable_flow') and model.fludef_number > 0

        if update_flow:
            if model.has_tag('has_inertia'):
                r1 = model.iterate(dt=dt, solver=solver, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=self.cell_keys['pre'])
            else:
                r1 = model.iterate(dt=dt, solver=solver, ca_p=self.cell_keys['pre'])
        else:
            r1 = None

        # 执行所有的扩散操作，这一步需要在没有固体存在的条件下进行
        for update in self.diffusions:
            update(model, dt)

        if has_solid:
            # 恢复备份的固体物质
            model.push_fluids(self.solid_buffer)

        update_ther = model.not_has_tag('disable_ther')

        if update_ther:
            r2 = model.iterate_thermal(dt=dt, solver=solver, ca_t=self.cell_keys['temperature'],
                                       ca_mc=self.cell_keys['mc'], fa_g=self.face_keys['g_heat'])
        else:
            r2 = None

        # 不存在禁止标识且存在流体
        exchange_heat = model.not_has_tag('disable_heat_exchange') and model.fludef_number > 0

        if exchange_heat:
            model.exchange_heat(dt=dt, ca_g=self.cell_keys['g_heat'],
                                ca_t=self.cell_keys['temperature'],
                                ca_mc=self.cell_keys['mc'],
                                fa_t=self.flu_keys['temperature'],
                                fa_c=self.flu_keys['specific_heat'])

        # 优先使用模型中定义的反应
        for idx in range(model.reaction_number):
            reaction = model.get_reaction(idx)
            assert isinstance(reaction, Reaction)
            reaction.react(model, dt)

        self.set_time(model, self.get_time(model) + dt)
        self.set_step(model, self.get_step(model) + 1)

        if not getattr(self, 'disable_update_dt', None):
            # 只要不禁用dt更新，就尝试更新dt
            if update_flow or update_ther:
                # 只有当计算了流动或者传热过程，才可以使用自动的时间步长
                dt = self.get_recommended_dt(model, dt, self.get_dv_relative(model),
                                             using_flow=update_flow,
                                             using_ther=update_ther
                                             )
            dt = max(self.get_dt_min(model), min(self.get_dt_max(model), dt))
            self.set_dt(model, dt)  # 修改dt为下一步建议使用的值

        return r1, r2

    def get_recommended_dt(self, model, previous_dt, dv_relative=0.1, using_flow=True, using_ther=True):
        """
        在调用了iterate函数之后，调用此函数，来获取更优的时间步长.
        """
        assert using_flow or using_ther
        if using_flow:
            dt1 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=dv_relative)
        else:
            dt1 = 1.0e100

        if using_ther:
            dt2 = model.get_recommended_dt(previous_dt=previous_dt, dv_relative=dv_relative,
                                           ca_t=self.cell_keys['temperature'], ca_mc=self.cell_keys['mc'])
        else:
            dt2 = 1.0e100
        return min(dt1, dt2)

    def to_fmap(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.to_fmap> will be removed after 2024-5-5',
                      DeprecationWarning)

    def from_fmap(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.from_fmap> will be removed after 2024-5-5',
                      DeprecationWarning)

    def save(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.save> will be removed after 2024-5-5',
                      DeprecationWarning)

    def load(self, *args, **kwargs):
        warnings.warn('<TherFlowConfig.load> will be removed after 2024-5-5',
                      DeprecationWarning)

    def update_g0(self, model, fa_g0=None, fa_k=None, fa_s=None, fa_l=None):
        """
        利用各个Face的渗透率、面积、长度来更新Face的g0属性;
        """
        assert isinstance(model, Seepage)
        if fa_g0 is None:
            fa_g0 = self.face_keys['g0']
        if fa_k is None:
            fa_k = self.face_keys['perm']
        if fa_s is None:
            fa_s = self.face_keys['area']
        if fa_l is None:
            fa_l = self.face_keys['length']
        model.update_g0(fa_g0=fa_g0, fa_k=fa_k, fa_s=fa_s, fa_l=fa_l)


SeepageTher = TherFlowConfig
