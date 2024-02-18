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
from zmlx.config import seepage
from zmlx.filesys import path
from zmlx.filesys import print_tag
from zmlx.filesys.make_dirs import make_dirs
from zmlx.filesys.make_fname import make_fname
from zmlx.filesys.opath import opath
from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
from zmlx.fluid.h2o_ice import create as create_h2o_ice
from zmlx.fluid.nist.ch4 import create as nist_ch4
from zmlx.fluid.nist.co2 import create as nist_co2
from zmlx.fluid.nist.h2o import create as nist_h2o
from zmlx.kr.create_kr import create_kr
from zmlx.kr.create_krf import create_krf
from zmlx.plt.tricontourf import tricontourf
from zmlx.plt.plotxy import plotxy
from zmlx.react import ch4_hydrate, co2_hydrate, h2o_ice as icing_react, dissolution
from zmlx.react.alpha.salinity import data as salinity_c2t
from zmlx.ui import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.LinearField import LinearField
from zmlx.utility.PressureController import PressureController
from zmlx.utility.SaveManager import SaveManager
from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor
from zmlx.utility.SeepageNumpy import as_numpy


def create_fludefs(inh_def=None, ch4_def=None, co2_def=None):
    """
    创建流体的定义
    """
    if inh_def is None:
        inh_def = Seepage.FluDef(den=2165.0, vis=0.001, specific_heat=4030.0, name='inh')
    if ch4_def is None:
        ch4_def = nist_ch4(name='ch4')
    if co2_def is None:
        co2_def = nist_co2(name='co2')

    gas = Seepage.FluDef(name='gas')
    gas.add_component(ch4_def, name='ch4')
    gas.add_component(co2_def, name='co2')

    liq = Seepage.FluDef(name='liq')
    liq.add_component(nist_h2o(), name='h2o')
    liq.add_component(inh_def, name='inh')
    liq.add_component(ch4_def, name='ch4_in_h2o')
    liq.add_component(co2_def, name='co2_in_h2o')

    sol = Seepage.FluDef(name='sol')
    sol.add_component(create_ch4_hydrate(), name='ch4_hyd')
    sol.add_component(create_h2o_ice(), name='h2o_ice')
    sol.add_component(create_co2_hydrate(), name='co2_hyd')  # 之前为919.7，现在默认为1112.0

    return [gas, liq, sol]


def create_reactions():
    """
    创建组分之间的反应
    """
    result = []
    # 添加甲烷水合物的相变
    r = ch4_hydrate.create(gas='ch4', wat='h2o', hyd='ch4_hyd',
                           dissociation=True, formation=True)
    # 抑制固体比例过高，增强计算稳定性 （非常必要）
    r['inhibitors'].append(create_dict(sol='sol', liq=None, c=[0, 0.8, 1.0], t=[0, 0, -200.0]))
    r['inhibitors'].append(create_dict(sol='inh',
                                       liq='liq',
                                       c=salinity_c2t[0],
                                       t=salinity_c2t[1]))
    result.append(r)

    # 添加水和冰之间的相变
    result.append(icing_react.create(flu='h2o', sol='h2o_ice'))

    # 添加co2和co2水合物之间的相变
    r = co2_hydrate.create(gas='co2', wat='h2o', hyd='co2_hyd')
    # 抑制固体比例过高，增强计算稳定性 （非常必要）
    r['inhibitors'].append(create_dict(sol='sol', liq=None, c=[0, 0.8, 1.0], t=[0, 0, -200.0]))
    r['inhibitors'].append(create_dict(sol='inh',
                                       liq='liq',
                                       c=salinity_c2t[0],
                                       t=salinity_c2t[1]))
    result.append(r)

    # 溶解气
    result.append(dissolution.create(gas='ch4', gas_in_liq='ch4_in_h2o',
                                     liq='liq', ca_sol='ch4_sol'))
    result.append(dissolution.create(gas='co2', gas_in_liq='co2_in_h2o',
                                     liq='liq', ca_sol='co2_sol'))

    return result


