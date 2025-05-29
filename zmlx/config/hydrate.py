"""
用于水合物计算的配置.
"""
import zmlx.alg.sys as warnings

from zml import Seepage, log
from zmlx.alg.fsys import join_paths
from zmlx.alg.fsys import make_fname
from zmlx.alg.base import time2str
from zmlx.base.seepage import as_numpy
from zmlx.config import seepage
from zmlx.config.TherFlowConfig import TherFlowConfig
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluid.co2 import create as create_co2
from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_h2o_gas
from zmlx.fluid.h2o_ice import create as create_h2o_ice
from zmlx.kr.base import create_krf
from zmlx.plt.fig2 import tricontourf
from zmlx.react import ch4_hydrate as ch4_hydrate_react
from zmlx.react import co2_hydrate as co2_hydrate_react
from zmlx.react import dissolution
from zmlx.react import h2o_ice as icing_react
from zmlx.react import vapor as vapor_react
from zmlx.react.alpha.salinity import data as salinity_c2t
from zmlx.react.inh import add_inh
from zmlx.ui import gui
from zmlx.utility.capillary_effect import CapillaryEffect
from zmlx.utility.fields import LinearField


def create_fludefs(has_co2=False,
                   has_steam=False,
                   has_inh=False,
                   has_ch4_in_liq=False,
                   has_co2_in_liq=False,
                   h2o_density=None,
                   ch4_def=None,
                   co2_def=None,
                   h2o_def=None,
                   inh_def=None,
                   other_gas=None, other_liq=None, other_sol=None):
    """
    创建水合物计算的时候的流体的定义(气体、液体和固体).
        当给定h2o_density的时候，h2o采用固定的密度.
        当给定co2的时候，将使用给定的定义.

    返回流体的定义(一个list)：
        气体：ch4, [co2, h2o_gas]
        液体：h2o, [ch4_in_liq, co2_in_liq]
        固体：ch4_hydrate, h2o_ice, [co2_hydrate]
    """

    # ch4
    if ch4_def is None:
        ch4_def = create_ch4()  # 此时，使用默认的定义

    # co2
    if has_co2_in_liq:  # 此时必然要求co2存在
        has_co2 = True
    if co2_def is not None:
        has_co2 = True
    else:
        assert co2_def is None
        if has_co2:
            co2_def = create_co2()

    # h2o
    if h2o_def is None:
        h2o_def = create_h2o(density=h2o_density)

    # inh
    if inh_def is not None:
        if has_inh is not None:  # add warning since 2024-6-11
            if not has_inh:
                warnings.warn('has inh define but do not has inh')
        has_inh = True
    else:
        assert inh_def is None
        if has_inh:
            inh_def = Seepage.FluDef(den=2165.0, vis=0.001,
                                     specific_heat=4030.0)

    # 1  气体：
    gas = Seepage.FluDef(name='gas')
    gas.add_component(ch4_def, name='ch4')
    if has_co2:
        gas.add_component(co2_def, name='co2')
    if has_steam:
        gas.add_component(create_h2o_gas(), name='h2o_gas')
    if other_gas is not None:  # 其它所有的气体
        for item in other_gas:
            gas.add_component(item)

    # 2  液体:
    liq = Seepage.FluDef(name='liq')
    liq.add_component(h2o_def, name='h2o')
    if has_inh:
        liq.add_component(inh_def, name='inh')
    if has_ch4_in_liq:
        liq.add_component(ch4_def, name='ch4_in_liq')
    if has_co2_in_liq:
        assert has_co2
        liq.add_component(co2_def, name='co2_in_liq')
    if other_liq is not None:  # 其它的液体
        for item in other_liq:
            liq.add_component(item)

    # 3   固体:
    sol = Seepage.FluDef(name='sol')
    sol.add_component(create_ch4_hydrate(), name='ch4_hydrate')
    sol.add_component(create_h2o_ice(), name='h2o_ice')
    if has_co2:
        sol.add_component(create_co2_hydrate(), name='co2_hydrate')
    if other_sol is not None:  # 其它的固体
        for item in other_sol:
            sol.add_component(item)

    # 返回list
    return [gas, liq, sol]


