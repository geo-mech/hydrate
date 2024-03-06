"""
用于：
    1、co2封存 (与置换)
    2、ch4水合物生成
    3、水合物开发
by 张召彬
since 2024-02
"""

import os

import numpy as np

from zml import Seepage, create_dict, SeepageMesh, Interp1, is_array, ConjugateGradientSolver
from zml import Tensor3, is_windows
from zmlx.alg.clamp import clamp
from zmlx.alg.interp1 import interp1
from zmlx.alg.join_cols import join_cols
from zmlx.alg.time2str import time2str
from zmlx.config import seepage, hydrate
from zmlx.filesys import path
from zmlx.filesys import print_tag
from zmlx.filesys.make_dirs import make_dirs
from zmlx.filesys.make_fname import make_fname
from zmlx.fluid.nist.ch4 import create as nist_ch4
from zmlx.fluid.nist.co2 import create as nist_co2
from zmlx.fluid.nist.h2o import create as nist_h2o
from zmlx.kr.create_kr import create_kr
from zmlx.kr.create_krf import create_krf
from zmlx.plt.plotxy import plotxy
from zmlx.plt.tricontourf import tricontourf
from zmlx.react import ch4_hydrate, co2_hydrate
from zmlx.react.alpha.salinity import data as salinity_c2t
from zmlx.react import hydrate as hydrate_reaction
from zmlx.ui import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.LinearField import LinearField
from zmlx.utility.PressureController import PressureController
from zmlx.utility.SaveManager import SaveManager
from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor
from zmlx.utility.SeepageNumpy import as_numpy
from zmlx.seepage_mesh.co2 import create_mesh, create_cylinder


def create_fludefs(inh_def=None, ch4_def=None, co2_def=None):
    """
    创建流体的定义.
        0. 气体： ch4, co2
        1. 液体： h2o, inh, ch4_in_liq, co2_in_liq, ca
        2. 固体： ch4_hyd, h2o_ice, co2_hyd, ca_co3
    """
    if inh_def is None:
        inh_def = Seepage.FluDef(den=2165.0, vis=0.001, specific_heat=4030.0, name='inh')
    if ch4_def is None:
        ch4_def = nist_ch4(name='ch4')
    if co2_def is None:
        co2_def = nist_co2(name='co2')

    # !!!
    #   特别需要注意的是，这样虽然名字为Ca，但是，这个Ca粒子是用来和co2反应生成ca_co3的，因此，这里的
    #   ca代表了实际中的CaO。这样，在后续设置质量浓度的时候，需要将Ca的浓度转化成为CaO的浓度，即乘以
    #   系数 (56/44)
    ca = Seepage.FluDef(den=2000.0, vis=0.001, specific_heat=2000.0, name='ca')
    ca_co3 = Seepage.FluDef(den=3000.0, vis=1.0e30, specific_heat=2000.0, name='ca_co3')
    return hydrate.create_fludefs(co2_def=co2_def, ch4_def=ch4_def, inh_def=inh_def, has_ch4_in_liq=True,
                                  has_co2_in_liq=True, other_liq=[ca],
                                  other_sol=[ca_co3], h2o_def=nist_h2o())


