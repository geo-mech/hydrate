from zml import Seepage, create_dict, SeepageMesh
from zmlx.alg.linspace import linspace
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.make_fname import make_fname
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluid.co2 import create as create_co2
from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_h2o_gas
from zmlx.fluid.h2o_ice import create as create_h2o_ice
from zmlx.kr.create_krf import create_krf
from zmlx.plt.tricontourf import tricontourf
from zmlx.react import ch4_hydrate as ch4_hydrate_react
from zmlx.react import co2_hydrate as co2_hydrate_react
from zmlx.react import dissolution
from zmlx.react import h2o_ice as icing_react
from zmlx.react import vapor as vapor_react
from zmlx.react.alpha.salinity import data as salinity_c2t
from zmlx.ui import gui
from zmlx.utility.LinearField import LinearField
from zmlx.utility.SeepageNumpy import as_numpy


def create_fludefs(h2o_density=None, co2=None, has_co2=False, has_steam=False, has_inh=False,
                   has_ch4_in_liq=False):
    """
    创建水合物计算的时候的流体的定义. 当给定h2o_density的时候，h2o采用固定的密度.
        当给定co2的时候，将使用给定的定义.
    """
    gas = Seepage.FluDef(name='gas')
    gas.add_component(create_ch4(name='ch4'))
    if has_co2:
        if co2 is not None:  # 使用给定的co2定义
            gas.add_component(co2.get_copy(name='co2'))
        else:
            gas.add_component(create_co2(name='co2'))
    if has_steam:
        gas.add_component(create_h2o_gas(name='h2o_gas'))

    liq = Seepage.FluDef(name='liq')
    liq.add_component(create_h2o(name='h2o', density=h2o_density))
    if has_inh:
        liq.add_component(Seepage.FluDef(den=2165.0, vis=0.001,
                                         specific_heat=4030.0, name='inh'))
    if has_ch4_in_liq:
        liq.add_component(Seepage.FluDef(den=500.0, vis=0.001,
                                         specific_heat=1000.0, name='ch4_in_liq'))

    sol = Seepage.FluDef(name='sol')
    sol.add_component(create_ch4_hydrate(name='ch4_hydrate'))
    sol.add_component(create_h2o_ice(name='h2o_ice'))
    if has_co2:
        sol.add_component(create_co2_hydrate(name='co2_hydrate'))

    return [gas, liq, sol]


def create_s_ini(sh=None, salinity=0.0, hyd_bottom=None, hyd_top=None,
                 has_co2=False, has_steam=False, has_inh=False, has_ch4_in_liq=False):
    """
    创建饱和度场. (沿着z方向分层)
    """
    sg = [0.0, ]
    if has_co2:
        sg.append(0.0)
    if has_steam:
        sg.append(0.0)

    if not has_inh:
        salinity = 0.0

    sl1 = [1.0 * (1.0 - salinity), ]
    if has_inh:
        sl1.append(salinity)
    if has_ch4_in_liq:
        sl1.append(0)

    assert 0.0 <= sh <= 0.9
    sl2 = [item * (1 - sh) for item in sl1]

    ss2 = [sh, 0]
    if has_co2:
        ss2.append(0)
    ss1 = [item * 0 for item in ss2]

    return lambda x, y, z: [sg, sl2, ss2] if hyd_bottom <= z <= hyd_top else [sg, sl1, ss1]


def create_reactions(support_ch4_hyd_diss=True, support_ch4_hyd_form=True, has_inh=False,
                     has_co2=False, has_steam=False, has_ch4_in_liq=False):
    """
    创建反应
    """
    result = []

    r = ch4_hydrate_react.create(gas='ch4', wat='h2o', hyd='ch4_hydrate',
                                 dissociation=support_ch4_hyd_diss, formation=support_ch4_hyd_form)
    # 抑制固体比例过高，增强计算稳定性 （非常必要）
    r['inhibitors'].append(create_dict(sol='sol', liq=None, c=[0, 0.8, 1.0], t=[0, 0, -200.0]))
    if has_inh:
        # 抑制剂修改平衡温度
        r['inhibitors'].append(create_dict(sol='inh',
                                           liq='liq',
                                           c=salinity_c2t[0],
                                           t=salinity_c2t[1]))
    result.append(r)

    result.append(icing_react.create(flu='h2o', sol='h2o_ice'))

    if has_co2:
        # 添加CO2和CO2水合物之间的相变<只要有了CO2，那么就要有水合物>
        r = co2_hydrate_react.create(gas='co2', wat='h2o', hyd='co2_hydrate')
        # 抑制固体比例过高，增强计算稳定性 （非常必要）
        r['inhibitors'].append(create_dict(sol='sol', liq=None, c=[0, 0.8, 1.0], t=[0, 0, -200.0]))
        if has_inh:
            # 抑制剂修改平衡温度
            r['inhibitors'].append(create_dict(sol='inh', liq='liq', c=salinity_c2t[0], t=salinity_c2t[1]))
        result.append(r)

    if has_steam:
        # 添加水和水蒸气之间的相变反应
        # 2022-10-19
        result.append(vapor_react.create(vap='h2o_gas', wat='h2o'))

    if has_ch4_in_liq:
        result.append(dissolution.create(gas='ch4', gas_in_liq='ch4_in_liq', liq='liq', ca_sol='n_ch4_sol'))

    return result


