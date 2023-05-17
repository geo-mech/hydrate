# -*- coding: utf-8 -*-


import warnings

from zml import *


def get_mg_vs_mh(Nh=6.0):
    """
    返回1kg水合物分解之后产生的甲烷气体的质量(kg)
    """
    return 16.0 / (18.0 * Nh + 16.0)


def get_ch4_density(p, T):
    T = max(270.0, min(290.0, T))
    p = max(0.1E6, min(40.0E6, p))
    return (0.016042 * p / (8.314 * T)) * (1.0 + 0.025 * p / 1.0E6 - 0.000645 * math.pow(p / 1.0E6, 2))


def get_ch4_viscosity(p, T):
    T = max(270.0, min(290.0, T))
    p = max(0.1E6, min(40.0E6, p))
    return 10.3E-6 * (1.0 + 0.053 * (p / 1.0E6) * math.pow(280.0 / T, 3))


def get_h2o_density(p, T):
    T = max(272.0, min(300.0, T))
    return 999.8 * (1.0 + (p / 2000.0E6)) * (1.0 - 0.0002 * math.pow((T - 277.0) / 5.6, 2))


def get_h2o_viscosity(p, T):
    T = max(272.0, min(300.0, T))
    return 2.0E-6 * math.exp(1808.5 / T)


def create_ch4_density():
    data = Interp2()
    data.create(1.0e6, 0.1e6, 40e6, 270, 1, 290, get_ch4_density)
    return data


def create_ch4_viscosity():
    data = Interp2()
    data.create(1.0e6, 0.1e6, 40e6, 270, 1, 290, get_ch4_viscosity)
    return data


def create_h2o_density():
    data = Interp2()
    data.create(1.0e6, 0.1e6, 40e6, 270, 1, 290, get_h2o_density)
    return data


def create_h2o_viscosity():
    data = Interp2()
    data.create(1.0e6, 0.1e6, 40e6, 270, 1, 290, get_h2o_viscosity)
    return data


def create_t2p_TH():
    """
    温度压力曲线：Tough+Hydrate中使用的数据
    """
    T = [148.714, 154.578, 159.889, 166.418, 174.827, 183.458, 192.199, 200.277, 207.026, 213.887, 222.739, 231.259,
         236.017, 241.438, 247.746, 253.278, 258.257, 261.134, 265.007, 267.663, 270.207, 272.752, 275.408, 278.728,
         281.494, 284.703, 287.69, 289.461, 291.784, 293.776, 295.325, 297.095, 299.198, 302.185, 304.066, 305.726,
         307.497, 309.488, 311.48, 313.14, 316.017, 317.566, 319.004, 320, 320.221]
    p = [5262.24, 8054.63, 11965.9, 18591.3, 32551.1, 56148.2, 94000.9, 147142, 209015, 292504, 434544, 617269, 738443,
         890026, 1.10525e+06, 1.34212e+06, 1.57001e+06, 1.73008e+06, 1.96429e+06, 2.16456e+06, 2.34989e+06, 2.57021e+06,
         3.23978e+06, 4.56786e+06, 6.11232e+06, 8.68254e+06, 1.23335e+07, 1.5089e+07, 2.01908e+07, 2.60274e+07,
         3.16053e+07, 3.95423e+07, 5.13549e+07, 7.24068e+07, 8.85833e+07, 1.05184e+08, 1.23967e+08, 1.46104e+08,
         1.73484e+08, 1.98446e+08, 2.57728e+08, 3.0149e+08, 3.57991e+08, 3.97448e+08, 4.47894e+08]
    return Interp1(x=T, y=p).to_evenly_spaced(300)


def create_p2t_TH():
    """
    温度压力曲线：Tough+Hydrate中使用的数据
    """
    T = [148.714, 154.578, 159.889, 166.418, 174.827, 183.458, 192.199, 200.277, 207.026, 213.887, 222.739, 231.259,
         236.017, 241.438, 247.746, 253.278, 258.257, 261.134, 265.007, 267.663, 270.207, 272.752, 275.408, 278.728,
         281.494, 284.703, 287.69, 289.461, 291.784, 293.776, 295.325, 297.095, 299.198, 302.185, 304.066, 305.726,
         307.497, 309.488, 311.48, 313.14, 316.017, 317.566, 319.004, 320, 320.221]
    p = [5262.24, 8054.63, 11965.9, 18591.3, 32551.1, 56148.2, 94000.9, 147142, 209015, 292504, 434544, 617269, 738443,
         890026, 1.10525e+06, 1.34212e+06, 1.57001e+06, 1.73008e+06, 1.96429e+06, 2.16456e+06, 2.34989e+06, 2.57021e+06,
         3.23978e+06, 4.56786e+06, 6.11232e+06, 8.68254e+06, 1.23335e+07, 1.5089e+07, 2.01908e+07, 2.60274e+07,
         3.16053e+07, 3.95423e+07, 5.13549e+07, 7.24068e+07, 8.85833e+07, 1.05184e+08, 1.23967e+08, 1.46104e+08,
         1.73484e+08, 1.98446e+08, 2.57728e+08, 3.0149e+08, 3.57991e+08, 3.97448e+08, 4.47894e+08]
    return Interp1(x=p, y=T).to_evenly_spaced(300)


core.use(None, 'update_hyd', c_void_p, c_double,
         c_void_p, c_void_p,
         c_size_t, c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t,
         c_size_t
         )


def update_hyd(model, dt, fid_g, fid_w, fid_h, ca_h2g, ca_g2h, fa_t, fa_c, wa_ms, ha_dE, ha_mg,
               ph_curve=None, sal_curve=None):
    """
    更新水合物、水、气的质量和密度，同时更新温度。其中model为Seepage的实例;
    dt为时间步长;
    ph_curve是温度压力曲线，sal_curve是盐度对温度的修改；
    另外，此函数运行依赖于Seepage的自定义属性:
    其中，fid_g为gas的id, fid_w为water的id, fid_h为hydrate的id;
    ca_h2g为cell中g_h2g的id, ca_g2h为cell中g_g2h的id，这两个属性定义水合物分解和合成的速度
    fa_t和fa_c为流体中温度和比热容的属性id; wa_ms为水中盐度的属性id; ha_dE为水合物中相变潜热的属性id；ha_mg为水合物属性中单位质量水合物
    分解产生的气体质量的属性id
    """
    assert isinstance(model, Seepage)
    assert dt > 0
    if ph_curve is None:
        ph_curve = create_t2p_TH()
    if sal_curve is None:
        sal_curve = Interp1()
        sal_curve.set(y=0)
    assert isinstance(ph_curve, Interp1)
    assert isinstance(sal_curve, Interp1)
    core.update_hyd(model.handle, dt, ph_curve.handle, sal_curve.handle,
                    fid_g, fid_w, fid_h,
                    ca_h2g, ca_g2h,
                    fa_t, fa_c, wa_ms, ha_dE, ha_mg)


core.use(None, 'update_hyd2', c_void_p, c_double, c_void_p,
         c_size_t, c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t,
         c_size_t
         )


def update_hyd2(model, dt, fid_g, fid_w, fid_h, ca_h2g, ca_g2h, ca_dtemp, fa_t, fa_c, ha_dE, ha_mg, p2t=None):
    """
    更新水合物、水、气的质量和密度，同时更新温度。其中model为Seepage的实例;
    dt为时间步长;
    p2t是压力-温度曲线
    另外，此函数运行依赖于Seepage的自定义属性:
    其中，fid_g为gas的id, fid_w为water的id, fid_h为hydrate的id;
    ca_h2g为cell中g_h2g的id, ca_g2h为cell中g_g2h的id，这两个属性定义水合物分解和合成的速度
    fa_t和fa_c为流体中温度和比热容的属性id; ha_dE为水合物中相变潜热的属性id；ha_mg为水合物属性中单位质量水合物
    分解产生的气体质量的属性id
    """
    assert isinstance(model, Seepage)
    assert dt > 0
    if p2t is None:
        p2t = create_p2t_TH()
    assert isinstance(p2t, Interp1)
    core.update_hyd2(model.handle, dt, p2t.handle,
                     fid_g, fid_w, fid_h,
                     ca_h2g, ca_g2h, ca_dtemp,
                     fa_t, fa_c, ha_dE, ha_mg)


core.use(None, 'update_ice', c_void_p, c_double,
         c_size_t, c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t, c_size_t)


def update_ice(model, dt, fid_i, fid_w, fa_t, fa_c, ia_dE, ia_teq, ca_i2w=999999999, ca_w2i=999999999):
    """
    更新水和冰的质量，同时更新流体的温度。其中model为渗流模型，fid_w为水的流体ID，fid_i为冰的流体ID，fa_t为流体
    中温度属性的ID，fa_c为流体的比热属性的ID，ia_dE为冰的相变潜热的ID，ia_teq为冰的相变温度的ID。
    属性ca_i2w和ca_w2i定义冰和水之间发生相变的“半衰期”，及即特征时间。当属性不存在，则默认半衰期为0。
    """
    assert isinstance(model, Seepage)
    core.update_ice(model.handle, dt, fid_i, fid_w, fa_t, fa_c, ia_dE, ia_teq, ca_i2w, ca_w2i)


