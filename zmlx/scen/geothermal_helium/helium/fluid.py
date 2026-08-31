# -*- coding: utf-8 -*-

"""
溶解态氦气被动运移专用流体定义。


模型中的流体结构：

    气相 gas：
        vapor       水蒸气占位组分

    液相 liq：
        h2o         水
        he_sol      溶解态氦气
"""

from zmlx.exts import Seepage
from zmlx.fluid.solution import create_solute
from zmlx.tfc import create as create_tfc
from zmlx import Interp2
from iapws import IAPWS97


def _vapor():
    """
    气相占位组分。

    当前模型不考虑水蒸气生成，也不考虑任何气体脱溶。
    保留该组分只是为了维持模型的气相结构。
    """

    return Seepage.FluDef(
        name="vapor",
        den=30.0,
        vis=1.0e-5
    )


def _h2o():
    """
    创建适用于当前地热模型的温压相关水物性。

    物性计算范围
    ----------
    压力：
        1～40 MPa

    温度：
        290～420 K

    水密度和动力黏度通过 IAPWS-IF97 计算，
    然后转换为 ZMLX 使用的 Interp2 二维插值表。
    """

    # ========================================================
    # 1. 插值表范围
    # ========================================================

    p_min = 1.0e6       # Pa
    p_max = 40.0e6      # Pa
    dp = 0.5e6          # Pa

    t_min = 290.0       # K
    t_max = 420.0       # K
    dt = 1.0            # K

    # 缓存相同的压力—温度状态，避免密度和黏度重复计算
    state_cache = {}

    def get_state(P, T):
        """
        根据压力和温度返回 IAPWS97 状态。

        参数
        ----------
        P:
            ZMLX传入的压力，单位Pa。

        T:
            ZMLX传入的温度，单位K。
        """

        # 防止数值迭代过程中短暂超出物性表范围
        P = max(p_min, min(p_max, float(P)))
        T = max(t_min, min(t_max, float(T)))

        # IAPWS97的压力单位为MPa
        key = (
            round(P, 3),
            round(T, 6)
        )

        if key not in state_cache:
            state_cache[key] = IAPWS97(
                P=P / 1.0e6,
                T=T
            )

        return state_cache[key]

    def get_density(P, T):
        """
        返回水密度，单位kg/m3。
        """

        state = get_state(P, T)
        return float(state.rho)

    def get_viscosity(P, T):
        """
        返回水动力黏度，单位Pa·s。
        """

        state = get_state(P, T)
        return float(state.mu)

    # ========================================================
    # 2. 创建密度二维插值表
    # ========================================================

    density_table = Interp2()

    density_table.create(
        p_min,
        dp,
        p_max,
        t_min,
        dt,
        t_max,
        get_density
    )

    # ========================================================
    # 3. 创建黏度二维插值表
    # ========================================================

    viscosity_table = Interp2()

    viscosity_table.create(
        p_min,
        dp,
        p_max,
        t_min,
        dt,
        t_max,
        get_viscosity
    )

    # ========================================================
    # 4. 返回水相定义
    # ========================================================

    return Seepage.FluDef(
        name="h2o",
        den=density_table,
        vis=viscosity_table,
        specific_heat=4200.0
    )


def _he_sol(h2o):
    """
    创建水相中的溶解态氦气组分。

    这里的 he_sol 只是一个被动溶质，不表示：
    1. 亨利定律溶解度；
    2. 气液平衡；
    3. 氦气脱溶；
    4. 气泡生成；
    5. 独立气相流动。

    he_sol 将随水相进行对流运移。
    """

    return create_solute(
        solvent=h2o,

        # create_solute所需的参考浓度参数。
        # 储层实际初始含量仍由主程序中的get_s决定。
        c=0.01,

        # 暂时不考虑溶解态氦气对液相密度的影响
        den_times=1.0,

        # 暂时不考虑溶解态氦气对液相黏度的影响
        vis_times=1.0,

        name="he_sol"
    )


def create_fludefs():
    """
    创建仅包含水和溶解态氦气的流体定义。

    组分编号大致为：

    气相 gas：
        [0, 0] vapor

    液相 liq：
        [1, 0] h2o
        [1, 1] he_sol
    """

    # 气相仅保留水蒸气占位组分
    gas = Seepage.FluDef.create(
        name="gas",
        defs=[
            _vapor(),
        ]
    )

    # 创建水相
    h2o = _h2o()

    # 液相只包含水和溶解态氦气
    liq = Seepage.FluDef.create(
        name="liq",
        defs=[
            h2o,
            _he_sol(h2o),
        ]
    )

    return [gas, liq]


def create(**opts) -> Seepage:
    """
    创建水—溶解态氦气被动运移模型。

    模型不包含任何化学反应和脱溶反应。
    """

    default_opts = {
        "fludefs": create_fludefs(),
        "reactions": [],
    }

    default_opts.update(opts)

    model = create_tfc(**default_opts)

    return model


def test_geothermal_water_properties():
    """
    检查20 MPa条件下，不同温度对应的水密度和动力黏度。
    """

    print("\n========== IAPWS水物性检查 ==========")

    pressure_mpa = 20.0

    for temperature in [
        300.0,
        325.0,
        350.0,
        375.0,
        400.0,
    ]:
        state = IAPWS97(
            P=pressure_mpa,
            T=temperature
        )

        print(
            f"P = {pressure_mpa:6.2f} MPa, "
            f"T = {temperature:7.2f} K, "
            f"rho = {state.rho:10.4f} kg/m3, "
            f"mu = {state.mu:.6e} Pa·s"
        )

    print("=====================================\n")


if __name__ == "__main__":
    test_geothermal_water_properties()