def create_caps(inh_diff=None, co2_diff=None, ch4_diff=None, co2_cap=None, ch4_cap=None):
    """
    创建扩散过程. 其中inh_diff代表一种驱动力
    """
    result = []

    # 盐度的扩散
    if inh_diff is not None:
        # inh_diff = 1.0e6 / 400  # 大约10000年扩散100米左右
        assert inh_diff >= 0
        cap = create_dict(fid0='inh', fid1='h2o',
                          get_idx=lambda x, y, z: 0,
                          data=[[[0, 1], [0, inh_diff]], ])
        result.append(cap)

    # 溶解co2的扩散
    if co2_diff is not None:
        # co2_diff = 1.0e2
        assert co2_diff >= 0
        cap = create_dict(fid0='co2_in_h2o', fid1='h2o',
                          get_idx=lambda x, y, z: 0,
                          data=[[[0, 1], [0, co2_diff]], ])
        result.append(cap)

    # 溶解ch4的扩散
    if ch4_diff is not None:
        # ch4_diff = 1.0e2
        assert ch4_diff >= 0
        cap = create_dict(fid0='ch4_in_h2o', fid1='h2o',
                          get_idx=lambda x, y, z: 0,
                          data=[[[0, 1], [0, ch4_diff]], ])
        result.append(cap)

    # 自由co2的扩散（毛管压力驱动下）
    if co2_cap is not None:
        # co2_cap = 1.0e3
        assert co2_cap >= 0
        cap = create_dict(fid0='co2', fid1='liq',
                          get_idx=lambda x, y, z: 0,
                          data=[[[0, 1], [0, co2_cap]], ])
        result.append(cap)

    # 自由ch4的扩散（毛管压力驱动下）
    if ch4_cap is not None:
        # ch4_cap = 1.0e3
        assert ch4_cap >= 0
        cap = create_dict(fid0='ch4', fid1='liq',
                          get_idx=lambda x, y, z: 0,
                          data=[[[0, 1], [0, ch4_cap]], ])
        result.append(cap)

    # 返回结果.
    return result


def create_mesh(width, height, dw, dh):
    """
    创建网格. 模型高度height，宽度width.
    """
    assert 15.0 <= width <= 500.0 and 100.0 <= height <= 500.0
    assert 0.5 <= dw <= 5.0
    assert 0.5 <= dh <= 5.0
    jx = round(width / dw)
    jz = round(height / dh)
    x = np.linspace(0, width, jx)
    y = [-0.5, 0.5]
    z = np.linspace(-height, 0, jz)
    return SeepageMesh.create_cube(x, y, z)


def create_cylinder(radius=300.0, height=400.0, dr=1.0, dh=1.0, rc=0, hc=0, ratio=1.02,
                    dr_max=None, dh_max=None):
    """
    创建柱坐标网格.  (主要用于co2封存模拟). 其中：
        radius: 圆柱体的半径
        height: 圆柱体的高度
        dr: 在半径方向上的(初始的)网格的大小
        dh: 在高度方向上的(初始的)网格的大小
        rc: 临界的半径(在这个范围内一直采用细网格)
        hc: 临界的高度(在这个范围内一直采用细网格)
        ratio: 在临界高度和半径之外，网格逐渐增大的比率.
    2024-02
    """
    vr = [0]
    while vr[-1] < radius:
        vr.append(vr[-1] + dr)
        if vr[-1] > rc:
            dr *= ratio
            if dr_max is not None:
                assert dr_max > 0
                dr = min(dr, dr_max)

    vx = [0]
    while vx[-1] < height:
        vx.append(vx[-1] + dh)
        if vx[-1] > hc:
            dh *= ratio
            if dh_max is not None:
                assert dh_max > 0
                dh = min(dh, dh_max)

    mesh = SeepageMesh.create_cylinder(x=vx, r=vr)

    for cell in mesh.cells:
        assert isinstance(cell, SeepageMesh.Cell)
        x, y, z = cell.pos
        cell.pos = [y, z, -x]

    return mesh