def create_ini(z_min, z_max, under_h=None, hyd_h=None, perm=None,
               pore_modulus=None, s_ca=None, sh=None, s_inh=None, porosity=None,
               t_seabed=None, p_seabed=None, grad_t=None):
    """
    创建初始场. 其中：
        z_min, z_max： mesh在z方向的范围
        under_h: 下伏层厚度
        hyd_h: 水合物层厚度
        t_seabed: 海底温度. 注意：假设海底的z为0
        p_seabed：海底压力. 注意：假设海底的z为0
        grad_t: 地温梯度(每下降1m，温度升高的幅度).
        perm：渗透率
        porosity：孔隙度
        s_ca: 钙离子的饱和度 (体积饱和度)
    """

    if under_h is None:
        under_h = 100.0

    if hyd_h is None:
        hyd_h = 60.0

    if t_seabed is None:
        t_seabed = 273.15 + 2.5

    if p_seabed is None:
        p_seabed = 12e6

    if grad_t is None:
        grad_t = 0.04466

    if porosity is None:
        porosity = 0.3

    if s_inh is None:
        s_inh = 0.0

    if sh is None:
        sh = 0.3

    if s_ca is None:
        s_ca = 0.0

    if pore_modulus is None:
        pore_modulus = 200e6

    if perm is None:
        perm = 1.0e-14

    assert z_min < z_max
    assert 20.0 <= under_h <= 200.0
    assert 0.0 <= hyd_h <= 200.0
    assert 273.5 <= t_seabed <= 280.0
    assert 5e6 <= p_seabed <= 40e6
    assert 0.02 <= grad_t <= 0.06
    if isinstance(perm, (float, int)):
        assert 1.0e-17 <= perm <= 1.0e-11
    assert 0.1 <= porosity <= 0.6
    assert 50e6 <= pore_modulus <= 1000e6
    assert 0.0 <= s_inh <= 0.05
    assert 0.0 <= sh <= 0.7

    def get_s(_x, _y, z):
        """
        初始饱和度
        """
        if hyd_h > 1.0e-3 and z_min + under_h <= z <= z_min + under_h + hyd_h:
            sw = 1 - sh
            return {'h2o': sw * (1 - s_inh - s_ca), 'inh': sw * s_inh, 'ca': sw * s_ca, 'ch4_hydrate': sh}
        else:
            return {'h2o': 1 - s_inh - s_ca, 'inh': s_inh, 'ca': s_ca}

    def get_denc(_x, _y, z):
        """
        储层土体的密度乘以比热（在顶部和底部，将它设置为非常大以固定温度）.
            特别地：
                如果在海底面以上有网格，那么在这个区域固定温度不变.
        """
        return 3e6 if z_min + 0.1 < z < min(z_max - 0.1, 0) else 1e20

    def get_fai(_x, _y, z):
        """
        孔隙度（在顶部，将孔隙度设置为非常大，以固定压力）
        """
        if z > z_max - 0.1:  # 顶部固定压力
            return 1.0e7

        if z < z_min + 0.1:  # 底部(假设底部有500m的底水供给)
            return porosity * (500.0 / 2.0)

        else:
            return porosity

    t_ini_ = LinearField(v0=t_seabed, z0=0, dz=-grad_t)

    def t_ini(x, y, z):  # 在海底面以上，采用固定的温度.
        return t_ini_(x, y, z) if z <= 0 else t_seabed

    p_ini = LinearField(v0=p_seabed, z0=0, dz=-0.01e6)
    sample_dist = 1.0

    d_temp = interp1(salinity_c2t[0], salinity_c2t[1], s_inh)  # 由于盐度的存在，平衡温度降低的幅度
    t0 = t_ini(0, 0, z_min + under_h)
    p0 = p_ini(0, 0, z_min + under_h)
    teq = ch4_hydrate.get_t(p0) + d_temp
    peq = ch4_hydrate.get_p(t0 - d_temp)
    print(f'At bottom of hydrate layer: '
          f't = {t0 - 273.15}, p = {p0 / 1e6} MPa, teq = {teq - 273.15}, peq = {peq / 1e6} MPa')

    return {'porosity': get_fai, 'pore_modulus': pore_modulus, 'p': p_ini, 'temperature': t_ini,
            'denc': get_denc, 's': get_s, 'perm': perm, 'heat_cond': 2,
            'sample_dist': sample_dist}