get_time_str = time2str
get_mass_str = mass2str


def has_no_cell(obj):
    return obj.cell_number == 0


def property_by_attr(index, default_val=None, min=-1.0e100, max=1.0e100, writable=None, convert=None):
    """
    在类中定义一个属性，该属性利用 get_attr和set_attr函数来读写属性的值
    """

    def get(obj):
        val = obj.get_attr(index=index, default_val=default_val, min=min, max=max)
        if convert is None:
            return val
        else:
            return convert(val)

    def set(obj, value):
        if writable is not None:
            assert writable(obj)
        assert min <= value <= max
        obj.set_attr(index=index, value=value)

    return property(get, set)


def property_by_model_attr(index, default_val=None, min=-1.0e100, max=1.0e100, writable=has_no_cell):
    def get(obj):
        return obj.model.get_attr(index=index, default_val=default_val, min=min, max=max)

    def set(obj, value):
        if writable is not None:
            assert writable(obj.model)
        assert min <= value <= max
        obj.model.set_attr(index=index, value=value)

    return property(get, set)


class CellAttrs(Object):
    """
    单元的附加属性：其中vol为单元的网格体积(m^3)；g_h2g为水合物分解的速度(与相平衡温度的差为1K时，1秒内分解的质量)；
    g_h2g为水合物合成的的速度(与相平衡温度的差为1K时，1秒内生成的质量)；
    g_heat为单元内，流体和固体热传导的系数：当流体和固体的温度差为1K时，1秒内传递的热量(J)；
    T为单位的温度；
    mc为单元内固体的质量和比热的乘积；v_pore为Cell内孔隙空间的总体积；fp为迭代之后的流体压力（不是利用体积计算的压力）
    """
    vol = 0
    g_h2g = 1
    g_g2h = 2
    g_heat = 3
    T = 4
    mc = 5
    v_pore = 6  # 孔隙体积. 孔隙度=v_pore/vol
    fp = 7
    t_i2w = 8
    t_w2i = 9


class FaceAttrs(Object):
    """
    面的附加属性：其中area为Face的面积，length为流体经过Face流动的距离（Face两侧Cell之间的距离）
    g_heat为face作为热传导通道的时候的导热系数
    """
    area = 0
    length = 1
    g_heat = 2


class FluAttrs(Object):
    """
    流体共有的附加属性ID：其中T为流体的温度；c为流体的比热系数
    """
    T = 0
    c = 1


class GasAttrs(Object):
    """
    气体特有的属性ID，不可覆盖FluAttrs已经定义的ID
    """
    pass


class WaterAttrs(Object):
    """
    水的附加属性；ms为水中盐的浓度；mg为溶解气的质量分数
    """
    ms = 2
    mg = 3


class HydAttrs(Object):
    """
    水合物的附加属性：其中dE为1kg水合物相变的潜热(J)；mg为1kg水合物分解之后产生的气体的质量(kg)
    """
    dE = 2
    mg = 3


class IceAttrs(Object):
    """
    水冰的附加属性: 其中dE为1kg的冰相变的潜热(J)；teq为冰发生相变的温度(K)
    """
    dE = 2
    teq = 3


class Attrs(Object):
    """
    用以存储以上定义的所有的属性ID，切勿修改任何属性ID的值。此类用于模型中，已经弃用。
    """
    cell = CellAttrs()
    face = FaceAttrs()
    flu = FluAttrs()
    gas = GasAttrs()
    water = WaterAttrs()
    hyd = HydAttrs()
    ice = IceAttrs()


class FluIds(Object):
    """
    在渗流模型中，各种流体的ID。其中水合物和冰为特殊的流体（粘性系数等于无穷大）。
    """
    gas = 0
    water = 1
    hyd = 2
    ice = 3


class ModelAttrs(Object):
    """
    模型的属性ID（在后期更改时，切勿修改任何属性ID的数值）. 其中：
    dt为模型当前（下一步iterate时）所采用的时间步长。该dt可能会在iterate结束的时候自动更新；
    dm_relative为在每一步中，一个face所输运的流体的质量与face相邻的Cell内的质量的比值，用于确定时间步长dt；
    nloop1和nloop2分别为渗流和热传导过程更新的时候内核的迭代次数；
    precision_p为压力的迭代精度；precision_T为温度的迭代精度；
    """
    step = 0
    time = 1
    dt = 2
    dt_min = 3
    dt_max = 4
    dm_relative = 5
    nloop1 = 6
    nloop2 = 7
    precision_p = 8
    precision_T = 9

    # 冰的属性ID
    ice_den = 10
    ice_dE = 11
    ice_c = 12
    ice_teq = 13

    # 水合物的属性ID
    hyd_den = 15
    hyd_dE = 16
    hyd_c = 17

    # 水的属性ID
    water_den = 20
    water_c = 22

    # 气体的属性ID
    gas_den_min = 25
    gas_den_max = 26
    gas_c = 28

    # 迭代属性
    nloop_max = 30
    ratio_max = 31

    # 气和水之间的毛管压力，用于平衡饱和度
    pc_max = 35