def create_reactions(has_co2=False,
                     has_steam=False,
                     has_inh=False,
                     has_ch4_in_liq=False,
                     has_co2_in_liq=False,
                     support_ch4_hyd_diss=True,
                     support_ch4_hyd_form=True,
                     others=None,
                     sol_dt=None):
    """
    创建反应.
        sol_dt: 由于固体的存在，对平衡温度的修改的幅度。从而使得，固体的比例越高，则水合物的形成
                相对更加困难。(一个测试属性; 应给定小于等于0的数值)
                初步测试表明，使用sol_dt对于最终饱和度场的稳定有一定效果。测试sol_dt=-1
                since 2024-3-13
    """
    if sol_dt is None:
        sol_dt = 0.0

    result = []

    # 添加甲烷水合物的相变
    r = ch4_hydrate_react.create(gas='ch4', wat='h2o', hyd='ch4_hydrate',
                                 dissociation=support_ch4_hyd_diss,
                                 formation=support_ch4_hyd_form)
    # 抑制固体比例过高，增强计算稳定性 （非常必要）
    assert -5.0 <= sol_dt <= 0.0
    add_inh(r, sol='sol', liq=None,
            c=[0, 0.8, 1.0],
            t=[0, sol_dt, -200.0], use_vol=True)
    if has_inh:
        add_inh(r, sol='inh', liq='liq',
                c=salinity_c2t[0],
                t=salinity_c2t[1])
    result.append(r)

    # 添加冰的相变
    result.append(icing_react.create(flu='h2o', sol='h2o_ice'))

    if has_co2:
        # 添加co2和co2水合物之间的相变
        r = co2_hydrate_react.create(gas='co2', wat='h2o',
                                     hyd='co2_hydrate')
        # 抑制固体比例过高，增强计算稳定性 （非常必要）
        add_inh(r, sol='sol', liq=None,
                c=[0, 0.8, 1.0],
                t=[0, sol_dt, -200.0], use_vol=True)
        if has_inh:
            add_inh(r, sol='inh', liq='liq',
                    c=salinity_c2t[0],
                    t=salinity_c2t[1])
        result.append(r)

    if has_steam:
        # 添加水和水蒸气之间的相变反应
        # 2022-10-19
        result.append(vapor_react.create(vap='h2o_gas',
                                         wat='h2o'))

    if has_ch4_in_liq:
        result.append(dissolution.create(sol='ch4', sol_in_liq='ch4_in_liq',
                                         liq='liq', ca_sol='n_ch4_sol'))

    if has_co2_in_liq:
        result.append(dissolution.create(sol='co2', sol_in_liq='co2_in_liq',
                                         liq='liq', ca_sol='n_co2_sol'))

    # 其它的反应
    if others is not None:
        for item in others:
            result.append(item)

    return result


def create_caps(inh_diff=None,
                co2_diff=None,
                ch4_diff=None,
                co2_cap=None,
                ch4_cap=None,
                others=None):
    """
    创建扩散过程
    """
    result = []

    # 盐度的扩散
    if inh_diff is not None:
        assert inh_diff >= 0
        cap = dict(fid0='inh', fid1='h2o',
                   get_idx=lambda x, y, z: 0,
                   data=[[[0, 1], [0, inh_diff]], ])
        result.append(cap)

    # 溶解co2的扩散
    if co2_diff is not None:
        assert co2_diff >= 0
        cap = dict(fid0='co2_in_liq', fid1='h2o',
                   get_idx=lambda x, y, z: 0,
                   data=[[[0, 1], [0, co2_diff]], ])
        result.append(cap)

    # 溶解ch4的扩散
    if ch4_diff is not None:
        assert ch4_diff >= 0
        cap = dict(fid0='ch4_in_liq', fid1='h2o',
                   get_idx=lambda x, y, z: 0,
                   data=[[[0, 1], [0, ch4_diff]], ])
        result.append(cap)

    # 自由co2的扩散（毛管压力驱动下）
    if co2_cap is not None:
        assert co2_cap >= 0
        cap = dict(fid0='co2', fid1='liq',
                   get_idx=lambda x, y, z: 0,
                   data=[[[0, 1], [0, co2_cap]], ])
        result.append(cap)

    # 自由ch4的扩散（毛管压力驱动下）
    if ch4_cap is not None:
        assert ch4_cap >= 0
        cap = dict(fid0='ch4', fid1='liq',
                   get_idx=lambda x, y, z: 0,
                   data=[[[0, 1], [0, ch4_cap]], ])
        result.append(cap)

    if others is not None:
        for item in others:
            result.append(item)

    # 返回结果.
    return result


