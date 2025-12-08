import zmlx.alg.sys as warnings
from zmlx.base.zml import Seepage
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluid.co2 import create as create_co2
from zmlx.fluid.co2_hydrate import create as create_co2_hydrate
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.h2o_gas import create as create_h2o_gas
from zmlx.fluid.h2o_ice import create as create_h2o_ice
from zmlx.fluid.solution import create_solute


def create_fludefs(
        has_co2=False,
        has_steam=False,
        has_inh=False,
        has_ch4_in_liq=False,
        has_co2_in_liq=False,
        h2o_density=None,
        ch4_def=None,
        co2_def=None,
        h2o_def=None,
        inh_def=None,
        other_gas=None,
        other_liq=None,
        other_sol=None,
        co2_sol_data=None,
        ch4_sol_data=None,
        inh_sol_data=None,
):
    """
    创建水合物计算的时候的流体的定义(气体、液体和固体).
        当给定h2o_density的时候，h2o采用固定的密度.
        当给定co2的时候，将使用给定的定义.

    Args:
        has_co2: 是否需要创建co2
        has_steam: 是否需要创建h2o_gas
        has_inh: 是否需要创建inh
        has_ch4_in_liq: 是否需要创建ch4_in_liq
        has_co2_in_liq: 是否需要创建co2_in_liq
        h2o_density: h2o的密度（可选）
        ch4_def: ch4的定义（可选）
        co2_def: co2的定义（可选）
        h2o_def: h2o的定义（可选）
        inh_def: inh的定义（可选）
        other_gas: 其他所有的气体（可选）
        other_liq: 其他所有的液体（可选）
        other_sol: 其他所有的固体（可选）
        co2_sol_data: co2的溶解数据（可选）
        ch4_sol_data: ch4的溶解数据（可选）
        inh_sol_data: inh的溶解数据（可选）

    Returns:
        流体的定义(一个list)：
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
    else:  # 没有给定co2定义，根据has_co2判断是否需要创建co2
        assert co2_def is None
        if has_co2:
            co2_def = create_co2()

    # h2o
    if h2o_def is None:
        h2o_def = create_h2o(density=h2o_density)

    # inh
    if inh_def is not None or inh_sol_data is not None:
        if has_inh is not None:  # add warning since 2024-6-11
            if not has_inh:
                warnings.warn(
                    'Inhibitor data is provided when inhibitors are not needed')
        has_inh = True

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

    def create_solute_x(data):
        """
        创建一个“溶质”对象。
        Args:
            data: 一个列表，包含了浓度、密度变化和粘性变化（可选）。
                当只有浓度和密度变化时，默认粘性变化为1.0。

        Returns:
            Seepage.FluDef: “溶质”的流体定义
        """
        if data is None:
            return h2o_def
        if isinstance(data, dict):
            return create_solute(
                solvent=h2o_def, **data)
        else:
            assert len(data) == 2 or len(data) == 3
            return create_solute(
                solvent=h2o_def,
                c=data[0],
                den_times=data[1],
                vis_times=data[2] if len(data) == 3 else 1.0
            )

    # 2  液体:
    liq = Seepage.FluDef(name='liq')
    liq.add_component(h2o_def, name='h2o')

    if has_inh:
        if inh_sol_data is not None:
            liq.add_component(create_solute_x(inh_sol_data), name='inh')
        else:
            warnings.warn('The dissolved salinity data is not defined')
            if inh_def is None:
                inh_def = Seepage.FluDef(
                    den=2165.0,
                    vis=0.001,
                    specific_heat=4030.0)
            liq.add_component(inh_def, name='inh')

    if has_ch4_in_liq:
        if ch4_sol_data is not None:
            liq.add_component(create_solute_x(ch4_sol_data), name='ch4_in_liq')
        else:
            warnings.warn('The dissolved ch4 data is not defined')
            liq.add_component(ch4_def, name='ch4_in_liq')

    if has_co2_in_liq:
        assert has_co2
        if co2_sol_data is not None:
            liq.add_component(create_solute_x(co2_sol_data), name='co2_in_liq')
        else:
            warnings.warn('The dissolved co2 data is not defined')
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