class HydModel(Seepage):
    """
    热流耦合的水合物计算模型的Python接口。这个Model类导出了C++中类的几乎所有的接口。此类仅
    处理<流动>相关的内容。如果需要和应力进行耦合，需要借助其它的模块。
    """

    class FluidBase(Seepage.Fluid):
        def __init__(self, cell, fid):
            assert isinstance(cell, HydModel.Cell)
            super(HydModel.FluidBase, self).__init__(cell, fid)

        temperature = property_by_attr(FluAttrs.T, default_val=None, min=0.0, max=10000.0)
        specific_heat = property_by_attr(FluAttrs.c, default_val=None, min=1.0e-3, max=1.0e5)

    class FluWater(FluidBase):
        def __init__(self, cell, fid):
            assert isinstance(cell, HydModel.Cell)
            super(HydModel.FluWater, self).__init__(cell, fid)

        ms = property_by_attr(WaterAttrs.ms)
        mg = property_by_attr(WaterAttrs.mg)

    class FluHyd(FluidBase):
        def __init__(self, cell, fid):
            assert isinstance(cell, HydModel.Cell)
            super(HydModel.FluHyd, self).__init__(cell, fid)

        dE = property_by_attr(HydAttrs.dE)
        mg = property_by_attr(HydAttrs.mg)

    class FluIce(FluidBase):
        def __init__(self, cell, fid):
            assert isinstance(cell, HydModel.Cell)
            super(HydModel.FluIce, self).__init__(cell, fid)

        dE = property_by_attr(IceAttrs.dE)
        teq = property_by_attr(IceAttrs.teq)

    class Cell(Seepage.Cell):
        """
        控制单元：流体的存储空间
        """

        def __init__(self, model, index):
            assert isinstance(model, HydModel)
            super(Cell, self).__init__(model, index)
            self.model = model

        def exists(self):
            """
            判断此cell是否存在
            """
            return True

        @property
        def x(self):
            return self.pos[0]

        @property
        def y(self):
            return self.pos[1]

        @property
        def z(self):
            return self.pos[2]

        @property
        def vol(self):
            """
            返回cell的体积。是整个网格的总的体积。如果没有设置过，则返回None
            """
            return self.get_attr(CellAttrs.vol, min=1.0e-20, max=1.0e20)

        @vol.setter
        def vol(self, value):
            """
            设置cell的体积。是整个网格的总的体积。当设置体积的时候，为了保证孔隙度不发生变化，也需要同时修改v0和k.
            应该在添加Cell之后立即设置体积，然后再设置其它的相关属性.
            """
            assert 1.0e-20 < value < 1.0e20
            vol = self.vol
            self.set_attr(CellAttrs.vol, value)
            if vol is not None:  # 此时，是重新设定体积（而非初始设定），因此把和体积相关的一些属性也修改了
                assert vol > 0
                times = value / vol
                self.v0 *= times
                self.k *= times
                if self.g_g2h is not None:
                    self.g_g2h *= times
                if self.g_h2g is not None:
                    self.g_h2g *= times
                if self.g_heat is not None:
                    self.g_heat *= times
                if self.get_attr(CellAttrs.mc) is not None:
                    self.set_attr(CellAttrs.mc, self.get_attr(CellAttrs.mc) * times)
                if self.get_attr(CellAttrs.v_pore) is not None:
                    self.set_attr(CellAttrs.v_pore, self.get_attr(CellAttrs.v_pore) * times)

        @property
        def stress(self):
            warnings.warn('property <stress> is not supported anymore.',
                          DeprecationWarning)
            return 0.0

        @stress.setter
        def stress(self, value):
            warnings.warn('property <stress> is not supported anymore.',
                          DeprecationWarning)

        @property
        def porosity(self):
            """
            孔隙度：气、水、水合物、冰共同的存储空间占据网格体积的比例。取值的范围为0到1之间
            """
            v_pore = self.get_attr(CellAttrs.v_pore, 1.0e-20, 1.0e20)
            vol = self.vol
            if v_pore is not None and vol is not None:
                return v_pore / vol

        @porosity.setter
        def porosity(self, porosity):
            """
            孔隙度：气、水、水合物、冰共同的存储空间占据网格体积的比例。取值的范围为0到1之间
            """
            assert 0 < porosity < 0.7
            vol = self.vol
            assert vol is not None, 'please set vol before set porosity'
            v_pore = vol * porosity
            self.v0 = v_pore
            self.set_attr(CellAttrs.v_pore, v_pore)

        def set_porosity(self, p1, fai1, p2, fai2):
            """
            旧的版本，目前不再支持。在新的版本中，采用确定的孔隙度，请直接利用属性porosity来设置。
            """
            warnings.warn('please use the property <porosity> directly', DeprecationWarning)
            v1 = self.vol * fai1
            v2 = self.vol * fai2
            self.set_pore(p1, v1, p2 - p1, v2 - v1)

        def get_porosity(self, p=None):
            """
            返回给定压力下的孔隙度，该函数目前已经废弃
            """
            warnings.warn('please use the property <porosity> directly', DeprecationWarning)
            return self.porosity

        def get_fluid(self, index):
            flu = super(Cell, self).get_fluid(index)
            return HydModel.FluidBase(flu.cell, flu.fid)

        @property
        def gas(self):
            return self.get_fluid(FluIds.gas)

        @property
        def water(self):
            flu = self.get_fluid(FluIds.water)
            return HydModel.FluWater(flu.cell, flu.fid)

        @property
        def hyd(self):
            flu = self.get_fluid(FluIds.hyd)
            return HydModel.FluHyd(flu.cell, flu.fid)

        @property
        def ice(self):
            flu = self.get_fluid(FluIds.ice)
            return HydModel.FluIce(flu.cell, flu.fid)

        def fill_pore(self, target_p, sg, sw, sh, si, check=True):
            """
            将流体填充进孔隙度，请务必再设置了温度、孔隙度、孔隙弹性等属性之后再调用此函数.
            此函数主要用于设置Cell的初始状态;
            当check为True的时候，将对初始的温度压力状态进行检查（请尽量保证初始的压力温度状态为可以稳定存在的状态）
            """
            if check:
                assert abs(self.tr - self.tf) < 0.01, 'The initial temperture of Rock and Fluid should be Equal'
                p2 = self.model.hyd_t2p.get(self.tf)

                if target_p > p2 + 0.1e6:
                    assert sg < 0.001 or sw <= 0.001 or self.g_g2h_1m3 < 1.0e-10, 'Water and Gas should NOT co-exist while p-T in hydrate region'
                if target_p < p2 - 0.1e6:
                    assert sh < 0.001 or self.g_h2g_1m3 < 1.0e-10, 'Hydrate should NOT exist while p-T is NOT in hydrate region'

                if self.tf > self.ice.teq + 0.1:
                    assert si < 0.001 or self.t_i2w > 1.0e8, f'Ice should not exist when initial T (={self.tf}) is greater than teq (={self.model.ice.teq})'
                if self.tf < self.ice.teq - 0.1:
                    assert sw < 0.001 or self.t_w2i > 1.0e8, f'Water should not exist when initial T (={self.tf}) is smaller than teq (={self.model.ice.teq})'

            self.gas.den = self.model.gas.get_density(target_p, self.gas.temperature)
            self.v0 += (self.get_attr(CellAttrs.v_pore) - self.p2v(target_p))
            self.fill(target_p, (sg, sw, sh, si))
            # Modify viscosity when change pressure
            self.gas.set(vis=self.model.gas.get_vis(target_p, self.gas.temperature))
            self.water.set(vis=self.model.water.get_vis(target_p, self.water.temperature))

        @property
        def mg(self):
            """
            返回cell内气体的质量
            """
            return self.gas.mass

        @mg.setter
        def mg(self, value):
            """
            设置cell内气体的质量（cell的初始化请使用fill_pore，尽量避免直接使用该属性）
            """
            self.gas.mass = value

        @property
        def mw(self):
            """
            返回cell内水的质量
            """
            return self.water.mass

        @mw.setter
        def mw(self, value):
            """
            设置cell内水的质量（cell的初始化请使用fill_pore，尽量避免直接使用该属性）
            """
            self.water.mass = value

        @property
        def mh(self):
            """
            cell内水合物的质量
            """
            return self.hyd.mass

        @mh.setter
        def mh(self, value):
            """
            cell内水合物的质量（cell的初始化请使用fill_pore，尽量避免直接使用该属性）
            """
            self.hyd.mass = value

        @property
        def mi(self):
            """
            cell内冰的质量
            """
            return self.ice.mass

        @mi.setter
        def mi(self, value):
            """
            cell内冰的质量（cell的初始化请使用fill_pore，尽量避免直接使用该属性）
            """
            self.ice.mass = value

        @property
        def ms(self):
            """
            cell内盐分的质量（此版本不支持）
            """
            return self.water.mass * self.water.get_attr(WaterAttrs.ms)

        @ms.setter
        def ms(self, value):
            """
            cell内盐分的质量（此版本不支持）
            """
            self.water.set_attr(WaterAttrs.ms, value / self.water.mass)

        @property
        def deng(self):
            """
            cell内气体的密度（实时采用的值）
            """
            return self.gas.den

        @property
        def denw(self):
            """
            cell内水的密度（实时采用的值）
            """
            return self.water.den

        @property
        def ginw(self):
            """
            溶解气质量(kg)   （此版本不支持）
            """
            return self.water.mass * self.water.get_attr(WaterAttrs.mg)

        @ginw.setter
        def ginw(self, value):
            """
            溶解气质量(kg)   （此版本不支持）
            """
            self.water.set_attr(WaterAttrs.mg, value / self.water.mass)

        @property
        def mcr(self):
            """
            岩石质量乘以岩石的比热
            """
            return self.get_attr(CellAttrs.mc, 1.0e-10, 1.0e40)

        @mcr.setter
        def mcr(self, value):
            """
            岩石质量乘以岩石的比热
            """
            assert 1.0e-10 < value < 1.0e40
            self.set_attr(CellAttrs.mc, value)

        @property
        def dencr(self):
            """
            返回cell内单位体积的岩石的质量乘以岩石的比热（用于计算储能）
            """
            assert self.vol is not None
            return self.mcr / self.vol

        @dencr.setter
        def dencr(self, value):
            """
            设置cell内单位体积的岩石的质量乘以岩石的比热（用于计算储能）
            """
            assert self.vol is not None
            self.mcr = value * self.vol

        @property
        def tf(self):
            """
            返回cell内流体的温度（其中水、气、水合物、冰均被是为流体相）
            """
            return self.water.temperature

        @tf.setter
        def tf(self, value):
            """
            设置cell内流体的温度（其中水、气、水合物、冰均被是为流体相）
            """
            assert 0.0 < value < 10000.0
            self.gas.temperature = value
            self.water.temperature = value
            self.hyd.temperature = value
            self.ice.temperature = value

        @property
        def tr(self):
            """
            cell内rock的温度
            """
            return self.get_attr(CellAttrs.T, 0, 10000.0)

        @tr.setter
        def tr(self, value):
            """
            cell内rock的温度
            """
            assert 0.0 < value < 10000.0
            self.set_attr(CellAttrs.T, value)

        @property
        def pore_modulus(self):
            """
            孔隙的刚度. 单位体积的储层内，孔隙体积变化1时所需要的压力的改变量
            """
            assert self.vol is not None
            return self.vol / self.k

        @pore_modulus.setter
        def pore_modulus(self, value):
            """
            孔隙的刚度. 单位体积的储层内，孔隙体积变化1时所需要的压力的改变量
            注意：
                此参数仅仅用于辅助计算压力（提供一定的松弛空间），并不需要按照真正的孔隙弹性来设置。可以
                根据压力的变化的范围来进行计算。比如孔隙度为0.1，计算模型的压力的波动大约在5MPa左右，
                则这个刚度可以设置为 5Mpa/0.1，即取值大约为 50e6左右。
            """
            assert 1.0e-5 < value < 1.0e10
            assert self.vol is not None
            self.k = self.vol / value

        @property
        def pore_relax_factor(self):
            """
            孔隙度的松弛因子，取值在0到0.1之间
            """
            warnings.warn('Property not supported', DeprecationWarning)

        @pore_relax_factor.setter
        def pore_relax_factor(self, value):
            """
            孔隙度的松弛因子，取值在0到0.1之间。该松弛因子的默认值为0.001，即如果实际孔隙度
            和设定的孔隙度之间存在误差，该误差每一步大约会消除0.001. 默认设置比较小的松弛
            因子，主要是为了计算的稳定。
            """
            warnings.warn('Property not supported', DeprecationWarning)

        @property
        def density_relax_factor(self):
            """
            流体密度的松弛因子，取值在0到0.1之间
            """
            warnings.warn('Property not supported', DeprecationWarning)

        @density_relax_factor.setter
        def density_relax_factor(self, value):
            """
            流体密度的松弛因子，取值在0到0.1之间。默认取值为0.001
            """
            warnings.warn('Property not supported', DeprecationWarning)

        @property
        def ipc(self):
            """
            在这个cell适用的毛管压力曲线的序号
            """
            warnings.warn('Property not supported', DeprecationWarning)

        @ipc.setter
        def ipc(self, value):
            warnings.warn('Property not supported', DeprecationWarning)

        @property
        def g_heat(self):
            """
            cell内流体和固体进行能量交换的导流系数（等于热传导系数*导热面积/导热距离）.
            注意，当网格的体积发生变化了之后，应该重新设置这个值。
            """
            return self.get_attr(CellAttrs.g_heat, 0.0, 1.0e20)

        @g_heat.setter
        def g_heat(self, value):
            """
            cell内流体和固体进行能量交换的导流系数（等于热传导系数*导热面积/导热距离）
            """
            assert value >= 0
            assert self.vol is not None, 'please set vol before set g_heat'
            self.set_attr(CellAttrs.g_heat, value)

        @property
        def g_heat_1m3(self):
            vol = self.vol
            assert vol is not None
            g_heat = self.g_heat
            assert g_heat is not None
            return g_heat / vol

        @g_heat_1m3.setter
        def g_heat_1m3(self, value):
            assert value >= 0
            vol = self.vol
            assert vol is not None, 'please set vol before set g_heat'
            self.g_heat = vol * value

        def set_g_heat(self, heat_cond=2.0, distance=1.0e-2):
            """
            给定热传导系数，以及在一个cell内，流体和固体之间热传导的距离，来设置g_heat的数值。
            务必在vol设置了之后在调用此函数.
            """
            assert distance >= 1.0e-10
            vol = self.vol
            assert vol > 1e-20
            area = vol / distance
            assert 0 < heat_cond < 1e5
            self.g_heat = area * heat_cond / distance

        @property
        def g_g2h(self):
            """
            cell内气体转化为水合物的速度系数(当距离相平衡曲线为1度时，每秒钟分解的kg数)
            """
            return self.get_attr(CellAttrs.g_g2h, 0, 1.0e20)

        @g_g2h.setter
        def g_g2h(self, value):
            """
            cell内气体转化为水合物的速度系数(当距离相平衡曲线为1度时，每秒钟分解的kg数)
            """
            assert self.vol is not None, 'please set vol before set g_g2h'
            assert value >= 0
            self.set_attr(CellAttrs.g_g2h, value)

        @property
        def g_g2h_1m3(self):
            vol = self.vol
            assert vol is not None
            g_g2h = self.g_g2h
            assert g_g2h is not None
            return g_g2h / vol

        @g_g2h_1m3.setter
        def g_g2h_1m3(self, value):
            assert value >= 0
            vol = self.vol
            assert vol is not None, 'please set vol before set g2h'
            self.g_g2h = value * vol

        @property
        def g_h2g(self):
            """
            cell内水合物分解为气体的速度系数(当距离相平衡曲线为1度时，每秒钟的kg数)
            """
            return self.get_attr(CellAttrs.g_h2g, 0, 1.0e20)

        @g_h2g.setter
        def g_h2g(self, value):
            """
            cell内水合物分解为气体的速度系数(当距离相平衡曲线为1度时，每秒钟的kg数)
            """
            assert self.vol is not None, 'please set vol before set g_h2g'
            assert value >= 0
            self.set_attr(CellAttrs.g_h2g, value)

        @property
        def g_h2g_1m3(self):
            vol = self.vol
            assert vol is not None, 'please set vol before using g_h2g'
            return self.g_h2g / vol

        @g_h2g_1m3.setter
        def g_h2g_1m3(self, value):
            assert value >= 0
            vol = self.vol
            assert vol is not None, 'please set vol before using g_h2g'
            self.g_h2g = value * vol

        t_i2w = property_by_attr(CellAttrs.t_i2w)
        t_w2i = property_by_attr(CellAttrs.t_w2i)

        @property
        def update_hyd_enabled(self):
            """
            定义在这个cell中，是否对水合物的量进行更新。在目前的版本中，这个参数不再需要。如果不
            需要更新水合物，则直接将 g_h2g和g_g2h设置为0即可。
            """
            warnings.warn('please set g_h2g and g_g2h instead', DeprecationWarning)
            return self.g_g2h > 1.0e-20 or self.g_h2g > 1.0e-20

        @update_hyd_enabled.setter
        def update_hyd_enabled(self, value):
            warnings.warn('please set g_h2g and g_g2h instead', DeprecationWarning)
            if not value:
                self.g_g2h = 0
                self.g_h2g = 0
            else:
                self.g_g2h_1m3 = 1
                self.g_h2g_1m3 = 1

        @property
        def update_ice_enabled(self):
            """
            定义在这个cell中，是否对ice的量进行更新。在目前的版本中，这个参数不再需要。如果要
            禁止ice的生成，可以将ice的熔点设置到一个更低的温度即可。对于各个cell，则不再支持
            单独的设置。
            """
            warnings.warn('Property not supported', DeprecationWarning)
            return self.ice.get_attr(IceAttrs.teq) > 1.0

        @update_ice_enabled.setter
        def update_ice_enabled(self, value):
            warnings.warn('Property not supported', DeprecationWarning)
            if value:
                self.ice.set_attr(IceAttrs.teq, self.model.ice.teq)
            else:
                self.ice.set_attr(IceAttrs.teq, 0.0)

        @property
        def exchange_heat_enabled(self):
            """
            定义在这个cell中，流体和固体之间是否发生热传导。在目前的版本中，这个参数不再需要。如果
            不需要热传导，则直接将 g_heat这个参数设置为0即可。
            """
            warnings.warn('set g_heat instead', DeprecationWarning)
            return self.g_heat > 1.0e-20

        @exchange_heat_enabled.setter
        def exchange_heat_enabled(self, value):
            warnings.warn('set g_heat instead', DeprecationWarning)
            if not value:
                self.g_heat_1m3 = 0
            else:
                self.g_heat_1m3 = 1.0e6

        @property
        def fv(self):
            return self.fluid_vol

        @property
        def sg(self):
            """
            气体的体积饱和度（气体体积 / 孔隙体积）
            """
            return self.gas.vol_fraction

        @property
        def sw(self):
            """
            水的体积饱和度（水体积 / 孔隙体积）
            """
            return self.water.vol_fraction

        @property
        def sh(self):
            """
            水合物的体积饱和度（水合物体积 / 孔隙体积）
            """
            return self.hyd.vol_fraction

        @property
        def si(self):
            """
            冰的体积饱和度（冰体积 / 孔隙体积）
            """
            return self.ice.vol_fraction

        @property
        def pressure(self):
            """
            返回cell内流体的压力. 根据流体的体积和pore的属性来自动计算的值
            """
            return self.pre

        def get_face(self, i):
            """
            返回与此cell相连的第i个face
            """
            face = super(Cell, self).get_face(i)
            return HydModel.Face(self.model, face.index)

    class Face(Seepage.Face):
        """
        控制单元之间的界面：是流体的流动通道
        """

        def __init__(self, model, index):
            assert isinstance(model, HydModel)
            super(Face, self).__init__(model, index)
            self.model = model

        @property
        def permeability(self):
            """
            face位置储层的渗透率（在没有水合物和冰存在时候的原始渗透率）.当孔隙度发生变化的时候
            应该修改这个渗透率
            """
            return self.cond * self.length / self.area

        @permeability.setter
        def permeability(self, value):
            """
            face位置储层的渗透率（在没有水合物和冰存在时候的原始渗透率）.当孔隙度发生变化的时候
            应该修改这个渗透率
            """
            assert 0 <= value < 1.0
            self.cond = value * self.area / self.length

        @property
        def perm(self):
            """
            permeability的别名
            """
            return self.permeability

        @perm.setter
        def perm(self, value):
            """
            permeability的别名
            """
            self.permeability = value

        @property
        def heat_cond(self):
            """
            热传导系数
            """
            return self.get_attr(FaceAttrs.g_heat, 0, 1.0e20) * self.length / self.area

        @heat_cond.setter
        def heat_cond(self, value):
            """
            热传导系数
            """
            assert 100000 > value >= 0
            self.set_attr(FaceAttrs.g_heat, value * self.area / self.length)

        @property
        def area(self):
            """
            横截面积
            """
            return self.get_attr(FaceAttrs.area, 1.0e-10, 1.0e6)

        @area.setter
        def area(self, value):
            """
            横截面积
            """
            assert 1.0e-10 < value < 1.0e6
            self.set_attr(FaceAttrs.area, value)

        @property
        def length(self):
            """
            垂直于此face，流体流动的距离
            """
            return self.get_attr(FaceAttrs.length, 1.0e-6, 1.0e6)

        @length.setter
        def length(self, value):
            """
            垂直于此face，流体流动的距离
            """
            assert 1.0e-6 < value < 1.0e6
            self.set_attr(FaceAttrs.length, value)

        @property
        def ikr(self):
            """
            这个face使用的相对渗透率曲线的序号
            """
            warnings.warn('property not supported anymore.',
                          DeprecationWarning)

        @length.setter
        def ikr(self, value):
            warnings.warn('property not supported anymore.',
                          DeprecationWarning)

        @property
        def x(self):
            """
            face中心点的x坐标
            """
            return self.pos[0]

        @property
        def y(self):
            """
            face中心点的y坐标
            """
            return self.pos[1]

        @property
        def z(self):
            """
            face中心点的z坐标
            """
            return self.pos[2]

        @property
        def is_gas_path(self):
            """
            是否为gas的流动路径。在此版本，不再支持此属性。如果需要进行流体的流动，则直接将属性
            perm修改为0即可
            """
            warnings.warn('use peoperty <perm> instead', DeprecationWarning)
            return self.perm > 1.0e-30

        @is_gas_path.setter
        def is_gas_path(self, value):
            if not value:
                self.perm = 0
            warnings.warn('use peoperty <perm> instead', DeprecationWarning)

        @property
        def is_water_path(self):
            """
            是否为water的流动路径。在此版本，不再支持此属性。如果需要进行流体的流动，则直接将属性
            perm修改为0即可
            """
            warnings.warn('use peoperty <perm> instead', DeprecationWarning)
            return self.perm > 1.0e-30

        @is_water_path.setter
        def is_water_path(self, value):
            if not value:
                self.perm = 0
            warnings.warn('use peoperty <perm> instead', DeprecationWarning)

        @property
        def is_heat_path(self):
            """
            是否支持热传导。在此版本中，不再支持这个属性。如果要禁止热传导，则直接将heat_cond这个
            属性设置为0即可。
            """
            warnings.warn('use heat_cond instead', DeprecationWarning)
            return self.heat_cond > 1.0e-10

        @is_heat_path.setter
        def is_heat_path(self, value):
            if not value:
                self.heat_cond = 0
            warnings.warn('use heat_cond instead', DeprecationWarning)

        def get_cell(self, i):
            """
            返回与此face相连的第i个cell
            """
            cell = super(Face, self).get_cell(i)
            if cell is not None:
                return HydModel.Cell(self.model, cell.index)

    class IceProperty(Object):
        """
        定义冰的各种属性
        """

        def __init__(self, model):
            assert isinstance(model, HydModel)
            self.model = model

        den = property_by_model_attr(ModelAttrs.ice_den, 900.0)
        dE = property_by_model_attr(ModelAttrs.ice_dE, 336000.0)
        specific_heat = property_by_model_attr(ModelAttrs.ice_c, 1000.0)
        teq = property_by_model_attr(ModelAttrs.ice_teq, 273.15)

    class HydProperty(Object):
        """
        定义水合物相关的属性
        """

        def __init__(self, model):
            assert isinstance(model, HydModel)
            self.model = model

        den = property_by_model_attr(ModelAttrs.hyd_den, 900.0)
        dE = property_by_model_attr(ModelAttrs.hyd_dE, (62.8e3 / 16.0E-3) * get_mg_vs_mh(6.0))
        specific_heat = property_by_model_attr(ModelAttrs.hyd_c, 1000.0)

        def get_peq(self, T):
            """
            在水合物的相平衡曲线上，给定温度，计算压力
            """
            return self.model.hyd_t2p.get(T)

        def get_teq(self, p):
            """
            在水合物的相平衡曲线上，给定压力，计算温度
            """
            assert False

        def load_sal2dt(self, path):
            """
            导入盐度对水合物相平衡温度的修改曲线。该文件包含两列，第一列为盐度，第二列为平衡温度
            的该变量，即考虑了盐度后的平衡温度减去纯水时候的平衡温度。第一列盐度的定义为盐分
            的质量除以水的质量。
            """
            assert False

        def set_t2p(self, vt, vp):
            """
            设置水合物的温度压力曲线。给定温度(单位K)下的压力（单位Pa）
            """
            assert False

    class GasProperty(Object):
        """
        定义气体相关的属性
        """

        def __init__(self, model):
            assert isinstance(model, HydModel)
            self.model = model

        specific_heat = property_by_model_attr(ModelAttrs.gas_c, 1000.0)
        den_min = property_by_model_attr(ModelAttrs.gas_den_min, 5)
        den_max = property_by_model_attr(ModelAttrs.gas_den_max, 260)

        def get_density(self, p, T):
            den0, den1 = self.den_min, self.den_max
            assert den0 <= den1
            den = self.model.gas_den(max(p, 1.0), T)
            return max(den0, min(den1, den))

        def get_vis(self, p, T):
            return self.model.gas_vis(p, T)

        @property
        def den_range(self):
            """
            在计算过程中所允许的气体密度的范围
            """
            return (self.den_min, self.den_max)

    class WaterProperty(Object):
        """
        定义水的属性
        """

        def __init__(self, model):
            assert isinstance(model, HydModel)
            self.model = model

        specific_heat = property_by_model_attr(ModelAttrs.water_c, 4000.0)
        den = property_by_model_attr(ModelAttrs.water_den, 1000.0)

        def get_vis(self, p, T):
            return self.model.water_vis(p, T)

    # ---------------------------------------------------------------------------------

    def __init__(self):
        super(HydModel, self).__init__()
        self.hyd_t2p = create_t2p_TH()
        self.gas_den = create_ch4_density()
        self.gas_vis = create_ch4_viscosity()
        self.water_vis = create_h2o_viscosity()
        self.sal_curve = Interp1(value=0.0)
        self.attr = Attrs()
        self.fids = FluIds()

    step = property_by_attr(ModelAttrs.step, default_val=0, convert=int)
    time = property_by_attr(ModelAttrs.time, default_val=0)
    dt = property_by_attr(ModelAttrs.dt, default_val=1.0e-8)
    dt_min = property_by_attr(ModelAttrs.dt_min, default_val=1.0e-8)
    dt_max = property_by_attr(ModelAttrs.dt_max, default_val=1.0e5)
    dm_relative = property_by_attr(ModelAttrs.dm_relative, default_val=0.1)
    nloop1 = property_by_attr(ModelAttrs.nloop1, default_val=0, convert=int)
    nloop2 = property_by_attr(ModelAttrs.nloop2, default_val=0, convert=int)
    precision_p = property_by_attr(ModelAttrs.precision_p, default_val=1.0)
    precision_T = property_by_attr(ModelAttrs.precision_T, default_val=0.001)
    nloop_max = property_by_attr(ModelAttrs.nloop_max, default_val=0, convert=int, min=0)
    ratio_max = property_by_attr(ModelAttrs.ratio_max, default_val=0.98)
    pc_max = property_by_attr(ModelAttrs.pc_max, default_val=0, min=0, max=1.0e9)

    @property
    def dtrange(self):
        return self.dt_min, self.dt_max

    @dtrange.setter
    def dtrange(self, value):
        self.dt_min = value[0]
        self.dt_max = value[1]

    def save(self, path):
        """
        将当前的模型数据存入path指定的文件
        """
        fmap = FileMap()
        fmap.set('seepage', self.to_fmap())
        fmap.set('hyd_t2p', self.hyd_t2p.to_fmap())
        fmap.set('gas_den', self.gas_den.to_fmap())
        fmap.set('gas_vis', self.gas_vis.to_fmap())
        fmap.set('water_vis', self.water_vis.to_fmap())
        fmap.set('sal_curve', self.sal_curve.to_fmap())
        fmap.save(path)

    def load(self, path):
        """
        将从path指定的文件读取模型
        """
        fmap = FileMap()
        fmap.load(path)
        assert fmap.has_key('seepage')
        self.from_fmap(fmap.get('seepage'))
        if fmap.has_key('hyd_t2p'):
            self.hyd_t2p.from_fmap(fmap.get('hyd_t2p'))
        else:
            self.hyd_t2p = create_t2p_TH()
        if fmap.has_key('gas_den'):
            self.gas_den.from_fmap(fmap.get('gas_den'))
        else:
            self.gas_den = create_ch4_density()
        if fmap.has_key('gas_vis'):
            self.gas_vis.from_fmap(fmap.get('gas_vis'))
        else:
            self.gas_vis = create_ch4_viscosity()
        if fmap.has_key('water_vis'):
            self.water_vis.from_fmap(fmap.get('water_vis'))
        else:
            self.water_vis = create_h2o_viscosity()
        if fmap.has_key('sal_curve'):
            self.sal_curve.from_fmap(fmap.get('sal_curve'))
        else:
            self.sal_curve = Interp1(value=0.0)

    def add_cell(self, vol=1.0, pos=None, temperature=280.0):
        """
        添加一个cell，并且返回一个Cell对象. 当添加失败时，返回None.
        将对Cell进行必要的初始化
        """
        cell1 = super(HydModel, self).add_cell()
        if cell1 is None:
            return
        cell = HydModel.Cell(self, cell1.index)
        if pos is not None:
            cell.pos = pos
        cell.vol = vol
        cell.porosity = 0.1  # 默认的孔隙度
        cell.set(t_i2w=1.0e-8, t_w2i=1.0e-8, g_heat_1m3=1e5, g_h2g_1m3=1e5, g_g2h_1m3=1e5)
        cell.set_pore(10e6, vol * 0.1, 1000.0e6, vol)  # 设置pore的刚度(大约在10Mpa的时候，体积等于vol*0.1)
        cell.fluid_number = 4
        # 气体的密度是可变的，将在后续改变
        cell.gas.set(mass=0, den=self.gas.den_min, vis=self.gas.get_vis(10e6, temperature), temperature=temperature,
                     specific_heat=self.gas.specific_heat)
        cell.water.set(mass=0, den=self.water.den, vis=self.water.get_vis(10e6, temperature), temperature=temperature,
                       specific_heat=self.water.specific_heat, ms=0, mg=0)
        cell.hyd.set(mass=0, den=self.hyd.den, vis=1e20, temperature=temperature,
                     specific_heat=self.hyd.specific_heat, dE=self.hyd.dE, mg=get_mg_vs_mh(6.0))
        cell.ice.set(mass=0, den=self.ice.den, vis=1e20, temperature=temperature,
                     specific_heat=self.ice.specific_heat, dE=self.ice.dE, teq=self.ice.teq)
        cell.tf = temperature
        cell.tr = temperature
        cell.mcr = cell.vol * 1000.0 * 1000.0
        return cell

    def get_cell(self, i):
        """
        返回模型的第i个cell. 注: i从0开始编号
        """
        if i < self.cell_number:
            return HydModel.Cell(self, i)

    @property
    def cells(self):
        """
        返回cell的迭代器，方便对所有的cell进行遍历
        """
        return Iterators.Cell(self)

    def add_face(self, cell_0, cell_1, area=1.0, length=None):
        """
        对于给定的两个cell，添加一个face来进行连接。两个cell之间，只有添加了face，才能
        够交换流体和热量。
        face添加成功，则返回新添加face对象，否则返回None
        当两个cell之间已经存在了face，则返回这个已存在的face
        """
        assert isinstance(cell_0, HydModel.Cell)
        assert isinstance(cell_1, HydModel.Cell)
        face1 = super(HydModel, self).add_face(cell_0, cell_1)
        if face1 is None:
            return
        face = HydModel.Face(self, face1.index)
        # Now. config
        if length is None:
            face.length = get_distance(cell_0.pos, cell_1.pos)
        else:
            assert length > 1.0e-6
            face.length = length
        assert 1.0e-10 < area < 1.0e10
        face.area = area
        return face

    def get_face(self, i):
        """
        返回模型的第i个face. 注: i从0开始编号
        """
        if i < self.face_number:
            return HydModel.Face(self, i)

    @property
    def faces(self):
        """
        返回face的迭代器
        """
        return Iterators.Face(self)

    @property
    def dt_range(self):
        return self.dtrange

    @dt_range.setter
    def dt_range(self, value):
        self.dtrange = value

    @property
    def summary_of_dts(self):
        """
        Get a string that contains all the recommended dts.  Just for debug.
        """
        return ''

    def load_krf(self, path, ind=0):
        """
        导入流体的相对渗透率曲线。其中path指定的文件应包含两列，第一列为 (vg+vw)/vpore，其中
        vg为气体体积，vw为水的体积，vpore为孔隙空间总体积；第二列为流体的相对渗透率(0到1之间)
        """
        assert False

    def load_krg(self, path, ind=0):
        """
        导入气体的相对渗透率曲线。其中path指定的文件应包含两列，第一列为 vg/(vg+vw)，其中
        vg为气体体积，vw为水的体积；第二列为气体的相对渗透率(0到1之间)
        """
        with open(path, 'r') as file:
            x, y = [], []
            for line in file.readlines():
                vals = [float(s) for s in line.split()]
                if len(vals) > 0:
                    assert len(vals) == 2
                    x.append(vals[0])
                    y.append(vals[1])
            self.set_kr(FluIds.gas, x, y)

    def load_krw(self, path, ind=0):
        """
        导入水的相对渗透率曲线。其中path指定的文件应包含两列，第一列为 vw/(vg+vw)，其中
        vg为气体体积，vw为水的体积；第二列为水的相对渗透率(0到1之间)
        """
        with open(path, 'r') as file:
            x, y = [], []
            for line in file.readlines():
                vals = [float(s) for s in line.split()]
                if len(vals) > 0:
                    assert len(vals) == 2
                    x.append(vals[0])
                    y.append(vals[1])
            self.set_kr(FluIds.water, x, y)

    def print_krf(self, path, ind=0):
        """
        将当前采用的krf曲线输出到文件
        """
        assert False

    def print_krg(self, path, ind=0):
        """
        将当前采用的krg曲线输出到文件
        """
        assert False

    def print_krw(self, path, ind=0):
        """
        将当前采用的krw曲线输出到文件
        """
        assert False

    @property
    def update_flow_linearly(self):
        """
        是否线性地更新流动。默认为True。正常不需要修改
        """
        return True

    @update_flow_linearly.setter
    def update_flow_linearly(self, value):
        pass

    @property
    def update_gas_linearly(self):
        return True

    @update_gas_linearly.setter
    def update_gas_linearly(self, value):
        pass

    @property
    def update_water_linearly(self):
        return True

    @update_water_linearly.setter
    def update_water_linearly(self, value):
        pass

    def set_const_ginw(self, value):
        """
        将气体在水中的溶解度（单位质量的水中溶解的气体的质量）设置为一个固定的值，仅仅用于测试。
        目前版本暂不支持。
        """
        assert False

    def iterate(self):
        """
        向前迭代一步。此函数是模型进行求解的唯一途径。所谓的求解，就是一次次地调用这个函数。
        """
        # 温度交换
        self.exchange_heat(dt=self.dt, ca_g=CellAttrs.g_heat, ca_t=CellAttrs.T, ca_mc=CellAttrs.mc,
                           fa_t=FluAttrs.T, fa_c=FluAttrs.c)

        # 更新水合物
        update_hyd(self, dt=self.dt, ph_curve=self.hyd_t2p, sal_curve=self.sal_curve, fid_g=FluIds.gas,
                   fid_w=FluIds.water,
                   fid_h=FluIds.hyd, ca_h2g=CellAttrs.g_h2g, ca_g2h=CellAttrs.g_g2h,
                   fa_t=FluAttrs.T, fa_c=FluAttrs.c, wa_ms=WaterAttrs.ms, ha_dE=HydAttrs.dE,
                   ha_mg=HydAttrs.mg)

        # 更新冰
        update_ice(self, dt=self.dt, fid_i=FluIds.ice, fid_w=FluIds.water, fa_t=FluAttrs.T, fa_c=FluAttrs.c,
                   ia_dE=IceAttrs.dE, ia_teq=IceAttrs.teq,
                   ca_i2w=CellAttrs.t_i2w, ca_w2i=CellAttrs.t_w2i)

        # 更新气体密度
        gas_density_range = self.gas.den_range
        self.update_den(fluid_id=FluIds.gas, kernel=self.gas_den, relax_factor=0.01,
                        fa_t=FluAttrs.T, min=gas_density_range[0], max=gas_density_range[1])

        # 多相渗流的更新
        r1 = super(HydModel, self).iterate(dt=self.dt, precision=self.precision_p, ca_p=CellAttrs.fp,
                                           nloop_max=self.nloop_max, ratio_max=self.ratio_max)
        self.nloop1 = r1.get('n_loop', 0)
        if self.dm_relative > 0 and self.dm_relative < 1:
            new_dt1 = self.get_recommended_dt(self.dt, dv_relative=self.dm_relative)

        # 利用毛管压力，对流体的分布进行再平衡
        pc_max = self.pc_max
        if 1.0e-3 < pc_max < 1.0e7:
            pass
            # self.balance_saturation(FluIds.gas, FluIds.water, pc_max, self.dt)

        # 热传导过程的更新
        r2 = self.iterate_thermal(ca_t=CellAttrs.T, ca_mc=CellAttrs.mc, fa_g=FaceAttrs.g_heat,
                                  dt=self.dt, precision=self.precision_T, relax_factor=1.0,
                                  nloop_max=self.nloop_max, ratio_max=self.ratio_max)
        self.nloop2 = r2.get('n_loop', 0)
        if self.dm_relative > 0 and self.dm_relative < 1:
            new_dt2 = self.get_recommended_dt(self.dt, dv_relative=self.dm_relative,
                                              ca_t=CellAttrs.T, ca_mc=CellAttrs.mc)

        # 更新流体的粘性系数
        if self.step % 20 == 0:
            self.update_vis(fluid_id=FluIds.gas, kernel=self.gas_vis, ca_p=CellAttrs.fp, fa_t=FluAttrs.T,
                            relax_factor=0.3, min=1.0e-6, max=1.0e-3)
            self.update_vis(fluid_id=FluIds.water, kernel=self.water_vis, ca_p=CellAttrs.fp, fa_t=FluAttrs.T,
                            relax_factor=0.3, min=1.0e-4, max=1.0e-1)

        # 更新状态
        self.time += self.dt
        self.step += 1

        # 更新时间步长
        if self.dm_relative > 0 and self.dm_relative < 1:
            self.dt = min(new_dt1, new_dt2)

        # 修改dt的范围
        self.dt = max(self.dt, self.dtrange[0])
        self.dt = min(self.dt, self.dtrange[1])

    @property
    def flow_iter_n(self):
        """
        在上次iterate时，迭代流动所用的迭代次数
        """
        return 0

    @property
    def gas_iter_n(self):
        """
        不再支持的属性
        """
        return 0

    @property
    def water_iter_n(self):
        """
        不再支持的属性
        """
        return 0

    @property
    def heat_iter_n(self):
        """
        在上次iterate时，迭代热传导所用的迭代次数
        """
        return 0

    @property
    def heat(self):
        """
        返回体系内所有的能量，用于检测能量的守恒性
        """
        return 0

    @property
    def mass(self):
        """
        mg+mw+mh+mi
        """
        return self.mg + self.mw + self.mh + self.mi

    @property
    def mg(self):
        """
        当前模型中所有的气体质量
        """
        value = 0
        for cell in self.cells:
            value += cell.mg
        return value

    @property
    def mw(self):
        """
        当前模型中所有的水质量
        """
        value = 0
        for cell in self.cells:
            value += cell.mw
        return value

    @property
    def mh(self):
        """
        当前模型中所有的hyd质量
        """
        value = 0
        for cell in self.cells:
            value += cell.mh
        return value

    @property
    def mi(self):
        """
        当前模型中所有的ice质量
        """
        value = 0
        for cell in self.cells:
            value += cell.mi
        return value

    @property
    def ms(self):
        """
        当前模型中所有的盐的质量
        """
        value = 0
        for cell in self.cells:
            value += cell.ms
        return value

    @property
    def volume(self):
        """
        网格中所有的cell的总的体积
        """
        vol = 0
        for cell in self.cells:
            vol += cell.vol
        return vol

    @property
    def ice(self):
        """
        返回ice的属性参数
        """
        return HydModel.IceProperty(self)

    @property
    def hyd(self):
        """
        返回hyd的属性参数
        """
        return HydModel.HydProperty(self)

    @property
    def gas(self):
        """
        返回gas的属性参数
        """
        return HydModel.GasProperty(self)

    @property
    def water(self):
        """
        返回water的属性参数
        """
        return HydModel.WaterProperty(self)

    def is_hyd_state(self, p, T):
        """
        判断给定的压力和温度状态下是否允许水合物存在。其中p为压力[Pa]，T为温度[K]
        """
        return p > self.hyd_t2p.get(T)

    def print_cell_property(self, path):
        """
        将cell的属性输出到文件。格式：
             x   y   z   p   sg   sw   sh   si   tf  tr  ms/mw
        """

        def get(cell):
            fp = cell.get_attr(CellAttrs.fp)
            ms = cell.ms / max(cell.mw, 1.0e-20)
            x, y, z = cell.pos
            return f'{fp} {cell.sg} {cell.sw} {cell.sh} {cell.si} {cell.tf} {cell.tr} {ms}'

        self.print_cells(path, get)

    def set_mesh(self, mesh):
        """
        载入一个几何网络。这一步，将同时把cell和face添加到model中。设置cell的位置，孔隙体积
        设置face的面积和长度。
        """
        self.clear()

        for c in mesh.cells:
            cell = self.add_cell(vol=c.vol, pos=c.pos)
            assert cell is not None

        for f in mesh.faces:
            face = self.add_face(self.get_cell(f.link[0]), self.get_cell(f.link[1]), area=f.area, length=f.length)
            assert face is not None

    def set_dencr(self, denc=20000):
        denc = Field(denc)
        for cell in self.cells:
            cell.dencr = denc(cell.x, cell.y, cell.z)

    def set_mcr(self, mc=20000):
        warnings.warn('Use <set_dencr> instead', DeprecationWarning)
        self.set_dencr(mc)

    def set_tf(self, tf=280):
        """
        设置流体的温度分布
        """
        tf = Field(tf)
        for cell in self.cells:
            cell.tf = tf(cell.x, cell.y, cell.z)

    def set_tr(self, tr=280):
        """
        设置固体的温度分布
        """
        tr = Field(tr)
        for cell in self.cells:
            cell.tr = tr(cell.x, cell.y, cell.z)

    def set_porosity(self, porosity):
        porosity = Field(porosity)
        for cell in self.cells:
            x, y, z = cell.pos
            cell.porosity = porosity(x, y, z)

    def fill_pore(self, pre, sg, sw, sh, si):
        """
        根据给定的分布，向所有的cell中填充流体
        """
        pre = Field(pre)
        sg = Field(sg)
        sw = Field(sw)
        sh = Field(sh)
        si = Field(si)
        for cell in self.cells:
            x, y, z = cell.pos
            cell.fill_pore(pre(x, y, z), sg(x, y, z), sw(x, y, z),
                           sh(x, y, z), si(x, y, z))

    def set_cell_g(self, h2g, g2h, heat):
        """
        设置各个cell位置，水合物合成分解，以及流体固体热量交换的速度
        """
        h2g = Field(h2g)
        g2h = Field(g2h)
        heat = Field(heat)
        for cell in self.cells:
            x, y, z = cell.pos
            cell.g_g2h_1m3 = g2h(x, y, z)
            cell.g_h2g_1m3 = h2g(x, y, z)
            cell.g_heat_1m3 = heat(x, y, z)

    def set_perm(self, perm):
        """
        设置各个位置的渗透率
        """
        perm = Field(perm)
        for face in self.faces:
            x, y, z = face.pos
            face.perm = perm(x, y, z)

    def set_heat_cond(self, heat_cond):
        """
        设置各个位置的热传导系数
        """
        heat_cond = Field(heat_cond)
        for face in self.faces:
            x, y, z = face.pos
            face.heat_cond = heat_cond(x, y, z)

    def add_bound(self, temp=None, pre=None, sat=None, dist=None, cells=None, perm=None,
                  heat_cond=None, pos=None, bound_cell=None, vol=None, area=None):
        """
        添加一个定压力/温度的边界。其中pre为边界压力，temp为边界温度，sat为边界的饱和度,vol为虚拟cell的体积。cells为
        该边界条件所涉及的单元。dist为边界距离这些边界cell的距离。perm为边界与cells之间的
        渗透率，heat_cond为边界与cells之间的热传导系数。此函数会添加一个虚拟的cell，其中
        pos为这个虚拟cell的位置。如果已经给定了虚拟的cell(参数bound_cell)，则不再创建新
        的虚拟cell。area为和bond连接的所有face的总的面积，将会将这些面积平均分配到所有的cell上。
        """
        if isinstance(cells, HydModel.Cell):
            cells = (cells,)
        if isinstance(cells, int):
            cells = (self.get_cell(cells),)

        assert len(cells) > 0

        if bound_cell is None:
            if pos is None:
                xr, yr, zr = self.get_pos_range(0), self.get_pos_range(1), self.get_pos_range(2)
                dx, dy, dz = xr[1] - xr[0], yr[1] - yr[0], zr[1] - zr[0]
                pos = (xr[1] + dx * 0.1, yr[1] + dy * 0.1, zr[1] + dz * 0.1)
            assert temp is not None and pre is not None and sat is not None

            vol_average = 0
            dencr = 0
            n = 0
            for cell in cells:
                vol_average += cell.vol
                dencr += cell.dencr
                n += 1
            assert n > 0
            vol_average /= n
            dencr /= n

            if vol is None:
                vol = vol_average * 1e8

            cell = self.add_cell()
            cell.pos = pos
            cell.vol = vol
            cell.dencr = dencr
            cell.tf = temp
            cell.tr = temp
            sg, sw, sh, si = sat
            cell.fill_pore(pre, sg, sw, sh, si)
            cell.pore_relax_factor = 0  # make sure the boundary not change
            cell.density_relax_factor = 0
            cell.g_g2h = 0
            cell.g_h2g = 0
            cell.g_heat = 0
            bound_cell = cell
        else:
            assert temp is None and pre is None and sat is None and vol is None

        vol_sum = 0
        for c in cells:
            vol_sum += c.vol

        assert dist is not None
        assert vol_sum > 0
        if area is None:
            # Warning Here
            area = max(vol_sum / dist, 1.0e-10)

        for c in cells:
            assert isinstance(c, HydModel.Cell)
            face = self.add_face(c, bound_cell)
            if face is not None:
                assert area is not None
                assert dist is not None
                face.length = dist
                # 根据cell的体积来分配face的面积
                assert vol_sum > 1.0e-20
                face.area = area * c.vol / vol_sum

                assert perm is not None or heat_cond is not None
                if perm is None:
                    face.perm = 0
                else:
                    face.perm = perm

                if heat_cond is None:
                    face.heat_cond = 0
                else:
                    face.heat_cond = heat_cond

        return bound_cell

    def solve(self, cell_prod=None, cell_temp=None, tmax=3600,
              gprodmax=None, logstep=1, recstep=100, should_exit=None,
              iter_task=None, logpath='log.txt', recfinal=False, recfolder='node'):
        '''
        求解当前模型。其中cell_prod为用于监测生产的cell。cell_temp为用于监测温度的cell。
        gprodmax是最大的产气速度，如果实际的产气速度大于这个值，那么就对cell_prod附近的
        渗透率进行折减。

        should_exit: 额外的终止条件，此函数无参数，返回是否需要终止;
        iter_task：  每次调用iterate函数后，所额外执行的任务。此函数无需参数；

        recfinal: Record the final step when recfinal is True
        recfolder: The local folder that to print the results (do not print when this is None)
        如果需要进一步控制求解的行为，则请自行重写此函数。
        '''
        if recfolder is not None:
            if os.path.exists(recfolder):
                import shutil
                shutil.rmtree(recfolder)
            os.mkdir(recfolder)
        print_tag()

        mg0 = self.mg
        mw0 = self.mw
        mh0 = self.mh
        mi0 = self.mi

        def get_prod():
            if cell_prod is None:
                return 0, 0
            else:
                return cell_prod.mg, cell_prod.mw

        def get_temp():
            if cell_temp is None:
                return 0
            else:
                return cell_temp.tr

        if os.path.exists('record.log') and recfolder is not None:
            os.remove('record.log')

        def Record():
            print(self.step, self.dt, get_time_str(self.time),
                  get_mass_str(self.mg - mg0), get_mass_str(self.mw - mw0),
                  get_mass_str(self.mh - mh0), get_mass_str(self.mi - mi0))
            if recfolder is not None:
                path = f"{recfolder}\\%08d.txt" % self.step
                self.print_cell_property(path)
                with open('record.log', 'a') as file:
                    file.write('%g %s\n' % (self.time, path))

        Record()
        # 在生产的迭代中，是否通过调整prod_cell附近的渗透率来对生产的速度进行动态调整
        adjust_prod = False

        # 对产气的速度进行了限制，所以，要调整产量
        if gprodmax is not None:
            adjust_prod = True

        if adjust_prod and cell_prod is not None:
            # 在需要进行调整的时候，我们需要找到这些face，并且备份它们的原始的渗透率
            faces_prod = [cell_prod.get_face(i) for i in range(cell_prod.face_number)]
            print(f'N face prod = {len(faces_prod)}')
            # 在后期会实时采用的渗透率
            faces_prod_perm = [face.perm for face in faces_prod]
            print('Initial face perm is: ', faces_prod_perm)

        if should_exit is None:
            def should_exit():
                return False

        prod_ini = get_prod()
        with open(logpath, 'w') as file:
            while self.time < tmax and (not should_exit()):
                prod = get_prod()
                gpr1 = prod[0] - prod_ini[0]
                time1 = self.time

                if adjust_prod and cell_prod is not None:
                    perms_backup = [face.perm for face in faces_prod]
                    for i in range(len(faces_prod)):
                        face = faces_prod[i]
                        face.perm = min(faces_prod_perm[i], perms_backup[i])

                self.iterate()

                if adjust_prod and cell_prod is not None:
                    for i in range(len(faces_prod)):
                        face = faces_prod[i]
                        faces_prod_perm[i] = face.perm
                        face.perm = perms_backup[i]

                dt = self.time - time1
                prod = get_prod()
                gpr2 = prod[0] - prod_ini[0]

                if adjust_prod and cell_prod is not None:
                    assert gprodmax is not None
                    gpr = (gpr2 - gpr1) / dt
                    if gpr > gprodmax:
                        for i in range(len(faces_prod_perm)):
                            faces_prod_perm[i] *= (gprodmax / gpr)
                    else:
                        for i in range(len(faces_prod_perm)):
                            faces_prod_perm[i] *= math.sqrt(gprodmax / max(gpr, 1e-20))

                if iter_task is not None:
                    iter_task()

                if self.step % logstep == 0:
                    file.write('%g  %g  %g  %g \n' % (self.time,
                                                      prod[0] - prod_ini[0],
                                                      prod[1] - prod_ini[1],
                                                      get_temp()))
                if self.step % recstep == 0:
                    file.flush()
                    Record()

            if recfinal:
                # Record the final state
                Record()