def create_ini(z_min, z_max, under_h, hyd_h, t_top, p_top, grad_t, perm,
               porosity, pore_modulus, salinity, sh):
    """
    创建初始场. 其中：
        z_min, z_max： mesh在z方向的范围
        under_h: 下伏层厚度
        hyd_h: 水合物层厚度
        t_top: 模型顶部温度(海底温度)
        p_top： 模型顶部压力(海底压力)
        grad_t: 地温梯度(每下降1m，温度升高的幅度).
        perm：渗透率
        porosity：孔隙度
    """
    assert z_min < z_max
    assert 20.0 <= under_h <= 200.0
    assert 0.0 <= hyd_h <= 200.0
    assert 273.5 <= t_top <= 280.0
    assert 5e6 <= p_top <= 20e6
    assert 0.02 <= grad_t <= 0.06
    if isinstance(perm, (float, int)):
        assert 1.0e-17 <= perm <= 1.0e-11
    assert 0.1 <= porosity <= 0.6
    assert 50e6 <= pore_modulus <= 1000e6
    assert 0.0 <= salinity <= 0.05
    assert 0.0 <= sh <= 0.7

    def get_s(x, y, z):
        """
        初始饱和度
        """
        if hyd_h > 1.0e-3 and z_min + under_h <= z <= z_min + under_h + hyd_h:
            sw = 1 - sh
            return (0, 0), (sw * (1 - salinity), sw * salinity, 0, 0), (sh, 0, 0)
        else:
            return (0, 0), (1 * (1 - salinity), 1 * salinity, 0, 0), (0, 0, 0)

    def get_denc(x, y, z):
        """
        储层土体的密度乘以比热（在顶部和底部，将它设置为非常大以固定温度）
        """
        return 3e6 if z_min + 0.1 < z < z_max - 0.1 else 1e20

    def get_fai(x, y, z):
        """
        孔隙度（在顶部，将孔隙度设置为非常大，以固定压力）
        """
        if z > z_max - 0.1:  # 顶部固定压力
            return 1.0e7

        if z < z_min + 0.1:  # 底部(假设底部有500m的底水供给)
            return porosity * (500.0 / 2.0)

        else:
            return porosity

    t_ini = LinearField(v0=t_top, z0=z_max, dz=-grad_t)
    p_ini = LinearField(v0=p_top, z0=z_max, dz=-0.01e6)
    sample_dist = 1.0

    d_temp = interp1(salinity_c2t[0], salinity_c2t[1], salinity)  # 由于盐度的存在，平衡温度降低的幅度
    t0 = t_ini(0, 0, z_min + under_h)
    p0 = p_ini(0, 0, z_min + under_h)
    teq = ch4_hydrate.get_t(p0) + d_temp
    peq = ch4_hydrate.get_p(t0 - d_temp)
    print(f'At bottom of hydrate layer: '
          f't = {t0 - 273.15}, p = {p0 / 1e6} MPa, teq = {teq - 273.15}, peq = {peq / 1e6} MPa')

    return {'porosity': get_fai, 'pore_modulus': pore_modulus, 'p': p_ini, 'temperature': t_ini,
            'denc': get_denc, 's': get_s, 'perm': perm, 'heat_cond': 2,
            'sample_dist': sample_dist}