def create_model(mesh=None,
                 under_h=None, hyd_h=None, t_seabed=None, p_seabed=None, grad_t=None, perm=None, porosity=None,
                 kg_inj_day=None, x_inj=None, z_inj=None, p_prod=None, face_area_prod=None, pore_modulus=None,
                 s_inh=None, free_h=None, sh=None, flu_inj=None, s_ini=None, t_ini=None,
                 gr=None,
                 inh_diff=None, co2_diff=None, ch4_diff=None, ca_diff=None,
                 co2_cap=None, ch4_cap=None,
                 inh_def=None, n_co2_sol=None, n_ch4_sol=None, heat_cond=None, s_ca=None,
                 support_ch4_hyd_diss=True, support_ch4_hyd_form=True):
    """
    创建模型. 其中
        width、height分别为计算模型的宽度和高度，单位：米
        dw和dh分别是宽度和高度方向的网格大小，单位：米
        under_h：为下伏层的厚度 [m]
        hyd_h：为甲烷水合物层的厚度 [m]
        t_seabed：为计算模型顶部的温度 [K]
        p_seabed：为计算模型顶部的压力 [Pa]
        grad_t：为深度增加1米温度的增加幅度 [K]
        perm：渗透率 (1、浮点数；2、zml.Tensor3(xx=?, yy=?, zz=?)); 3. float = get(x, y, z);   4. Tensor3 = get(x, y, z);
        porosity：孔隙度. 1. float  2. float = get(x, y, z)
        kg_inj_day：每天注入的co2的质量
        x_inj：注入co2的x坐标位置，一个list
        z_inj：注入co2的点位相对于模型顶面(海底面)的位置。 注意：海底面的z必须为0附近
        p_prod：生产压力
        face_area_prod：用于产气的虚拟face的面积，0表示关闭，1表示打开
        pore_modulus：孔隙刚度
        s_inh：初始盐度
        free_h: 在海底面附近，禁止水合物生成的层的厚度.
        n_co2_sol: co2的溶解度
        n_ch4_sol: ch4的溶解度
        flu_inj：注入的流体的name (参考flu_defines)
    返回创建的计算模型，保证：
        计算模型最后一个cell为用于产气的虚拟的cell；
        最后一个face为用于产气的虚拟的face
        共有N个注入点，注入co2的排量一样
    """

    if mesh is None:
        # 只有没有给定mesh，才创建.
        mesh = create_mesh(width=50.0, height=400.0, dw=2.0, dh=2.0)

    assert isinstance(mesh, SeepageMesh)

    x_min, x_max = mesh.get_pos_range(0)
    z_min, z_max = mesh.get_pos_range(2)

    # 流体饱和度 s = vf / (vf+vs)
    #          s -> k / k0     k0原始渗透率，k是渗透率
    if gr is None:  # 创建默认的gr
        x, y = create_krf(0.2, 3, as_interp=False, k_max=1, s_max=1, count=200)
        gr = Interp1(x=x, y=y)
        print('default gr created. ')
        if gui.exists():
            plotxy(x=x, y=y, caption='gr')
    else:
        assert isinstance(gr, Interp1)  # 此时，使用给定的gr

    caps = hydrate.create_caps(inh_diff=inh_diff, co2_diff=co2_diff, ch4_diff=ch4_diff,
                               co2_cap=co2_cap, ch4_cap=ch4_cap)

    # 钙离子的扩散
    if ca_diff is not None:
        cap = create_dict(fid0='ca', fid1='h2o',
                          get_idx=lambda _x, _y, _z: 0,
                          data=[[[0, 1], [0, ca_diff]], ])
        caps.append(cap)

    ca_co3_react = hydrate_reaction.create(gas='co2_in_liq', liq='ca', hyd='ca_co3', mg=0.44,
                                           vp=[0, 100e6], vt=[1000, 1000],
                                           temp=300, heat=1.0,
                                           dissociation=False, formation=True)
    # 所有的反应
    reactions = hydrate.create_reactions(support_ch4_hyd_diss=support_ch4_hyd_diss,
                                         support_ch4_hyd_form=support_ch4_hyd_form,
                                         has_inh=True,
                                         has_co2=True,
                                         has_ch4_in_liq=True, has_co2_in_liq=True,
                                         others=[ca_co3_react])
    kw = create_dict(gravity=(0, 0, -10),
                     dt_ini=1.0, dt_min=1.0, dt_max=24 * 3600 * 7, dv_relative=0.1,
                     fludefs=create_fludefs(inh_def=inh_def),
                     reactions=reactions,
                     caps=caps,
                     gr=gr,
                     has_solid=True)
    if under_h is None:
        under_h = 100.0
    if hyd_h is None:
        hyd_h = 60.0
    if perm is None:
        perm = 1.0e-14
    if s_inh is None:
        s_inh = 0.0
    ini = create_ini(z_min=z_min, z_max=z_max, under_h=under_h, hyd_h=hyd_h,
                     t_seabed=t_seabed, p_seabed=p_seabed, grad_t=grad_t, perm=perm, porosity=porosity,
                     pore_modulus=pore_modulus,
                     s_inh=s_inh, sh=sh, s_ca=s_ca)
    kw.update(ini)
    if s_ini is not None:
        # 如果指定初始饱和度，则使用自定义的场.
        assert hasattr(s_ini, '__call__')
        kw.update({'s': s_ini})

    if t_ini is not None:  # 如果指定了初始温度，则使用
        kw.update({'temperature': t_ini})

    # 指定热传导系数
    if heat_cond is not None:
        kw.update({'heat_cond': heat_cond})

    # 创建模型
    model = seepage.create(mesh=mesh, **kw)

    # 设置溶解度
    if n_co2_sol is None:
        n_co2_sol = 0.0
    if n_ch4_sol is None:
        n_ch4_sol = 0.0
    ca = seepage.cell_keys(model)
    for cell in model.cells:
        cell.set_attr(ca.n_co2_sol, n_co2_sol)  # co2溶解度
        cell.set_attr(ca.n_ch4_sol, n_ch4_sol)  # ch4溶解度

    # 设置在海底面附近，不能发生水合物的反应(气体进入这个区域)
    ca_rate = model.reg_cell_key('hyd_rate')
    for r in model.reactions:
        r.irate = ca_rate

    if free_h is None:
        free_h = 1.0
    free_h = clamp(free_h, 0.5, 30.0)  # 顶层作为边界，不能有水合物的生成
    for cell in model.cells:
        if cell.z > min(z_max, 0) - free_h:  # 在海底面以上的计算区域，作为缓冲边界，不生成水合物
            cell.set_attr(ca_rate, 0)

    # 设置相渗
    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    i_gas = model.find_fludef('gas')
    i_liq = model.find_fludef('liq')
    assert len(i_gas) == 1 and len(i_liq) == 1
    i_gas = i_gas[0]
    i_liq = i_liq[0]
    model.set_kr(i_gas, vs, kg)
    model.set_kr(i_liq, vs, kw)

    # 添加虚拟cell用于生产
    z_prod = z_min + under_h + hyd_h * 0.5
    pos = (x_min, -1000.0, z_prod)
    if p_prod is None:
        p_prod = 3e6
    virtual_cell = seepage.add_cell(model, pos=pos, porosity=1.0e7, pore_modulus=100e6, vol=1.0,
                                    temperature=ini['temperature'](*pos), p=p_prod,
                                    s={'h2o': 1 - s_inh, 'inh': s_inh})
    cell = model.get_nearest_cell([x_min, 0, z_prod])
    if face_area_prod is None:
        face_area_prod = 1.0
    assert 0.0 <= face_area_prod <= 1.0
    seepage.add_face(model, virtual_cell, cell,
                     heat_cond=0, perm=perm, area=face_area_prod, length=1.0)

    # 添加注入的流体(将流量平分给多个注入点)
    #    注入点最好不要放在左右侧边界（考虑对称性）
    if flu_inj is None:
        flu_inj = 'co2'  # 如果需要ch4， 名字修改为 'ch4'
    if kg_inj_day is None:
        kg_inj_day = 1.0e-30  # 默认几乎等于0
    assert 0 <= kg_inj_day
    if x_inj is None:
        x_inj = [0.0, ]
    else:
        assert is_array(x_inj)
    if z_inj is None:
        z_inj = -100.0
    for x in x_inj:
        pos = [clamp(x, x_min, x_max), 0.0, clamp(z_inj, -1000.0, -5.0)]
        cell = model.get_nearest_cell(pos)
        i_inj = model.find_fludef(flu_inj)
        assert i_inj is not None
        flu = cell.get_fluid(*i_inj).get_copy()
        model.add_injector(cell=cell, fluid_id=i_inj, flu=flu, pos=pos, radi=3,
                           value=kg_inj_day / len(x_inj) / flu.den / (3600 * 24)
                           )

    # 对于h2o，注册一个属性，用以显示注入的时间.
    fa_time = model.reg_flu_key('time')
    i_h2o = model.find_fludef(name='h2o')
    assert i_h2o is not None
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        h2o = cell.get_fluid(*i_h2o)
        assert h2o is not None
        h2o.set_attr(fa_time, 0.0)

    return model


