# 气-水体系UV平衡计算模块
# 【用途与适用范围】
# 1. 本模块面向含水地层单元或封闭局部体系中 N2、CH4、He 与 H2O 的气-水两相平衡重分配计算(可在模块扩展其他气体)。
#    给定初始温压及气/水相物种的质量后，模块先计算初始体系总体积 V0 和总内能 U0，随后在 V=V0、U=U0 的约束下求解最终平衡状态。
# 2. 本模块不包含反应动力学、传质速率、扩散速率或界面传质系数；求解结果代表指定 V–U 约束下的瞬时热力学平衡，而不是显式的溶解/脱溶速率。
#
# 【物种与相定义】
# 水相：H2O(aq)、CH4(aq)、N2(aq)、He(aq)
# 气相：H2O(g)、CH4(g)、N2(g)、He(g)
# 输入字典的键名必须与上述 Reaktoro 物种名称完全一致；未提供的按 0.0 kg 处理。
#
# 【单位约定】
# temperature : K（开尔文）
# pressure    : Pa（帕）
# masses      : kg（千克）
# 返回值      : kg（千克）
#
# 【温压适用边界】
# 当前平衡求解器设置的温度边界为 275–500 K，压力边界为 0.1–100 MPa。
#
# 【当前测试误差情况】
# 在的 6000 个网格单元测试中，单次平衡更新出现 1–9 个 warning cells，即 0.02%–0.15%。
# 这表示少量局部单元的 Reaktoro UV 平衡未在该次调用中收敛，未收敛将跳过该单元本次质量更新；
# 该单元保留本次调用前的组分质量。因此，这些单元可能产生局部暂时的平衡滞后。
#
# 【调用格式】
# eq = GasWaterUVEquilibrium()
# result = eq.get_next_state(
#     temperature=320.0,            # K
#     pressure=10.0e6,              # Pa
#     masses={                      # kg
#         'H2O(aq)': 1000.0,
#         'CH4(aq)': 0.0, 'N2(aq)': 0.0, 'He(aq)': 0.0,
#         'H2O(g)': 0.0,
#         'CH4(g)': 100.0, 'N2(g)': 100.0, 'He(g)': 10.0,
#     },
# )

"""

"""
from typing import Optional, List

import reaktoro as rtk


class GasWaterUVEquilibrium:
    """
    气体溶解计算模块
    """

    def __init__(self, gas_names: Optional[List[str]] = None):
        """
        初始化并导入数据库
        Args:
            gas_names (Optional[List[str]], optional): 气体名称列表。 Defaults to None.
                在内部，利用后缀(g)代表气体、(aq)代表水相。


        注意：
            支持的类型：

        """
        if gas_names is None:
            # 需要对输入的参数作检查，比如是否重复，大小写，是否包含在我们允许的库中

            gas_names = ['CH4', 'N2', 'He', 'H2']

        db = rtk.SupcrtDatabase("supcrtbl-organics")
        aqueous = rtk.AqueousPhase("H2O(aq) CH4(aq) N2(aq) He(aq)")
        gases = rtk.GaseousPhase("H2O(g) CH4(g) N2(g) He(g)")
        self.names = ['H2O(aq)', 'CH4(aq)', 'N2(aq)', 'He(aq)', 'H2O(g)', 'CH4(g)', 'N2(g)', 'He(g)']
        self.system = rtk.ChemicalSystem(db, gases, aqueous)
        self.molar_mass = {sp.name(): float(sp.molarMass()) for sp in self.system.species()}
        self.specs = rtk.EquilibriumSpecs(self.system)
        self.specs.volume()
        self.specs.internalEnergy()
        self.solver = rtk.EquilibriumSolver(self.specs)
        opts = rtk.EquilibriumOptions()
        opts.epsilon = 1.0e-30
        self.solver.setOptions(opts)
        self.conditions = rtk.EquilibriumConditions(self.specs)
        self.conditions.setLowerBoundTemperature(275, "K")
        self.conditions.setUpperBoundTemperature(500.0, "K")
        self.conditions.setLowerBoundPressure(0.1, "MPa")
        self.conditions.setUpperBoundPressure(100.0, "MPa")  # 范围

        # 机理运行的状态的统计，调用了多少次、耗时多少、多少次成功或者失败，保证效率

        # 初始化之后，就要知道各个组分的序号
        self.indexes = {
            "ch3": 0
        }

        # 什么状态改变了，导致有点地方没有错误，有的时候有错误？

        # 初始化之后，存储摩尔质量的np数组，后续就可以先量化计算质量

    def get_next_state(self, temperature, pressure, masses):
        """
        计算气-水体系UV平衡状态.

        后续，能否支持对各cell的数据同时处理
        Args:
            temperature (float): 温度（开尔文）
            pressure (float): 压力（帕）
            masses (dict): 物种质量（千克）  支持字典和列表输入（列表输入更加高效）
                列表的种类的顺序是：气态的各个组分+水的各个的组分
        Returns: 最终平衡状态（千克）
        """

        # 归一化物种质量
        assert isinstance(masses, dict)
        state = rtk.ChemicalState(self.system)
        state.temperature(temperature, "K")
        state.pressure(pressure, "Pa")

        # 最终，要使用setSpeciesAmounts来设置质量
        for name in self.names:   # 最好是直接设置对应index的物质的质量    输入参数的检查，并且明显问题的时候报错
            index = self.indexes.get(name)  ##??
            state.set(name, max(1.0e-30, masses.get(name, 0.0)), "kg")
        props = rtk.ChemicalProps(state)
        self.conditions.volume(props.volume())
        self.conditions.internalEnergy(props.internalEnergy())
        result = self.solver.solve(state, self.conditions)
        if hasattr(result, "succeeded") and not result.succeeded():
            return None

        # 返回最终平衡状态   # 返回温度(需要返回给cell)

        # 返回和输入保持同样的格式。如果输入的是dict，返回也是dict；输入的是list，返回也是list

        # 是否存在向量化的返回语句？  speciesAmounts?
        return {name: float(state.speciesMass(name)) for name in self.names}