def create_kwargs(has_co2=False,
                  has_steam=False,
                  has_inh=False,
                  has_ch4_in_liq=False,
                  has_co2_in_liq=False,
                  inh_diff=None,
                  ch4_diff=None,
                  co2_diff=None,
                  co2_cap=None,
                  ch4_cap=None,
                  support_ch4_hyd_diss=True,
                  support_ch4_hyd_form=True,
                  gr=None,
                  h2o_density=None,
                  co2_def=None,
                  gravity=None,
                  dt_max=None,
                  sol_dt=None,
                  **kwargs):
    """
    返回用于seepage.create的参数列表
        当给定co2的时候，将使用给定的定义. (since 2024-1-10)
    """
    if has_co2_in_liq:  # 此时，必须要求存在co2
        has_co2 = True

    fludefs = create_fludefs(h2o_density=h2o_density,
                             co2_def=co2_def,
                             has_co2=has_co2,
                             has_steam=has_steam,
                             has_inh=has_inh,
                             has_ch4_in_liq=has_ch4_in_liq,
                             has_co2_in_liq=has_co2_in_liq,
                             )
    reactions = create_reactions(support_ch4_hyd_diss=support_ch4_hyd_diss,
                                 support_ch4_hyd_form=support_ch4_hyd_form,
                                 has_inh=has_inh,
                                 has_co2=has_co2,
                                 has_steam=has_steam,
                                 has_ch4_in_liq=has_ch4_in_liq,
                                 has_co2_in_liq=has_co2_in_liq,
                                 sol_dt=sol_dt,
                                 )

    # 修改部分参数，确保协调.
    if not has_inh:
        inh_diff = None
    if not has_ch4_in_liq:
        ch4_diff = None
    if not has_co2_in_liq:
        co2_diff = None
    if not has_co2:
        co2_cap = None

    caps = create_caps(ch4_diff=ch4_diff,
                       inh_diff=inh_diff,
                       co2_diff=co2_diff,
                       co2_cap=co2_cap,
                       ch4_cap=ch4_cap)

    if dt_max is None:
        dt_max = 3600 * 24

    if gr is None:
        gr = create_krf(as_interp=True)

    if gravity is None:
        gravity = [0, -10, 0]

    # 返回结果.
    return dict(dt_max=dt_max,
                fludefs=fludefs,
                reactions=reactions,
                caps=caps,
                gr=gr,
                gravity=gravity,
                has_solid=True,
                **kwargs)


def create_t_ini(z_top=0.0, t_top=276.0, grad_t=0.04466):
    """
    创建温度的初始场;
        (在z方向线性)
    """
    assert 0.02 <= grad_t <= 0.06
    return LinearField(v0=t_top, z0=z_top, dz=-grad_t)


def create_p_ini(z_top=0.0, p_top=12e6, grad_p=0.01e6):
    """
    创建压力的初始场;
        (在z方向线性)
    """
    assert 0.001e6 <= grad_p <= 0.1e6
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
                          folder=join_paths(folder, key),
                          ext='.jpg', unit='y')

    cell_keys = seepage.cell_keys(model)

    def show_key(key):
        tricontourf(x, y, as_numpy(model).cells.get(cell_keys[key]),
                    caption=key,
                    fname=fname(key), **kwargs)

    show_key('pre')
    show_key('temperature')

    fv_all = as_numpy(model).cells.fluid_vol

    def show_s(flu_name):
        s = as_numpy(model).fluids(*model.find_fludef(flu_name)).vol / fv_all
        tricontourf(x, y, s, caption=flu_name,
                    fname=fname(flu_name), **kwargs)

    for item in ['ch4', 'liq', 'ch4_hydrate']:
        show_s(item)


class ConfigV2:
    """
    水合物计算的配置
        deprecated!!!
    """

    def __init__(self, has_co2=False, has_steam=False, has_inh=False,
                 has_ch4_in_liq=False, inh_diff=None,
                 ch4_diff=None,
                 support_ch4_hyd_diss=True, support_ch4_hyd_form=True,
                 gr=None):
        """
        创建.
            注意，当gr为None的时候，将自动创建一个 (从0到1之间，且y不大于1).
        """
        log(text='deprecated: hydrate ConfigV2 used',
            tag='tag_240305')
        self.has_co2 = has_co2
        self.has_steam = has_steam
        self.has_inh = has_inh
        self.has_ch4_in_liq = has_ch4_in_liq
        self.inh_diff = inh_diff
        self.ch4_diff = ch4_diff
        self.support_ch4_hyd_diss = support_ch4_hyd_diss
        self.support_ch4_hyd_form = support_ch4_hyd_form
        self.gr = create_krf(as_interp=True) if gr is None else gr

    def get_fludefs(self, h2o_density=None, co2=None):
        """
        创建流体的定义.
        """
        return create_fludefs(h2o_density=h2o_density, co2_def=co2,
                              has_co2=self.has_co2,
                              has_steam=self.has_steam,
                              has_inh=self.has_inh,
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
                                has_co2=self.has_co2,
                                has_steam=self.has_steam,
                                has_ch4_in_liq=self.has_ch4_in_liq)

    @property
    def caps(self):
        """
        扩散
        """
        return create_caps(ch4_diff=self.ch4_diff, inh_diff=self.inh_diff)

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
        return dict(dt_max=3600 * 24,
                    fludefs=self.get_fludefs(h2o_density=h2o_density,
                                             co2=co2),
                    reactions=self.reactions,
                    caps=self.caps,
                    gr=self.gr, gravity=[0, -10, 0], has_solid=True)