def show(model: Seepage, monitor=None, folder=None):
    """
    在界面上绘图并且(在给定folder的时候)保存图片
    """
    if not gui.exists():
        return

    time = time2str(seepage.get_time(model))
    year = seepage.get_time(model) / (3600 * 24 * 365)

    x = as_numpy(model).cells.x
    z = as_numpy(model).cells.z
    x = x[: -1]
    z = z[: -1]

    def show_ca(idx, name):
        tmp = as_numpy(model).cells.get(idx)
        tmp = tmp[: -1]
        tricontourf(x, z, tmp, caption=name, title=f'time = {time}',
                    fname=make_fname(year, path.join(folder, name), '.jpg', 'y'))
        return tmp

    p = show_ca(-12, 'pressure')
    t = show_ca(model.get_cell_key('temperature'), 'temperature')

    # 显示ch4水合物稳定去
    dt = ch4_hydrate.get_t(p) - t
    dt[dt >= 0] = 200
    tricontourf(x, z, dt, caption='ch4_hyd_zone',
                fname=make_fname(year, path.join(folder, 'ch4_hyd_zone'), '.jpg', 'y'))

    # 显示co2水合物稳定去
    dt = co2_hydrate.get_t(p) - t
    dt[dt >= 0] = 200
    tricontourf(x, z, dt, caption='co2_hyd_zone',
                fname=make_fname(year, path.join(folder, 'co2_hyd_zone'), '.jpg', 'y'))

    fv_all = as_numpy(model).cells.fluid_vol
    fv_all = fv_all[: -1]

    def show_m(name):
        idx = model.find_fludef(name=name)
        assert idx is not None, f'can not find define of fluid: {name}'
        v = as_numpy(model).fluids(*idx).vol
        v = v[: -1]
        tricontourf(x, z, v / fv_all, caption=name, title=f'time = {time}',
                    fname=make_fname(year, path.join(folder, name), '.jpg', 'y'))

    show_m('ch4')
    show_m('ch4_in_liq')
    show_m('co2')
    show_m('co2_in_liq')
    show_m('ch4_hydrate')
    show_m('co2_hydrate')
    show_m('ca')
    show_m('ca_co3')

    # 显示盐度
    v0 = as_numpy(model).fluids(*model.find_fludef(name='inh')).vol
    v1 = as_numpy(model).fluids(*model.find_fludef(name='liq')).vol
    inh = v0 / v1
    inh = inh[: -1]
    tricontourf(x, z, inh, caption='inh', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'inh'), '.jpg', 'y'))

    # 显示流体时间
    ft = as_numpy(model).fluids(*model.find_fludef(name='h2o')).get(model.get_flu_key('time'))
    ft = ft[: -1]
    tricontourf(x, z, ft, caption='h2o_time', title=f'time = {time}',
                fname=make_fname(year, path.join(folder, 'h2o_time'), '.jpg', 'y'))

    # 显示生产曲线
    if monitor is not None:
        monitor.plot_prod(index=0, caption='ch4_prod',
                          fname=make_fname(year, path.join(folder, 'ch4_prod'), '.jpg', 'y'))
        monitor.plot_rate(index=0, caption='ch4_rate',
                          fname=make_fname(year, path.join(folder, 'ch4_rate'), '.jpg', 'y'))