def load_hyd_model(path):
    """
    从文件path中读取一个model对象并返回。其中位于path的文件必须是Model.save保存的文件
    """
    assert isinstance(path, str)
    assert os.path.exists(path)
    model = HydModel()
    model.load(path)
    return model


Model = HydModel
Cell = Model.Cell
Face = Model.Face
IceProperty = Model.IceProperty
HydProperty = Model.HydProperty
GasProperty = Model.GasProperty
WaterProperty = Model.WaterProperty
load_model = load_hyd_model

Mesh = SeepageMesh
load_mesh = Mesh.load_mesh
create_cube_mesh = Mesh.create_cube
create_cylinder_mesh = Mesh.create_cylinder


class Config(SeepageTher):
    """
    水合物计算的配置：基于zml的Seepage模块
    """

    class HydProperty(Object):
        """
        定义水合物相关的属性
        """

        def __init__(self):
            self.mg = get_mg_vs_mh(6.0)
            self.dE = (62.8e3 / 16.0E-3) * self.mg
            self.t2p = create_t2p_TH()
            self.sal_curve = Interp1(value=0.0)

    class IceProperty(Object):
        """
        定义冰的属性
        """

        def __init__(self):
            self.dE = 336000.0
            self.teq = 273.15

    def __init__(self):
        super(Config, self).__init__()
        self.igas = self.add_fluid(SeepageTher.FluProperty(den=create_ch4_density(), vis=create_ch4_viscosity(),
                                                           specific_heat=1000.0))
        self.iwat = self.add_fluid(SeepageTher.FluProperty(den=1000.0, vis=create_h2o_viscosity(),
                                                           specific_heat=4000.0))
        self.ihyd = self.add_fluid(SeepageTher.FluProperty(den=900.0, vis=1.0e30, specific_heat=1000.0))
        self.iice = self.add_fluid(SeepageTher.FluProperty(den=900.0, vis=1.0e30, specific_heat=1000.0))
        self.hyd = Config.HydProperty()
        self.ice = Config.IceProperty()

        cell_keymax = max(self.cell_keys.values())
        self.cell_keys.update({'g_h2g': cell_keymax + 1, 'g_g2h': cell_keymax + 2,
                               't_i2w': cell_keymax + 3, 't_w2i': cell_keymax + 4})

        flu_keymax = max(self.flu_keys.values())
        self.flu_keys.update({'dE': flu_keymax + 1,
                              'ms': flu_keymax + 2,  # 仅仅对水有效
                              'mg': flu_keymax + 2,  # 仅仅对hyd有效
                              'teq': flu_keymax + 2  # 仅仅对冰有效
                              })
        from zmlx.kr.create_krf import create_krf
        x, y = create_krf()
        self.krf = Interp1(x=x, y=y)

    def set_cell(self, cell, *args, **kwargs):
        super(Config, self).set_cell(cell, *args, **kwargs)
        cell.set_attr(self.cell_keys['t_i2w'], 1.0e-8).set_attr(self.cell_keys['t_w2i'], 1.0e-8)
        cell.set_attr(self.cell_keys['g_h2g'], 1e6).set_attr(self.cell_keys['g_g2h'], 1e6)
        cell.get_fluid(self.iwat).set_attr(self.flu_keys['ms'], 0)
        cell.get_fluid(self.ihyd).set_attr(self.flu_keys['mg'], self.hyd.mg).set_attr(self.flu_keys['dE'], self.hyd.dE)
        cell.get_fluid(self.iice).set_attr(self.flu_keys['dE'], self.ice.dE).set_attr(self.flu_keys['teq'],
                                                                                      self.ice.teq)

    def iterate(self, model, *args, **kwargs):
        t0 = self.get_time(model)
        r = super(Config, self).iterate(model, *args, **kwargs)
        dt = self.get_time(model) - t0  # 因为在iterate中会修改dt为下一步的建议值，所以不可以直接返回dt
        if dt <= 0:
            return r

        # 更新水合物
        update_hyd(model, dt=dt, ph_curve=self.hyd.t2p, sal_curve=self.hyd.sal_curve, fid_g=self.igas,
                   fid_w=self.iwat,
                   fid_h=self.ihyd,
                   fa_t=self.flu_keys['temperature'], fa_c=self.flu_keys['specific_heat'],
                   ca_h2g=self.cell_keys['g_h2g'], ca_g2h=self.cell_keys['g_g2h'],
                   ha_dE=self.flu_keys['dE'],
                   wa_ms=self.flu_keys['ms'],
                   ha_mg=self.flu_keys['mg'])

        # 更新冰
        update_ice(model, dt=dt, fid_i=self.iice, fid_w=self.iwat, fa_t=self.flu_keys['temperature'],
                   fa_c=self.flu_keys['specific_heat'],
                   ia_dE=self.flu_keys['dE'],
                   ia_teq=self.flu_keys['teq'],
                   ca_i2w=self.cell_keys['t_i2w'], ca_w2i=self.cell_keys['t_w2i'])

        return r


def main():
    print(about())


if __name__ == "__main__":
    main()