def create_model(width=50.0, height=400.0, dw=2.0, dh=2.0,
                 under_h=100.0, hyd_h=60.0, t_top=276.0826483615683, p_top=12e6, grad_t=0.04466,
                 perm=None, porosity=0.3,
                 kg_inj_day=30.0, x_inj=None, z_inj=-100.0, p_prod=3e6, face_area_prod=1.0, pore_modulus=200e6,
                 salinity=0.0, free_h=1.0, sh=0.6, mesh=None, flu_inj=None, s_ini=None, t_ini=None,
                 gr=None,
                 inh_diff=None, co2_diff=None, ch4_diff=None, co2_cap=None, ch4_cap=None,
                 inh_def=None, co2_sol=0.06, heat_cond=None):
    """
    创建模型. 其中
        width、height分别为计算模型的宽度和高度，单位：米
        dw和dh分别是宽度和高度方向的网格大小，单位：米
        under_h：为下伏层的厚度 [m]
        hyd_h：为甲烷水合物层的厚度 [m]
        t_top：为计算模型顶部的温度 [K]
        p_top：为计算模型顶部的压力 [Pa]
        grad_t：为深度增加1米温度的增加幅度 [K]
        perm：渗透率 (1、浮点数；2、zml.Tensor3(xx=?, yy=?, zz=?)); 3. float = get(x, y, z);   4. Tensor3 = get(x, y, z);
        porosity：孔隙度. 1. float  2. float = get(x, y, z)
        kg_inj_day：每天注入的co2的质量
        x_inj：注入co2的x坐标位置，一个list
        z_inj：注入co2的点位相对于模型顶面的位置
        p_prod：生产压力
        face_area_prod：用于产气的虚拟face的面积，0表示关闭，1表示打开
        pore_modulus：孔隙刚度
        salinity：初始盐度
        free_h: 在海底面附近，禁止水合物生成的层的厚度.
        co2_sol: co2的溶解度
    返回创建的计算模型，保证：
        计算模型最后一个cell为用于产气的虚拟的cell；
        最后一个face为用于产气的虚拟的face
        共有N个注入点，注入co2的排量一样
    """
    if perm is None:
        perm = 1.0e-14

    if mesh is None:
        # 只有没有给定mesh，才创建.
        mesh = create_mesh(width=width, height=height, dw=dw, dh=dh)

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

    caps = create_caps(inh_diff=inh_diff, co2_diff=co2_diff, ch4_diff=ch4_diff,
                       co2_cap=co2_cap, ch4_cap=ch4_cap)

    kw = create_dict(gravity=(0, 0, -10),
                     dt_ini=1.0, dt_min=1.0, dt_max=24 * 3600 * 7, dv_relative=0.1,
                     fludefs=create_fludefs(inh_def=inh_def),
                     reactions=create_reactions(),
                     caps=caps,
                     gr=gr,
                     has_solid=True)
    ini = create_ini(z_min=z_min, z_max=z_max, under_h=under_h, hyd_h=hyd_h,
                     t_top=t_top, p_top=p_top, grad_t=grad_t, perm=perm, porosity=porosity,
                     pore_modulus=pore_modulus,
                     salinity=salinity, sh=sh)
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
    ca = seepage.cell_keys(model)
    for cell in model.cells:
        cell.set_attr(ca.co2_sol, co2_sol)  # co2溶解度

    # 设置在海底面附近，不能发生水合物的反应(气体进入这个区域)
    ca_rate = model.reg_cell_key('hyd_rate')
    for r in model.reactions:
        r.irate = ca_rate

    free_h = clamp(free_h, 0.5, 30.0)  # 顶层作为边界，不能有水合物的生成
    for cell in model.cells:
        if cell.z > z_max - free_h:
            cell.set_attr(ca_rate, 0)

    # 设置相渗
    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    igas = model.find_fludef('gas')
    iliq = model.find_fludef('liq')
    assert len(igas) == 1 and len(iliq) == 1
    igas = igas[0]
    iliq = iliq[0]
    model.set_kr(igas, vs, kg)
    model.set_kr(iliq, vs, kw)

    # 添加虚拟cell用于生产
    z_prod = z_min + under_h + hyd_h * 0.5
    pos = (x_min, -1000.0, z_prod)
    virtual_cell = seepage.add_cell(model, pos=pos, porosity=1.0e7, pore_modulus=100e6, vol=1.0,
                                    temperature=ini['temperature'](*pos), p=p_prod,
                                    s=((0, 0), (1 * (1 - salinity), 1 * salinity), (0, 0, 0)))
    cell = model.get_nearest_cell([x_min, 0, z_prod])
    assert 0.0 <= face_area_prod <= 1.0
    seepage.add_face(model, virtual_cell, cell,
                     heat_cond=0, perm=perm, area=face_area_prod, length=1.0)

    # 添加注入的流体(将流量平分给多个注入点)
    #    注入点最好不要放在左右侧边界（考虑对称性）
    if flu_inj is None:
        flu_inj = 'co2'  # 如果需要ch4， 名字修改为 'ch4'
    assert 0 <= kg_inj_day
    if x_inj is None:
        x_inj = [0.0, ]
    else:
        assert is_array(x_inj)
    for x in x_inj:
        pos = [clamp(x, x_min, x_max), 0.0, z_max + clamp(z_inj, -1000.0, -5.0)]
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
        p = as_numpy(model).cells.get(idx)
        p = p[: -1]
        tricontourf(x, z, p, caption=name, title=f'time = {time}',
                    fname=make_fname(year, path.join(folder, name), '.jpg', 'y'))
        return p

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
    show_m('ch4_in_h2o')
    show_m('co2')
    show_m('co2_in_h2o')
    show_m('ch4_hyd')
    show_m('co2_hyd')

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