def solve(model, time_forward=3600.0 * 24.0 * 365.0 * 10.0, folder=None, day_save=None, save_prod=None,
          kg_inj_day=None, face_area_prod=None, p_prod=None, dt_max=None, tolerance=None):
    """
    求解给定的模型 model. 且该model需要保证：
        1、最后一个cell是虚拟的，用于生产
        2、包含一个注入点，用于注入co2 (或者其它在create_model的时候指定的流体)

    day_save：数据保存的时间间隔[单位：天];
    time_forward：向前求解的时间长度[单位: 秒]
    dt_max: 一个函数，参数为当前的时间，返回当前时间允许的最大的时间步长，单位是：秒

    注意：
        若指定参数 kg_inj_day，则首先修改流体的注入速率，之后再计算.
        若指定face_area_prod，则首先修改用于产气的face的面积，之后再计算（用以开关）；这个面积应该设置为0或者1;
        p_prod：如果给定，则首先修改产气的压力;
    """
    assert isinstance(model, Seepage)
    if folder is not None:
        make_dirs(folder)
        print_tag(folder)
        print(f'Solve. folder = {folder}')
        if gui.exists():
            gui.title(f'Data folder = {folder}')

    if kg_inj_day is not None:  # 更改co2注入的排量
        assert model.injector_number > 0
        for inj in model.injectors:
            inj.value = kg_inj_day / model.injector_number / inj.flu.den / (3600 * 24)

    if face_area_prod is not None:
        virtual_face = model.get_face(model.face_number - 1)
        seepage.set_face(virtual_face, area=face_area_prod)

    # 最后一个cell为虚拟的，用以存储产出的流体
    virtual_cell = model.get_cell(model.cell_number - 1)
    if p_prod is None:
        p_prod = virtual_cell.pre

    # 压力控制，从而保证内部流体压力保持不变
    p_ctrl = PressureController(cell=virtual_cell, t=[-1e20, 1e20], p=[p_prod, p_prod], modify_pore=True)

    # 产量监控
    monitor = SeepageCellMonitor(get_t=lambda: seepage.get_time(model), cell=virtual_cell)

    # 执行迭代（不让gui绘图占用太多cpu）
    iterate = GuiIterator(seepage.iterate,
                          lambda: show(model, folder=path.join(folder, 'figures'), monitor=monitor))

    # 线性求解器.
    if tolerance is None:
        tolerance = 1.0e-25
    solver = ConjugateGradientSolver(tolerance=tolerance)

    if day_save is None:
        day_save = 30.0

    if save_prod is None:
        save_prod = True

    # 自动保存模型(day_save可以是一个数，也可以是一个函数 interval = get(time) )
    save_model = SaveManager(folder=path.join(folder, 'models'),
                             dtime=day_save, get_time=lambda: seepage.get_time(model) / (24 * 3600),
                             save=model.save, ext='.seepage', time_unit='d', always_save=False)

    fa_time = model.reg_flu_key('time')
    i_h2o = model.find_fludef(name='h2o')

    # 自动保存cells（用于绘图）
    save_cells = SaveManager(folder=path.join(folder, 'cells'),
                             dtime=day_save, get_time=lambda: seepage.get_time(model) / (24 * 3600),
                             save=lambda name: seepage.print_cells(name, model,
                                                                   fa_keys=[[i_h2o, fa_time]], export_mass=True),
                             ext='.txt', time_unit='d', always_save=False)

    # 最终停止时的时间.
    time_max = time_forward + seepage.get_time(model)

    z_min, z_max = model.get_pos_range(2)
    top_cells = []
    for cell in model.cells:
        if cell.z > min(z_max - 0.1, 0) or abs(z_min - cell.z) < 0.1:  # 将海底面以上的计算区域设置为边界.
            top_cells.append(cell)
    print(f'Count of top cell: {len(top_cells)}')

    def mark_h2o_time():
        t = seepage.get_time(model) / (24 * 3600 * 365)
        for c in top_cells:
            c.get_fluid(*i_h2o).set_attr(fa_time, t)

    while seepage.get_time(model) < time_max:
        iterate(model, solver=solver)
        p_ctrl.update(t=seepage.get_time(model))  # 维持压力
        monitor.update(dt=3600.0 * 24)

        # 调整最大允许时间步长
        if dt_max is not None:
            if hasattr(dt_max, '__call__'):
                seepage.set_dt_max(model, max(24 * 3600, dt_max(seepage.get_time(model))))
            else:
                seepage.set_dt_max(model, max(24 * 3600, dt_max))

        save_model()
        save_cells()
        step = seepage.get_step(model)
        if step % 10 == 0:
            time = time2str(seepage.get_time(model))
            dt = time2str(seepage.get_dt(model))
            print(f'step = {step}, dt = {dt}, time = {time}')
        if step % 100 == 0:
            mark_h2o_time()
            if folder is not None and save_prod:
                monitor.save(path.join(folder, 'prod.txt'))

    # 保存最后一帧
    save_model(check_dt=False)
    save_cells(check_dt=False)

    if folder is not None:  # 保存最终时刻
        if save_prod:
            monitor.save(path.join(folder, 'prod.txt'))  # 覆盖的原有的曲线

    # 计算之后，再返回model (后续可能用到)
    return model