class Config(TherFlowConfig):
    """
    水合物求解配置
        deprecated!!!
    """

    def __init__(self, has_co2=False, has_steam=False, has_inh=False,
                 has_ch4_in_liq=False, inh_diff_rate=None,
                 ch4_diff_rate=None,
                 support_ch4_hyd_diss=True, support_ch4_hyd_form=True,
                 krf=None):
        """
        创建一个水合物的求解配置. 包含气<Id=0>、液<Id=1>和固<Id=2>三种相态;
        其中气体为：
            [Ch4, [Co2, Steam]], 其中Co2只有当has_co2为True时存在，Steam只有当has_steam的时候存在;

        液体为:
            [H2o, [Inh], [ch4]]，其中Inh代表抑制剂，当has_inh参数为True的时候存在  ch4为溶解的甲烷气体

        固体为:
            [CH4_hyd, H2o_Ice, [Co2_Hyd]]. 其中Co2_Hyd只有当has_co2为True的时候存在

        化学反应为:
            Ch4水合物的形成/分解
            水/冰相互转化
            Ch4水合物的形成/分解 [当has_co2参数为True的时候]
            H2o/Steam之间的相互转化 [当has_steam参数为True的时候]
            Ch4在水中的溶解反应 [当has_ch4_in_liq为True的时候]
        """
        super().__init__()
        log(text='deprecated: hydrate Config used', tag='tag_240304')

        # 添加默认的重力
        # since 2023-4-19
        self.gravity = (0, -10, 0)

        # 最后一种流体其实是固体，不参流体计算，因此，在流体计算的时候，把这个数据暂存一下
        self.has_solid = True

        # 配置气体的组分
        gas = [create_ch4(), ]
        if has_co2:
            # 添加CO2
            ico2 = len(gas)
            gas.append(create_co2())
        else:
            ico2 = None
        if has_steam:
            # 添加蒸汽
            steam_id = len(gas)
            gas.append(create_h2o_gas())
        else:
            steam_id = None
        gas_id = self.add_fluid(gas)
        self.igas = gas_id

        self.components['gas'] = gas_id
        self.components['ch4'] = [gas_id, 0]
        if ico2 is not None:
            self.components['co2'] = [gas_id, ico2]
        if steam_id is not None:
            self.components['h2o_gas'] = [gas_id, steam_id]

        # 配置液体
        liq = [create_h2o(), ]
        if has_inh:
            # 添加盐度
            inh_id = len(liq)
            # 这里，采用NaCl的密度和比热容
            liq.append(Seepage.FluDef(den=2165.0, vis=0.001,
                                      specific_heat=4030.0))
        else:
            inh_id = None
        if has_ch4_in_liq:
            ich4_in_liq = len(liq)
            self.cell_keys.add_keys('ch4_sol')
            #
            # 每个组分都需要有一个密度，这个确实有些难办，溶解在水中的气体，它其实已经不是气体了。
            # 对于混溶的各个组分，如何确定密度，我也还没想好，也没有具体去调研别人的处理方法。
            #
            # 这里，主要考虑到，溶解的气体很少，其实气体组分的密度无论怎么给（因为它此时是液体
            # 的一个组分，所以就参考水的属性，只要别太极端），对结果的影响都不会太大。
            #
            # 粘性系数和比热也是一样。
            #
            #    -- zzb, 2023-5-25
            #
            liq.append(Seepage.FluDef(den=500.0, vis=0.001,
                                      specific_heat=1000.0))
        else:
            ich4_in_liq = None
        liq_id = self.add_fluid(liq)
        self.iliq = liq_id
        self.components['liq'] = liq_id
        self.components['h2o'] = [liq_id, 0]
        if inh_id is not None:
            self.components['inh'] = [liq_id, inh_id]
        if ich4_in_liq is not None:
            self.components['ch4_in_liq'] = [liq_id, ich4_in_liq]

        # 配置固体
        sol = [create_ch4_hydrate(), create_h2o_ice()]
        if has_co2:
            # 当有二氧化碳气体的时候，就有其水合物
            ico2_hyd = len(sol)
            sol.append(create_co2_hydrate())
        else:
            ico2_hyd = None
        sol_id = self.add_fluid(sol)
        self.isol = sol_id
        self.components['sol'] = sol_id
        self.components['ch4_hydrate'] = [sol_id, 0]
        self.components['h2o_ice'] = [sol_id, 1]
        if ico2_hyd is not None:
            self.components['co2_hydrate'] = [sol_id, ico2_hyd]

        # -------------------------------------------------------------
        # 添加甲烷水合物的相变
        r = ch4_hydrate_react.create(
            gas=self.components['ch4'], wat=self.components['h2o'],
            hyd=self.components['ch4_hydrate'],
            fa_t=self.flu_keys['temperature'],
            fa_c=self.flu_keys['specific_heat'],
            dissociation=support_ch4_hyd_diss,
            formation=support_ch4_hyd_form
        )
        # 抑制固体比例过高，增强计算稳定性 （非常必要）
        r['inhibitors'].append(dict(sol=self.components['sol'],
                                    liq=None,
                                    c=[0, 0.8, 1.0],
                                    t=[0, 0, -200.0]))
        if has_inh:
            # 抑制剂修改平衡温度
            r['inhibitors'].append(dict(sol=self.components['inh'],
                                        liq=self.components['liq'],
                                        c=salinity_c2t[0],
                                        t=salinity_c2t[1]))
        self.reactions.append(r)

        # -------------------------------------------------------------
        # 添加水和冰之间的相变
        self.reactions.append(
            icing_react.create(
                flu=self.components['h2o'],
                sol=self.components['h2o_ice'],
                fa_t=self.flu_keys['temperature'],
                fa_c=self.flu_keys['specific_heat']))

        # -------------------------------------------------------------
        if has_co2:
            # 添加CO2和CO2水合物之间的相变<只要有了CO2，那么就要有水合物>
            assert ico2 is not None and ico2_hyd is not None
            r = co2_hydrate_react.create(
                gas=self.components['co2'],
                wat=self.components['h2o'],
                hyd=self.components['co2_hydrate'],
                fa_t=self.flu_keys['temperature'],
                fa_c=self.flu_keys['specific_heat'])
            # 抑制固体比例过高，增强计算稳定性 （非常必要）
            r['inhibitors'].append(dict(sol=self.components['sol'],
                                        liq=None,
                                        c=[0, 0.8, 1.0],
                                        t=[0, 0, -200.0], ))
            if has_inh:
                # 抑制剂修改平衡温度
                r['inhibitors'].append(dict(sol=self.components['inh'],
                                            liq=self.components['liq'],
                                            c=salinity_c2t[0],
                                            t=salinity_c2t[1]))
            self.reactions.append(r)

        # -------------------------------------------------------------
        if has_steam:
            # 添加水和水蒸气之间的相变反应
            # 2022-10-19
            assert steam_id is not None
            self.reactions.append(
                vapor_react.create(
                    vap=self.components['h2o_gas'],
                    wat=self.components['h2o'],
                    fa_t=self.flu_keys['temperature'],
                    fa_c=self.flu_keys['specific_heat']))

        # -------------------------------------------------------------
        if has_ch4_in_liq:
            self.reactions.append(
                dissolution.create(
                    gas=self.components['ch4'],
                    gas_in_liq=self.components['ch4_in_liq'],
                    liq=self.components['liq'],
                    ca_sol=self.cell_keys['ch4_sol'],
                    fa_c=self.flu_keys['specific_heat'],
                    fa_t=self.flu_keys['temperature']))

        # -------------------------------------------------------------
        if has_ch4_in_liq and ch4_diff_rate is not None:
            # 添加水中溶解气的扩散
            assert ch4_diff_rate > 0
            i0 = self.components['ch4_in_liq']
            i1 = self.components['h2o']
            cap = CapillaryEffect(i0, i1,
                                  s2p=([0, 1], [0, ch4_diff_rate]))
            self.diffusions.append(cap)

        # -------------------------------------------------------------
        if has_inh and inh_diff_rate is not None:
            # 添加水中盐度的扩散
            assert inh_diff_rate > 0
            i0 = self.components['inh']
            i1 = self.components['h2o']
            cap = CapillaryEffect(i0, i1,
                                  s2p=([0, 1], [0, inh_diff_rate]))
            self.diffusions.append(cap)

        if krf is None:
            self.krf = create_krf(as_interp=True)
        else:
            self.krf = krf


def create(*args, **kwargs):
    """
        deprecated!!!
    """
    warnings.warn(
        'The function hydrate.create is deprecated (remove after 2024-12-01)',
        DeprecationWarning, stacklevel=2)
    return Config(*args, **kwargs)
