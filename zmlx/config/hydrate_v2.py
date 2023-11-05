from zml import *
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluid.co2 import create as create_co2
from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_h2o_gas
from zmlx.fluid.h2o_ice import create as create_h2o_ice
from zmlx.kr.create_krf import create_krf
from zmlx.react import ch4_hydrate as ch4_hydrate_react
from zmlx.react import co2_hydrate as co2_hydrate_react
from zmlx.react import dissolution
from zmlx.react import h2o_ice as icing_react
from zmlx.react import vapor as vapor_react
from zmlx.react.alpha.salinity import data as salinity_c2t


class Config:
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

    @property
    def fludefs(self):
        """
        创建流体的定义
        """
        gas = Seepage.FluDef(name='gas')
        gas.add_component(create_ch4(name='ch4'))
        if self.has_co2:
            gas.add_component(create_co2(name='co2'))
        if self.has_steam:
            gas.add_component(create_h2o_gas(name='h2o_gas'))

        liq = Seepage.FluDef(name='liq')
        liq.add_component(create_h2o(name='h2o'))
        if self.has_inh:
            liq.add_component(Seepage.FluDef(den=2165.0, vis=0.001, specific_heat=4030.0, name='inh'))
        if self.has_ch4_in_liq:
            liq.add_component(Seepage.FluDef(den=500.0, vis=0.001, specific_heat=1000.0, name='ch4_in_liq'))

        sol = Seepage.FluDef(name='sol')
        sol.add_component(create_ch4_hydrate(name='ch4_hydrate'))
        sol.add_component(create_h2o_ice(name='h2o_ice'))
        if self.has_co2:
            sol.add_component(create_co2_hydrate(name='co2_hydrate'))

        return [gas, liq, sol]

    @property
    def reactions(self):
        result = []
        # -------------------------------------------------------------
        # 添加甲烷水合物的相变
        r = ch4_hydrate_react.create(gas='ch4', wat='h2o', hyd='ch4_hydrate',
                                     dissociation=self.support_ch4_hyd_diss, formation=self.support_ch4_hyd_form)
        # 抑制固体比例过高，增强计算稳定性 （非常必要）
        r['inhibitors'].append(create_dict(sol='sol', liq=None, c=[0, 0.8, 1.0], t=[0, 0, -200.0]))
        if self.has_inh:
            # 抑制剂修改平衡温度
            r['inhibitors'].append(create_dict(sol='inh',
                                               liq='liq',
                                               c=salinity_c2t[0],
                                               t=salinity_c2t[1]))
        result.append(r)

        # -------------------------------------------------------------
        # 添加水和冰之间的相变
        result.append(icing_react.create(flu='h2o', sol='h2o_ice'))

        # -------------------------------------------------------------
        if self.has_co2:
            # 添加CO2和CO2水合物之间的相变<只要有了CO2，那么就要有水合物>
            r = co2_hydrate_react.create(gas='co2', wat='h2o', hyd='co2_hydrate')
            # 抑制固体比例过高，增强计算稳定性 （非常必要）
            r['inhibitors'].append(create_dict(sol='sol', liq=None, c=[0, 0.8, 1.0], t=[0, 0, -200.0]))
            if self.has_inh:
                # 抑制剂修改平衡温度
                r['inhibitors'].append(create_dict(sol='inh', liq='liq', c=salinity_c2t[0], t=salinity_c2t[1]))
            result.append(r)

        # -------------------------------------------------------------
        if self.has_steam:
            # 添加水和水蒸气之间的相变反应
            # 2022-10-19
            result.append(vapor_react.create(vap='h2o_gas', wat='h2o'))

        # -------------------------------------------------------------
        if self.has_ch4_in_liq:
            result.append(dissolution.create(gas='ch4', gas_in_liq='ch4_in_liq', liq='liq', ca_sol='n_ch4_sol'))

        return result

    @property
    def caps(self):
        result = []
        # -------------------------------------------------------------
        if self.has_ch4_in_liq and self.ch4_diff_rate is not None:
            # 添加水中溶解气的扩散
            assert self.ch4_diff_rate > 0
            cap = create_dict(fid0='ch4_in_liq', fid1='h2o',
                              get_idx=lambda i: 0,
                              data=[[[0, 1], [0, self.ch4_diff_rate]], ])
            result.append(cap)
        # -------------------------------------------------------------
        if self.has_inh and self.inh_diff_rate is not None:
            # 添加水中盐度的扩散
            assert self.inh_diff_rate > 0
            cap = create_dict(fid0='inh', fid1='h2o', get_idx=lambda i: 0,
                              data=[[[0, 1], [0, self.inh_diff_rate]], ])
            result.append(cap)
        return result

    @property
    def kwargs(self):
        """
        返回用于seepage.create的参数列表
        """
        return create_dict(dt_max=3600 * 24,
                           fludefs=self.fludefs, reactions=self.reactions, caps=self.caps,
                           gr=self.gr, gravity=[0, -10, 0], has_solid=True)