def cooling(model, folder=None, time_forward=None, dt_max=None, day_save=None, tolerance=None):
    """
    冷却过程:
        对于开发计算之后的模型，再计算更长的时间，来观察储层内的长期状态.
        默认冷却10万年；
    """
    if dt_max is None:
        def dt_max(time):
            """
            在不同的时间，所允许的最大的时间步长
            """
            return max(30 * 24 * 3600, time / 1000.0)

    if day_save is None:
        def day_save(day):
            """
            在不同的时刻，采用不同的保存间隔.
            """
            return max(365, day / 15.0)

    if time_forward is None:
        time_forward = 3600.0 * 24.0 * 365.0 * 100000.0

    return solve(model=model, time_forward=time_forward, folder=folder,
                 kg_inj_day=0, face_area_prod=0, save_prod=False,
                 day_save=day_save,
                 dt_max=dt_max, tolerance=tolerance)


def export_co2(folder):
    """
    遍历计算结果文件夹的models文件夹，获得model中co2_hydrate的质量、co2气体质量、逃逸的co2质量随着时间的变化数据，
    并保存到co2.txt中
    """
    assert path.isdir(folder)

    models_folder = path.join(folder, 'models')
    assert path.isdir(models_folder)

    a = []  # time
    b = []  # hydrate
    c = []  # co2
    d = []  # co2 escaped
    e = []  # co2 in h2o
    f = []  # co2 in ca_co3

    names = os.listdir(models_folder)
    names.sort()

    for index in range(len(names)):
        gui.break_point()
        name = names[index]

        days = float(name[0: len('00000000000000_00001')].replace('_', '.'))
        a.append(days * 24 * 3600)  # 时间

        model = Seepage(path=path.join(models_folder, name))

        idx = model.find_fludef('co2_hydrate')
        assert idx is not None
        mass = np.sum(as_numpy(model).fluids(*idx).mass[: -1])
        b.append(mass)  # co2 水合物

        z = as_numpy(model).cells.z
        z_max = np.max(z)

        idx = model.find_fludef('co2')
        assert idx is not None
        m = as_numpy(model).fluids(*idx).mass

        # 所有的自由的co2
        m1 = np.sum(m)
        # 被视为逃逸的co2
        m2 = np.sum(m[z > min(z_max - 0.1, 0)]) + m[-1]

        c.append(m1 - m2)  # 计算区域的co2
        d.append(m2)  # 逃逸的co2

        # 溶解的co2
        idx = model.find_fludef('co2_in_liq')
        assert idx is not None
        m = as_numpy(model).fluids(*idx).mass

        # 所有的co2
        m1 = np.sum(m)
        # 被视为逃逸的
        m2 = np.sum(m[z > min(z_max - 0.1, 0)]) + m[-1]

        e.append(m1 - m2)  # 计算区域的co2

        # 逃逸的溶解的co2也加入到d
        d[-1] += m2

        # 碳酸钙
        idx = model.find_fludef('ca_co3')
        assert idx is not None
        m = as_numpy(model).fluids(*idx).mass
        f.append(np.sum(m))

        print(f"{index}/{len(names)}: '{name}' Processed!")

    np.savetxt(path.join(folder, 'co2.txt'), join_cols(a, b, c, d, e, f))


