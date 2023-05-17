# -*- coding: utf-8 -*-


from zml import *
from zmlx.react.alpha.salinity import data as salinity_c2t
from zmlx.fluid import *
from zmlx.kr.create_krf import create_krf
from zmlx.react import ch4_hydrate as ch4_hydrate_react
from zmlx.react import co2_hydrate as co2_hydrate_react
from zmlx.react import h2o_ice as icing_react
from zmlx.react import vapor as vapor_react
from zmlx.react import dissolution
from zmlx.utility.CapillaryEffect import CapillaryEffect


def create(has_co2=False, has_vapor=False, has_inh=False, has_ch4_in_liq=False, inh_diff_rate=None, ch4_diff_rate=None):
    """
    创建一个水合物的求解配置. 包含气<Id=0>、液<Id=1>和固<Id=2>三种相态;
    其中气体为：
        [Ch4, [Co2, Vapor]], 其中Co2只有当has_co2为True时存在，Vapor只有当has_vapor的时候存在;

    液体为:
        [H2o, [Inh], [ch4]]，其中Inh代表抑制剂，当has_inh参数为True的时候存在  ch4为溶解的甲烷气体

    固体为:
        [CH4_hyd, H2o_Ice, [Co2_Hyd]]. 其中Co2_Hyd只有当has_co2为True的时候存在

    化学反应为:
        Ch4水合物的形成/分解
        水/冰相互转化
        Ch4水合物的形成/分解 [当has_co2参数为True的时候]
        H2o/Vapor之间的相互转化 [当has_vapor参数为True的时候]
        Ch4在水中的溶解反应 [当has_ch4_in_liq为True的时候]
    """
    config = TherFlowConfig()

    # 添加默认的重力
    # since 2023-4-19
    config.gravity = (0, -10, 0)

    # 最后一种流体其实是固体，不参流体计算，因此，在流体计算的时候，把这个数据暂存一下
    config.has_solid = True

    # 配置气体的组分
    gas = [create_ch4(), ]
    if has_co2:
        # 添加CO2
        ico2 = len(gas)
        gas.append(create_co2())
    else:
        ico2 = None
    if has_vapor:
        # 添加蒸汽
        ivap = len(gas)
        gas.append(create_h2o_gas())
    else:
        ivap = None
    config.igas = config.add_fluid(gas)

    # 配置液体
    liq = [create_h2o(), ]
    if has_inh:
        # 添加盐度
        iinh = len(liq)
        # 这里，采用NaCl的密度和比热容
        liq.append(TherFlowConfig.FluProperty(den=2165.0, vis=0.001, specific_heat=4030.0))
    else:
        iinh = None
    if has_ch4_in_liq:
        ich4_in_liq = len(liq)
        add_keys(config.cell_keys, 'ch4_sol')
        liq.append(TherFlowConfig.FluProperty(den=500.0, vis=0.001, specific_heat=1000.0))
    else:
        ich4_in_liq = None
    config.iliq = config.add_fluid(liq)

    # 配置固体
    sol = [create_ch4_hydrate(), create_h2o_ice()]
    if has_co2:
        # 当有二氧化碳气体的时候，就有其水合物
        ico2_hyd = len(sol)
        sol.append(create_co2_hydrate())
    else:
        ico2_hyd = None
    config.isol = config.add_fluid(sol)

    # -------------------------------------------------------------
    # 添加甲烷水合物的相变
    r = ch4_hydrate_react.create(
        igas=(config.igas, 0),
        iwat=(config.iliq, 0),
        ihyd=(config.isol, 0),
        fa_t=config.flu_keys['temperature'],
        fa_c=config.flu_keys['specific_heat'])
    # 抑制固体比例过高，增强计算稳定性 （非常必要）
    r.add_inhibitor(sol=config.isol,
                    liq=None,
                    c=[0, 0.8, 1.0],
                    t=[0, 0, -200.0],
                    )
    if has_inh:
        # 抑制剂修改平衡温度
        r.add_inhibitor(sol=(config.iliq, 1),
                        liq=(config.iliq,),
                        c=salinity_c2t[0],
                        t=salinity_c2t[1])
    config.reactions.append(r)

    # -------------------------------------------------------------
    # 添加水和冰之间的相变
    config.reactions.append(
        icing_react.create(
            iflu=(config.iliq, 0),
            isol=(config.isol, 1),
            fa_t=config.flu_keys['temperature'],
            fa_c=config.flu_keys['specific_heat']))

    # -------------------------------------------------------------
    if has_co2:
        # 添加CO2和CO2水合物之间的相变<只要有了CO2，那么就要有水合物>
        assert ico2 is not None and ico2_hyd is not None
        r = co2_hydrate_react.create(
            igas=(config.igas, ico2),
            iwat=(config.iliq, 0),
            ihyd=(config.isol, ico2_hyd),
            fa_t=config.flu_keys['temperature'],
            fa_c=config.flu_keys['specific_heat'])
        if has_inh:
            # 抑制剂修改平衡温度
            r.add_inhibitor(sol=(config.iliq, 1),
                            liq=(config.iliq,),
                            c=salinity_c2t[0],
                            t=salinity_c2t[1])
        config.reactions.append(r)

    # -------------------------------------------------------------
    if has_vapor:
        # 添加水和水蒸气之间的相变反应
        # 2022-10-19
        assert ivap is not None
        config.reactions.append(
            vapor_react.create(
                ivap=(config.igas, ivap),
                iwat=(config.iliq, 0),
                fa_t=config.flu_keys['temperature'],
                fa_c=config.flu_keys['specific_heat']))

    # -------------------------------------------------------------
    if has_ch4_in_liq:
        config.reactions.append(
            dissolution.create(
                igas=(config.igas, 0),
                igas_in_liq=(config.iliq, ich4_in_liq),
                iliq=config.iliq,
                ca_sol=config.cell_keys['ch4_sol'],
                fa_c=config.flu_keys['specific_heat'],
                fa_t=config.flu_keys['temperature']))

    # -------------------------------------------------------------
    if has_ch4_in_liq and ch4_diff_rate is not None:
        # 添加水中溶解气的扩散
        assert ch4_diff_rate > 0
        i0 = (config.iliq, ich4_in_liq)
        i1 = (config.iliq, 0)
        cap = CapillaryEffect(i0, i1, s2p=([0, 1], [0, ch4_diff_rate]))
        config.diffusions.append(cap)

    # -------------------------------------------------------------
    if has_inh and inh_diff_rate is not None:
        # 添加水中盐度的扩散
        assert inh_diff_rate > 0
        i0 = (config.iliq, 1)
        i1 = (config.iliq, 0)
        cap = CapillaryEffect(i0, i1, s2p=([0, 1], [0, inh_diff_rate]))
        config.diffusions.append(cap)

    x, y = create_krf()
    config.krf = Interp1(x=x, y=y)
    return config


if __name__ == '__main__':
    c = create(True, True, True)
    print(c)
