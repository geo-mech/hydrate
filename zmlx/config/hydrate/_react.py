from zmlx.react import ch4_hydrate as ch4_hydrate_react
from zmlx.react import co2_hydrate as co2_hydrate_react
from zmlx.react import dissolution
from zmlx.react import h2o_ice as icing_react
from zmlx.react import vapor as vapor_react
from zmlx.react.alpha.salinity import data as salinity_c2t
from zmlx.react.inh import add_inh


def create_reactions(
        has_co2=False,
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
    r = ch4_hydrate_react.create(
        gas='ch4', wat='h2o', hyd='ch4_hydrate',
        dissociation=support_ch4_hyd_diss,
        formation=support_ch4_hyd_form
    )
    # 抑制固体比例过高，增强计算稳定性 （非常必要）
    assert -5.0 <= sol_dt <= 0.0
    add_inh(r, sol='sol', liq=None,
            c2t=[[0, 0.8, 1.0], [0, sol_dt, -200.0]],
            use_vol=True)
    if has_inh:
        add_inh(r, sol='inh', liq='liq', c2t=salinity_c2t)
    result.append(r)

    # 添加冰的相变
    result.append(icing_react.create(
        flu='h2o', sol='h2o_ice'))

    if has_co2:
        # 添加co2和co2水合物之间的相变
        r = co2_hydrate_react.create(
            gas='co2', wat='h2o',
            hyd='co2_hydrate')
        # 抑制固体比例过高，增强计算稳定性 （非常必要）
        add_inh(r, sol='sol', liq=None,
                c2t=[[0, 0.8, 1.0], [0, sol_dt, -200.0]], use_vol=True)
        if has_inh:
            add_inh(r, sol='inh', liq='liq', c2t=salinity_c2t)
        result.append(r)

    if has_steam:
        # 添加水和水蒸气之间的相变反应
        # 2022-10-19
        result.append(vapor_react.create(
            vap='h2o_gas',
            wat='h2o'))

    if has_ch4_in_liq:
        result.append(dissolution.create(
            sol='ch4', sol_in_liq='ch4_in_liq',
            liq='liq', ca_sol='n_ch4_sol'))

    if has_co2_in_liq:
        result.append(dissolution.create(
            sol='co2', sol_in_liq='co2_in_liq',
            liq='liq', ca_sol='n_co2_sol'))

    # 其它的反应
    if others is not None:
        for item in others:
            result.append(item)

    return result