def gas_seq(folder=None, pool_d=100, pool_h=80, inj_depth=200.0, s_inh=None, mesh=None,
            p_seabed=10e6, t_seabed=2.5 + 273.15,
            gas_ty=None,
            inh_diff=1.0e6 / 400, co2_diff=None, ch4_diff=None,
            gui_mode=is_windows, close_after_done=True, perm=None, gas_temp_w=0.3,
            s_ca=None, ca_cap=1.0e6 / 400,
            ):
    """
    执行co2/ch4水合物封存计算模型 (建模和求解)。 since 2024-2-7
    """
    if mesh is None:
        mesh = create_cylinder(radius=300.0, depth=400.0, height=100,
                               dr=1, dh=1, rc=100, hc=150, ratio=1.05, dr_max=10, dh_max=10)
        print(f'mesh = {mesh}')

    if s_inh is None:
        s_inh = 0.0315 / 2.165  # 将质量浓度(0.0315)转化为体积浓度

    if s_ca is None:
        s_ca = 0.0

    def get_radi(x, _y, z):
        if pool_d <= 0 or pool_h <= 0:
            return 1e100
        else:
            return np.linalg.norm([x / (pool_d * 0.5), (z + inj_depth) / (pool_h * 0.5)])

    def pool_region(x, y, z):
        return get_radi(x, y, z) < 1

    if gas_ty is None:
        gas_ty = 'co2'

    def get_s(x, y, z):
        r = get_radi(x, y, z)
        if r < 1:
            # 让gas的饱和度在中心最高. follow 张东晓
            s_gas = 0.75 + (0.4 - 0.75) * r
            s_liq = 1 - s_gas
            return {gas_ty: s_gas, 'h2o': s_liq * (1 - s_inh - s_ca) * 0.94,
                    gas_ty + '_in_liq': s_liq * 0.06,
                    'inh': s_liq * s_inh * 0.94, 'ca': s_liq * s_ca * 0.94}
        else:
            return {'h2o': 1 - s_inh - s_ca, 'inh': s_inh, 'ca': s_ca}

    grad_t = 0.04466

    t_ini_ = LinearField(v0=t_seabed, z0=0, dz=-grad_t)

    def t_ini(x, y, z):  # 在海底面以上，采用固定的温度.
        return t_ini_(x, y, z) if z <= 0 else t_seabed

    # 气体温度的权重
    gas_temp_w = clamp(gas_temp_w, 0, 1)

    def get_t(x, y, z):
        if pool_region(x, y, z):
            return 288.0 * gas_temp_w + t_ini(x, y, z) * (1 - gas_temp_w)
        else:
            return t_ini(x, y, z)

    if perm is None:
        perm = Tensor3(xx=5.0e-14, yy=5.0e-14, zz=1.0e-14)

    # 创建模型.
    model = create_model(mesh=mesh, x_inj=[0], z_inj=-800.0, under_h=30.0, hyd_h=0,
                         kg_inj_day=0, face_area_prod=0.0,
                         perm=perm,  # 初始渗透率.
                         free_h=0.0, s_ini=get_s, t_seabed=t_seabed, grad_t=grad_t, t_ini=get_t,
                         p_seabed=p_seabed,
                         inh_diff=inh_diff, co2_diff=co2_diff, ch4_diff=ch4_diff, s_ca=s_ca, ca_diff=ca_cap,
                         n_co2_sol=0.06)

    def dt_max(time):
        """
        在不同的时间，所允许的最大的时间步长
        """
        return max(30 * 24 * 3600, time / 1000.0)

    def day_save(day):
        """
        在不同的时刻，采用不同的保存间隔.
        """
        return max(365, day / 25)

    def func():
        cooling(model=model, folder=folder,
                time_forward=3600.0 * 24.0 * 365.0 * 100000.0,
                dt_max=dt_max, day_save=day_save)
        if gas_ty == 'co2':
            export_co2(folder=folder)

    # 执行
    gui.execute(func, close_after_done=close_after_done,
                disable_gui=not gui_mode)


