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


def create(has_co2=False, has_steam=False, has_inh=False, has_ch4_in_liq=False, inh_diff_rate=None, ch4_diff_rate=None):
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
    if has_steam:
        # 添加蒸汽
        isteam = len(gas)
        gas.append(create_h2o_gas())
    else:
        isteam = None
    igas = config.add_fluid(gas)
    config.igas = igas

    config.components['gas'] = igas
    config.components['ch4'] = [igas, 0]
    if ico2 is not None:
        config.components['co2'] = [igas, ico2]
    if isteam is not None:
        config.components['h2o_gas'] = [igas, isteam]

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
    iliq = config.add_fluid(liq)
    config.iliq = iliq
    config.components['liq'] = iliq
    config.components['h2o'] = [iliq, 0]
    if iinh is not None:
        config.components['inh'] = [iliq, iinh]
    if ich4_in_liq is not None:
        config.components['ch4_in_liq'] = [iliq, ich4_in_liq]

    # 配置固体
    sol = [create_ch4_hydrate(), create_h2o_ice()]
    if has_co2:
        # 当有二氧化碳气体的时候，就有其水合物
        ico2_hyd = len(sol)
        sol.append(create_co2_hydrate())
    else:
        ico2_hyd = None
    isol = config.add_fluid(sol)
    config.isol = isol
    config.components['sol'] = isol
    config.components['ch4_hydrate'] = [isol, 0]
    config.components['h2o_ice'] = [isol, 1]
    if ico2_hyd is not None:
        config.components['co2_hydrate'] = [isol, ico2_hyd]

    # -------------------------------------------------------------
    # 添加甲烷水合物的相变
    r = ch4_hydrate_react.create(
        igas=config.components['ch4'],
        iwat=config.components['h2o'],
        ihyd=config.components['ch4_hydrate'],
        fa_t=config.flu_keys['temperature'],
        fa_c=config.flu_keys['specific_heat'])
    # 抑制固体比例过高，增强计算稳定性 （非常必要）
    r.add_inhibitor(sol=config.components['sol'],
                    liq=None,
                    c=[0, 0.8, 1.0],
                    t=[0, 0, -200.0],
                    )
    if has_inh:
        # 抑制剂修改平衡温度
        r.add_inhibitor(sol=config.components['inh'],
                        liq=config.components['liq'],
                        c=salinity_c2t[0],
                        t=salinity_c2t[1])
    config.reactions.append(r)

    # -------------------------------------------------------------
    # 添加水和冰之间的相变
    config.reactions.append(
        icing_react.create(
            iflu=config.components['h2o'],
            isol=config.components['h2o_ice'],
            fa_t=config.flu_keys['temperature'],
            fa_c=config.flu_keys['specific_heat']))

    # -------------------------------------------------------------
    if has_co2:
        # 添加CO2和CO2水合物之间的相变<只要有了CO2，那么就要有水合物>
        assert ico2 is not None and ico2_hyd is not None
        r = co2_hydrate_react.create(
            igas=config.components['co2'],
            iwat=config.components['h2o'],
            ihyd=config.components['co2_hydrate'],
            fa_t=config.flu_keys['temperature'],
            fa_c=config.flu_keys['specific_heat'])
        if has_inh:
            # 抑制剂修改平衡温度
            r.add_inhibitor(sol=config.components['inh'],
                            liq=config.components['liq'],
                            c=salinity_c2t[0],
                            t=salinity_c2t[1])
        config.reactions.append(r)

    # -------------------------------------------------------------
    if has_steam:
        # 添加水和水蒸气之间的相变反应
        # 2022-10-19
        assert isteam is not None
        config.reactions.append(
            vapor_react.create(
                ivap=config.components['h2o_gas'],
                iwat=config.components['h2o'],
                fa_t=config.flu_keys['temperature'],
                fa_c=config.flu_keys['specific_heat']))

    # -------------------------------------------------------------
    if has_ch4_in_liq:
        config.reactions.append(
            dissolution.create(
                igas=config.components['ch4'],
                igas_in_liq=config.components['ch4_in_liq'],
                iliq=config.components['liq'],
                ca_sol=config.cell_keys['ch4_sol'],
                fa_c=config.flu_keys['specific_heat'],
                fa_t=config.flu_keys['temperature']))

    # -------------------------------------------------------------
    if has_ch4_in_liq and ch4_diff_rate is not None:
        # 添加水中溶解气的扩散
        assert ch4_diff_rate > 0
        i0 = config.components['ch4_in_liq']
        i1 = config.components['h2o']
        cap = CapillaryEffect(i0, i1, s2p=([0, 1], [0, ch4_diff_rate]))
        config.diffusions.append(cap)

    # -------------------------------------------------------------
    if has_inh and inh_diff_rate is not None:
        # 添加水中盐度的扩散
        assert inh_diff_rate > 0
        i0 = config.components['inh']
        i1 = config.components['h2o']
        cap = CapillaryEffect(i0, i1, s2p=([0, 1], [0, inh_diff_rate]))
        config.diffusions.append(cap)

    x, y = create_krf()
    config.krf = Interp1(x=x, y=y)
    return config


if __name__ == '__main__':
    c = create(True, True, True, True)
    print(c.components)
    print(c.flu_keys)
    print(c.cell_keys)
    print(c.face_keys)
    print(c.model_keys)

