from zml import *
from zmlx.react.alpha.salinity import data as salinity_c2t
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
from zmlx.react import h2o_ice as icing_react
from zmlx.react import vapor as vapor_react
from zmlx.react import dissolution
from zmlx.utility.CapillaryEffect import CapillaryEffect
from zmlx.config.TherFlowConfig import TherFlowConfig


class Config(TherFlowConfig):
    def __init__(self, has_co2=False, has_steam=False, has_inh=False, has_ch4_in_liq=False, inh_diff_rate=None,
                 ch4_diff_rate=None,
                 support_ch4_hyd_diss=True, support_ch4_hyd_form=True, krf=None):
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
            liq.append(TherFlowConfig.FluProperty(den=2165.0, vis=0.001, specific_heat=4030.0))
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
            liq.append(TherFlowConfig.FluProperty(den=500.0, vis=0.001, specific_heat=1000.0))
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
            fa_t=self.flu_keys['temperature'], fa_c=self.flu_keys['specific_heat'],
            dissociation=support_ch4_hyd_diss, formation=support_ch4_hyd_form
        )
        # 抑制固体比例过高，增强计算稳定性 （非常必要）
        r['inhibitors'].append(create_dict(sol=self.components['sol'],
                                           liq=None,
                                           c=[0, 0.8, 1.0],
                                           t=[0, 0, -200.0]))
        if has_inh:
            # 抑制剂修改平衡温度
            r['inhibitors'].append(create_dict(sol=self.components['inh'],
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
            r['inhibitors'].append(create_dict(sol=self.components['sol'],
                            liq=None,
                            c=[0, 0.8, 1.0],
                            t=[0, 0, -200.0],))
            if has_inh:
                # 抑制剂修改平衡温度
                r['inhibitors'].append(create_dict(sol=self.components['inh'],
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
            cap = CapillaryEffect(i0, i1, s2p=([0, 1], [0, ch4_diff_rate]))
            self.diffusions.append(cap)

        # -------------------------------------------------------------
        if has_inh and inh_diff_rate is not None:
            # 添加水中盐度的扩散
            assert inh_diff_rate > 0
            i0 = self.components['inh']
            i1 = self.components['h2o']
            cap = CapillaryEffect(i0, i1, s2p=([0, 1], [0, inh_diff_rate]))
            self.diffusions.append(cap)

        if krf is None:
            self.krf = create_krf(as_interp=True)
        else:
            self.krf = krf


def create(*args, **kwargs):
    return Config(*args, **kwargs)


if __name__ == '__main__':
    c = create(True, True, True, True)
    print(c.components)
    print(c.flu_keys)
    print(c.cell_keys)
    print(c.face_keys)
    print(c.model_keys)