class Co2Disp:
    """
    纵向二维模型，计算:
        注入co2+冷却
        注入co2+生产+冷却
        生产+注入co2+冷却
    """
    @staticmethod
    def create_model(support_ch4_hyd_form=True, sh=0.3, p_seabed=13e6):
        """
        创建用于co2置换开采的计算模型.
        """
        return create_model(x_inj=[25.0, ], z_inj=-120.0,
                            mesh=create_mesh(width=50.0, height=400.0, dw=1.0, dh=1.0),
                            kg_inj_day=0.0, face_area_prod=1.0,
                            s_inh=0.0315 / 2.165,
                            s_ca=400e-6*(56/44)*0.5,  # 400ppm
                            support_ch4_hyd_form=support_ch4_hyd_form,
                            sh=sh, p_seabed=p_seabed,
                            n_co2_sol=0.06,
                            )

    @staticmethod
    def prod(folder=None, model=None):
        """
        生产10年
        """
        if model is None:
            model = Co2Disp.create_model()
        solve(model=model, time_forward=24 * 3600 * 365 * 10,
              folder=folder,
              day_save=30.0, dt_max=24 * 3600 * 30, face_area_prod=1.0, kg_inj_day=0.0, save_prod=True)
        return model

    @staticmethod
    def inj(folder=None, kg_inj_day=None, model=None):
        """
        注入10年co2
        """
        if model is None:
            model = Co2Disp.create_model()
        if kg_inj_day is None:
            kg_inj_day = 50.0
        solve(model=model, time_forward=24 * 3600 * 365 * 10,
              folder=folder,
              day_save=60.0,
              dt_max=24 * 3600 * 30, kg_inj_day=kg_inj_day, face_area_prod=0.0, save_prod=False)
        return model

    @staticmethod
    def inj_cooling(folder=None, kg_inj_day=None, model=None):
        """
        注入10年co2，再冷却1000年；
        """
        if model is None:
            model = Co2Disp.create_model()
        Co2Disp.inj(folder=folder, kg_inj_day=kg_inj_day, model=model)
        cooling(model=model, folder=folder)
        export_co2(folder=folder)
        return model

    @staticmethod
    def prod_inj_cooling(folder=None, kg_inj_day=None, model=None):
        """
        先开发10年，再注入10年co2，再冷却1000年
        """
        if model is None:
            model = Co2Disp.create_model()
        Co2Disp.prod(folder=folder, model=model)
        Co2Disp.inj(folder=folder, kg_inj_day=kg_inj_day, model=model)
        cooling(model=model, folder=folder)
        export_co2(folder=folder)
        return model

    @staticmethod
    def inj_prod_cooling(folder=None, kg_inj_day=None, model=None):
        """
        先注入10年co2，再开发10年，再冷却1000年
        """
        if model is None:
            model = Co2Disp.create_model()
        Co2Disp.inj(folder=folder, kg_inj_day=kg_inj_day, model=model)
        Co2Disp.prod(folder=folder, model=model)
        cooling(model=model, folder=folder)
        export_co2(folder=folder)
        return model
