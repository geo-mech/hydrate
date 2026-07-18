"""
第二阶段：溶解气体被动运移专用 create

本文件用于 He_sol / n2_sol / ch4_sol 的水相被动运移测试。

注意：
1. 不启用亨利定律；
2. 不启用脱溶反应；
3. 不调用 update_he_sol；
4. 不调用 update_n2_sol；
5. 不调用 update_ch4_sol；
6. 只把 he_sol / n2_sol / ch4_sol 当作水相被动组分。
"""

from zmlx.exts import Seepage
from zmlx.fluid.solution import create_solute
from zmlx.tfc import create as create_tfc
from zmlx import Interp2
from iapws import IAPWS97

def _vapor():
    """
    水蒸气，占位。
    第二阶段不考虑气相生成。
    """
    return Seepage.FluDef(name='vapor', den=30.0, vis=1.0e-5)


def _he():
    """
    气相 He，占位。
    第二阶段不发生 He 脱溶，因此该气相物性暂不控制结果。
    """
    return Seepage.FluDef(name='he', den=27.0, vis=2.2e-5)


def _n2():
    """
    气相 N2，占位。
    第二阶段不发生 N2 脱溶，因此该气相物性暂不控制结果。
    """
    return Seepage.FluDef(name='n2', den=195.0, vis=2.1e-5)


def _ch4():
    """
    气相 CH4，占位。
    第二阶段不发生 CH4 脱溶，因此该气相物性暂不控制结果。

    后续如果进入脱溶 / 气相运移阶段，应替换为更严格的
    压力-温度相关 CH4 物性。
    """
    return Seepage.FluDef(name='ch4', den=120.0, vis=1.5e-5)


def _h2o():
    """
    适用于当前地热模型的温压相关水物性。

    物性范围：
        压力：1～40 MPa
        温度：290～410 K

    密度和动力黏度由 IAPWS-IF97 计算，
    再转换成 ZMLX 使用的 Interp2 二维插值表。
    """

    # ------------------------------------------------------------
    # 1. 插值表范围
    # ------------------------------------------------------------
    p_min = 1.0e6       # Pa
    p_max = 40.0e6      # Pa
    dp = 0.5e6          # Pa，压力表格间隔

    t_min = 290.0       # K
    t_max = 420.0       # K
    dt = 1.0            # K，温度表格间隔

    # 缓存同一 P-T 状态，避免密度表和黏度表重复计算
    state_cache = {}

    def get_state(P, T):
        """
        P：ZMLX传入的压力，Pa
        T：ZMLX传入的温度，K
        """

        # 仅用于防止数值迭代过程中暂时超出插值表范围
        P = max(p_min, min(p_max, float(P)))
        T = max(t_min, min(t_max, float(T)))

        # IAPWS97压力单位是MPa
        key = (round(P, 3), round(T, 6))

        if key not in state_cache:
            state_cache[key] = IAPWS97(
                P=P / 1.0e6,
                T=T
            )

        return state_cache[key]

    def get_density(P, T):
        """
        水密度，kg/m3。
        """
        state = get_state(P, T)
        return float(state.rho)

    def get_viscosity(P, T):
        """
        水动力黏度，Pa·s。
        """
        state = get_state(P, T)
        return float(state.mu)

    # ------------------------------------------------------------
    # 2. 创建密度二维插值表
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # 3. 创建黏度二维插值表
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # 4. 返回水相定义
    # ------------------------------------------------------------
    return Seepage.FluDef(
        name='h2o',
        den=density_table,
        vis=viscosity_table,
        specific_heat=4200.0
    )


def _he_sol(h2o):
    """
    作为水相溶质的 He。
    这里不代表亨利定律溶解度，只是创建一个水相被动组分。
    """
    return create_solute(
        solvent=h2o,
        c=0.01,
        den_times=1.0,
        vis_times=1.0,
        name='he_sol'
    )


def _n2_sol(h2o):
    """
    作为水相溶质的 N2。
    这里不代表亨利定律溶解度，只是创建一个水相被动组分。
    """
    return create_solute(
        solvent=h2o,
        c=0.01,
        den_times=1.0,
        vis_times=1.0,
        name='n2_sol'
    )


def _ch4_sol(h2o):
    """
    作为水相溶质的 CH4。
    这里不代表亨利定律溶解度，只是创建一个水相被动组分。
    """
    return create_solute(
        solvent=h2o,
        c=0.01,
        den_times=1.0,
        vis_times=1.0,
        name='ch4_sol'
    )


def create_fludefs():
    """
    创建第二阶段被动运移所需流体定义。

    组分编号大致为：
    气相 gas:
        [0, 0] vapor
        [0, 1] he
        [0, 2] n2
        [0, 3] ch4

    液相 liq:
        [1, 0] h2o
        [1, 1] he_sol
        [1, 2] n2_sol
        [1, 3] ch4_sol
    """

    gas = Seepage.FluDef.create(
        name='gas',
        defs=[
            _vapor(),
            _he(),
            _n2(),
            _ch4()
        ]
    )

    h2o = _h2o()

    liq = Seepage.FluDef.create(
        name='liq',
        defs=[
            h2o,
            _he_sol(h2o),
            _n2_sol(h2o),
            _ch4_sol(h2o)
        ]
    )

    return [gas, liq]


def create(**opts) -> Seepage:
    """
    创建第二阶段被动运移模型。
    """

    default_opts = dict(
        fludefs=create_fludefs(),
        reactions=[]
    )

    default_opts.update(opts)

    model = create_tfc(**default_opts)

    return model

def test_geothermal_water_properties():
    """
    检查20 MPa下不同温度的水密度和黏度。
    """

    print("\n========== IAPWS水物性检查 ==========")

    pressure_mpa = 20.0

    for temperature in [300.0, 325.0, 350.0, 375.0, 400.0]:
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
if __name__ == '__main__':
        test_geothermal_water_properties()