def create_caps(has_ch4_in_liq=False, ch4_diff_rate=None, has_inh=False, inh_diff_rate=None):
    """
    创建扩散
    """
    result = []

    if has_ch4_in_liq and ch4_diff_rate is not None:
        # 添加水中溶解气的扩散
        assert ch4_diff_rate > 0
        cap = create_dict(fid0='ch4_in_liq', fid1='h2o',
                          get_idx=lambda i: 0,
                          data=[[[0, 1], [0, ch4_diff_rate]], ])
        result.append(cap)

    if has_inh and inh_diff_rate is not None:
        # 添加水中盐度的扩散
        assert inh_diff_rate > 0
        cap = create_dict(fid0='inh', fid1='h2o', get_idx=lambda i: 0,
                          data=[[[0, 1], [0, inh_diff_rate]], ])
        result.append(cap)
    return result


def create_t_ini(z_top=0.0, t_top=276.0, grad_t=0.04466):
    """
    创建温度的初始场(在z方向线性)
    """
    assert 0.02 <= grad_t <= 0.06
    return LinearField(v0=t_top, z0=z_top, dz=-grad_t)


def create_p_ini(z_top=0.0, p_top=12e6, grad_p=0.01e6):
    """
    创建压力的初始场(在z方向线性)
    """
    return LinearField(v0=p_top, z0=z_top, dz=-grad_p)


def create_denc_ini(z_min, z_max, denc=3e6):
    """
    储层土体的密度乘以比热（在顶部和底部，将它设置为非常大以固定温度）
    """
    return lambda x, y, z: denc if z_min + 0.1 < z < z_max - 0.1 else 1e20


def create_fai_ini(*, z_max, fai=0.2):
    """
    孔隙度（在顶部，将孔隙度设置为非常大，以固定压力）
    """
    return lambda x, y, z: 1.0e7 if abs(z - z_max) < 0.1 else fai


def show_2d(model: Seepage, folder=None, xdim=0, ydim=1):
    """
    二维绘图，且当folder给定的时候，将绘图结果保存到给定的文件夹
    """
    if not gui.exists():
        return
    time = seepage.get_time(model)
    kwargs = {'title': f'plot when model.time={time2str(time)}'}
    x = as_numpy(model).cells.get(-(xdim + 1))
    y = as_numpy(model).cells.get(-(ydim + 1))

    def fname(key):
        return make_fname(time / (3600 * 24 * 365),
                          folder=join_paths(folder, key), ext='.jpg', unit='y')

    cell_keys = seepage.cell_keys(model)

    def show_key(key):
        tricontourf(x, y, as_numpy(model).cells.get(cell_keys[key]), caption=key,
                    fname=fname(key), **kwargs)

    show_key('pre')
    show_key('temperature')

    fv_all = as_numpy(model).cells.fluid_vol

    def show_s(flu_name):
        s = as_numpy(model).fluids(*model.find_fludef(flu_name)).vol / fv_all
        tricontourf(x, y, s, caption=flu_name, fname=fname(flu_name), **kwargs)

    for item in ['ch4', 'liq', 'ch4_hydrate']:
        show_s(item)


class Config:
    """
    水合物计算的配置
    """

    def __init__(self, has_co2=False, has_steam=False, has_inh=False, has_ch4_in_liq=False, inh_diff_rate=None,
                 ch4_diff_rate=None,
                 support_ch4_hyd_diss=True, support_ch4_hyd_form=True, gr=None):
        """
        创建.
            注意，当gr为None的时候，将自动创建一个 (从0到1之间，且y不大于1).
        """
        self.has_co2 = has_co2
        self.has_steam = has_steam
        self.has_inh = has_inh
        self.has_ch4_in_liq = has_ch4_in_liq
        self.inh_diff_rate = inh_diff_rate
        self.ch4_diff_rate = ch4_diff_rate
        self.support_ch4_hyd_diss = support_ch4_hyd_diss
        self.support_ch4_hyd_form = support_ch4_hyd_form
        self.gr = create_krf(as_interp=True) if gr is None else gr

    def get_fludefs(self, h2o_density=None, co2=None):
        """
        创建流体的定义.
        """
        return create_fludefs(h2o_density=h2o_density, co2=co2, has_co2=self.has_co2,
                              has_steam=self.has_steam, has_inh=self.has_inh,
                              has_ch4_in_liq=self.has_ch4_in_liq)

    @property
    def fludefs(self):
        """
        创建流体的定义.
        """
        return self.get_fludefs()

    @property
    def reactions(self):
        """
        反应
        """
        return create_reactions(support_ch4_hyd_diss=self.support_ch4_hyd_diss,
                                support_ch4_hyd_form=self.support_ch4_hyd_form,
                                has_inh=self.has_inh,
                                has_co2=self.has_co2, has_steam=self.has_steam,
                                has_ch4_in_liq=self.has_ch4_in_liq)

    @property
    def caps(self):
        """
        扩散
        """
        return create_caps(has_ch4_in_liq=self.has_ch4_in_liq, ch4_diff_rate=self.ch4_diff_rate,
                           has_inh=self.has_inh, inh_diff_rate=self.inh_diff_rate)

    @property
    def kwargs(self):
        """
        返回用于seepage.create的参数列表
        """
        return self.get_kw()

    def get_kw(self, h2o_density=None, co2=None):
        """
        返回用于seepage.create的参数列表
            当给定co2的时候，将使用给定的定义. (since 2024-1-10)
        """
        return create_dict(dt_max=3600 * 24,
                           fludefs=self.get_fludefs(h2o_density=h2o_density, co2=co2), reactions=self.reactions,
                           caps=self.caps,
                           gr=self.gr, gravity=[0, -10, 0], has_solid=True)