def solve(model, time_forward=3600.0 * 24.0 * 365.0 * 10.0, folder=None, day_save=None, save_prod=True,
          kg_co2_day=None, face_area_prod=None, p_prod=None, dt_max=None, tolerance=None):
    """
    求解给定的模型 model. 且该model需要保证：
        1、最后一个cell是虚拟的，用于生产
        2、包含一个注入点，用于注入co2

    day_save：数据保存的时间间隔[单位：天];
    time_forward：向前求解的时间长度[单位: 秒]
    dt_max: 一个函数，参数为当前的时间，返回当前时间允许的最大的时间步长，单位是：秒

    注意：
        若指定参数kg_co2_day，则首先修改co2的注入速率，之后再计算.
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

    if kg_co2_day is not None:  # 更改co2注入的排量
        assert model.injector_number > 0
        for inj in model.injectors:
            inj.value = kg_co2_day / model.injector_number / inj.flu.den / (3600 * 24)

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
    solver = ConjugateGradientSolver(tolerance=tolerance if tolerance is not None else 1.0e-25)

    if day_save is None:
        day_save = 30.0

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
        if abs(z_max - cell.z) < 0.1 or abs(z_min - cell.z) < 0.1:
            top_cells.append(cell)
    print(f'Count of top cell: {len(top_cells)}')

    def mark_h2o_time():
        time = seepage.get_time(model) / (24 * 3600 * 365)
        for cell in top_cells:
            cell.get_fluid(*i_h2o).set_attr(fa_time, time)

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

    if folder is not None:  # 保存最终时刻
        if save_prod:
            monitor.save(path.join(folder, 'prod.txt'))  # 覆盖的原有的曲线
        model.save(path.join(folder, 'final.seepage'))
        seepage.print_cells(path.join(folder, 'final.txt'), model)

    # 计算之后，再返回model (后续可能用到)
    return model


def solve_post_exploit(model, time_forward=3600.0 * 24.0 * 365.0 * 500.0, folder=None,
                       dt_max=None, day_save=None, tolerance=None):
    """
    对于开发计算之后的模型，再计算更长的时间，来观察储层内的长期状态
    """
    if dt_max is None:
        dt_max = 3600.0 * 24.0 * 30.0

    if day_save is None:
        day_save = 365.0

    return solve(model=model, time_forward=time_forward, folder=folder,
                 kg_co2_day=0, face_area_prod=0, save_prod=False,
                 day_save=day_save,
                 dt_max=dt_max, tolerance=tolerance)


def execute_compare(kg_co2_day=15.0, root=None, width=50.0, x_inj=None, solve_post=True, dt_max=None,
                    **kwargs):
    """
    对比3个算例：1、仅仅注入；2、注采；3、仅仅采收
    """
    time_forward = 3600 * 24 * 365 * 30

    if x_inj is None:
        x_inj = [width * (1 / 8), width * (3 / 8), width * (5 / 8), width * (7 / 8)]

    assert root is not None
    assert path.isdir(root)

    # 计算仅仅注入
    folder = path.join(root, 'inj')
    model = create_model(x_inj=x_inj, z_inj=-150.0,
                         width=width, kg_inj_day=kg_co2_day, face_area_prod=0.0, **kwargs)
    solve(model=model, time_forward=time_forward, folder=folder, day_save=30.0, dt_max=dt_max)
    if solve_post:
        solve_post_exploit(model=model, folder=folder, dt_max=dt_max)
    export_co2(folder=folder)

    # 计算注采
    folder = path.join(root, 'inj_prod')
    model = create_model(x_inj=x_inj, z_inj=-30.0,
                         width=width, kg_inj_day=kg_co2_day, **kwargs)
    solve(model=model, time_forward=time_forward, folder=folder, day_save=30.0, dt_max=dt_max)
    if solve_post:
        solve_post_exploit(model=model, folder=folder, dt_max=dt_max)
    export_co2(folder=folder)

    # 计算仅降压开采
    model = create_model(x_inj=x_inj, z_inj=-30.0, width=width, kg_inj_day=0.0, **kwargs)
    solve(model=model, time_forward=time_forward,
          folder=path.join(root, 'prod'), day_save=30.0, dt_max=dt_max)


def export_co2(folder):
    """
    遍历计算结果文件夹的models文件夹，获得model中co2_hydrate的质量、co2气体质量、逃逸的co2质量随着时间的变化数据，并保存到co2_hyd.txt中

        name: 结果文件名. (将保存在folder中)
    """
    assert path.isdir(folder)

    models_folder = path.join(folder, 'models')
    assert path.isdir(models_folder)

    a = []  # time
    b = []  # hydrate
    c = []  # co2
    d = []  # co2 escaped
    e = []  # co2 in h2o

    for name in os.listdir(models_folder):
        gui.break_point()

        days = float(name[0: len('00000000000000_00001')].replace('_', '.'))
        a.append(days * 24 * 3600)  # 时间

        model = Seepage(path=path.join(models_folder, name))

        idx = model.find_fludef('co2_hyd')
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
        m2 = np.sum(m[z > z_max - 0.1]) + m[-1]

        c.append(m1 - m2)   # 计算区域的co2
        d.append(m2)  # 逃逸的co2

        # 溶解的co2
        idx = model.find_fludef('co2_in_h2o')
        assert idx is not None
        m = as_numpy(model).fluids(*idx).mass

        # 所有的co2
        m1 = np.sum(m)
        # 被视为逃逸的
        m2 = np.sum(m[z > z_max - 0.1]) + m[-1]

        e.append(m1 - m2)  # 计算区域的co2

        # 逃逸的溶解的co2也加入到d
        d[-1] += m2

        print(f'days = {days}, co2_hyd mass = {mass}')

    np.savetxt(path.join(folder, 'co2.txt'), join_cols(a, b, c, d, e))


def co2_seq(folder=None, co2_d=100, co2_h=80, inj_depth=200.0, salinity=None, mesh=None,
            inh_diff=1.0e6 / 400, co2_diff=None):
    """
    执行co2水合物封存计算模型 (建模和求解)。 since 2024-2-7
    """
    if mesh is None:
        mesh = create_cylinder(radius=300.0, height=400.0,
                               dr=1, dh=1, rc=100, hc=150, ratio=1.05, dr_max=10, dh_max=10)
        print(f'mesh = {mesh}')

    if salinity is None:
        salinity = 0.0315 / 2.165  # 将质量浓度(0.0315)转化为体积浓度

    def get_radi(x, y, z):
        return np.linalg.norm([x / (co2_d * 0.5), (z + inj_depth) / (co2_h * 0.5)])

    def co2_region(x, y, z):
        return get_radi(x, y, z) < 1

    def get_s(x, y, z):
        r = get_radi(x, y, z)
        if r < 1:
            # 让co2的饱和度在中心最高. follow 张东晓
            s_co2 = 0.75 + (0.4 - 0.75) * r
            s_liq = 1 - s_co2
            return (0, s_co2), (s_liq * (1 - salinity) * 0.94, s_liq * salinity * 0.94, 0, s_liq * 0.06), (0, 0, 0)
        else:
            return (0, 0), (1 * (1 - salinity), 1 * salinity, 0, 0), (0, 0, 0)

    t_top = 276.0826483615683
    grad_t = 0.04466

    # 范围
    z_min, z_max = mesh.get_pos_range(2)

    # 初始温度场
    t_ini = LinearField(v0=t_top, z0=z_max, dz=-grad_t)

    def get_t(x, y, z):
        if co2_region(x, y, z):
            return 288.0 * 0.3 + t_ini(x, y, z) * 0.7
        else:
            return t_ini(x, y, z)

    model = create_model(mesh=mesh, x_inj=[0], z_inj=-800.0, under_h=30.0, hyd_h=0,
                         kg_inj_day=0, face_area_prod=0.0,
                         perm=Tensor3(xx=5.0e-14, yy=5.0e-14, zz=1.0e-14),
                         free_h=0.0, s_ini=get_s, t_top=t_top, grad_t=grad_t, t_ini=get_t,
                         inh_diff=inh_diff, co2_diff=co2_diff)

    def dt_max(time):
        """
        在不同的时间，所允许的最大的时间步长
        """
        return max(30 * 24 * 3600, time / 1000.0)

    def day_save(day):
        """
        在不同的时刻，采用不同的保存间隔.
        """
        return max(100, day / 50)

    solve_post_exploit(model=model, folder=folder,
                       time_forward=3600.0 * 24.0 * 365.0 * 100000.0,
                       dt_max=dt_max, day_save=day_save)
    export_co2(folder=folder)


def test_base():
    folder = opath('co2', 'base')
    gui.execute(lambda: co2_seq(folder=folder),
                close_after_done=False, disable_gui=not is_windows)


if __name__ == '__main__':
    test_base()
