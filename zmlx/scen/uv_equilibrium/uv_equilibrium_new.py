"""
气–水两相体系的固定体积–内能（UV）平衡模块。
"""
from time import perf_counter
from typing import Optional, List
import numpy as np
import reaktoro as rtk

class GasWaterUVEquilibrium:
    def __init__(self, gas_names: Optional[List[str]] = None):
        """
        初始化并导入数据库
        Args:
            gas_names (Optional[List[str]], optional): 气体名称列表。 Defaults to None.
                在内部，利用后缀(g)代表气体、(aq)代表水相。
        """
        if gas_names is None:
            gas_names = ['CH4', 'N2', 'He']

        db = rtk.SupcrtDatabase("supcrtbl-organics")
        # 按 gas_names 同时生成水相和气相物种，便于后续扩展新气体时只改输入列表。
        gases = rtk.GaseousPhase(" ".join(['H2O(g)', *(f'{name}(g)' for name in gas_names)]))
        aqueous = rtk.AqueousPhase(" ".join(['H2O(aq)', *(f'{name}(aq)' for name in gas_names)]))
        # 对外输入/输出顺序固定在 self.names；dict 不依赖顺序，list 必须按这个顺序。
        self.names = [ 'H2O(g)',*(f'{name}(g)' for name in gas_names),
                       'H2O(aq)', *(f'{name}(aq)' for name in gas_names),]
        self.system = rtk.ChemicalSystem(db, gases, aqueous)
        # Reaktoro 的系统物种顺序可能和 self.names 不同，因此单独保存 system_names 用于 setSpeciesAmounts。
        self.system_names = [sp.name() for sp in self.system.species()]
        self.molar_mass = {sp.name(): float(sp.molarMass()) for sp in self.system.species()}
        self.specs = rtk.EquilibriumSpecs(self.system)
        self.specs.volume()
        self.specs.internalEnergy()
        self.solver = rtk.EquilibriumSolver(self.specs)
        opts = rtk.EquilibriumOptions()
        opts.epsilon = 1.0e-30
        self.solver.setOptions(opts)
        self.conditions = rtk.EquilibriumConditions(self.specs)
        self.conditions.setLowerBoundTemperature(273.15, "K")
        self.conditions.setUpperBoundTemperature(1273, "K")
        self.conditions.setLowerBoundPressure(0.1, "MPa")
        self.conditions.setUpperBoundPressure(400.0, "MPa")  # 官方数据范围

        # 运行的状态的统计，调用了多少次、耗时多少、多少次成功或者失败，保证效率
        # 这些统计量不参与计算，只用于调试收敛表现和定位 warning cell。
        self.calls = 0
        self.successes = 0
        self.failures = 0
        self.elapsed = 0.0

        # 初始化之后，就要知道各个组分的序号
        # 什么状态改变了，导致有点地方没有错误，有的时候有错误？
        # 缓存本次成功平衡后的温度和压力，供外部网格循环立即读取并写回 cell。
        self.last_temperature = None
        self.last_pressure = None

        # 初始化之后，存储摩尔质量的np数组，后续就可以向量化计算质量
        # 当前只保留 molar_mass 字典，用于输入质量 kg 到物质的量 mol 的换算。

    def get_next_state(self, temperature, pressure, masses):
        """
        计算气-水体系UV平衡状态.

        后续，能否支持对各cell的数据同时处理(未实现)
        Args:
            temperature (float): 温度（开尔文）
            pressure (float): 压力（帕）
            masses (dict): 物种质量（千克）  支持字典和列表输入（列表输入更加高效）
                列表的种类的顺序是：气态的各个组分+水的各个的组分
        Returns: 最终平衡状态（千克）
        """

        # 归一化物种质量
        # dict 输入按物种名取值；list/array 输入直接按 self.names 顺序解释。
        is_dict = isinstance(masses, dict)
        input_masses = np.array([masses.get(name, 0.0) for name in self.names], dtype=float) if is_dict else np.array(
            masses, dtype=float)
        mass_by_name = dict(zip(self.names, input_masses))
        # Reaktoro 的 setSpeciesAmounts 接受 mol，不接受 kg；极小正值用于避免零物质量导致的数值问题。
        amounts = np.array(
            [max(mass_by_name.get(name, 0.0), 1.0e-30) / self.molar_mass[name] for name in self.system_names])
        state = rtk.ChemicalState(self.system)
        state.temperature(temperature, "K")
        state.pressure(pressure, "Pa")

        state.setSpeciesAmounts(amounts)
        props = rtk.ChemicalProps(state)
        # 先用初始 T/P/组成计算 V0 和 U0，再把它们作为 UV 平衡约束。
        self.conditions.volume(props.volume())
        self.conditions.internalEnergy(props.internalEnergy())
        self.calls += 1
        t0 = perf_counter()
        result = self.solver.solve(state, self.conditions)
        self.elapsed += perf_counter() - t0
        if result.failed():
            self.failures += 1
            return None

        # 返回最终平衡状态   # 返回温度(需要返回给cell)
        self.successes += 1
        self.last_temperature = float(state.temperature())
        self.last_pressure = float(state.pressure())

        # 返回和输入保持同样的格式。如果输入的是dict，返回也是dict；输入的是list，返回也是list
        # speciesMass(name) 直接返回 kg
        values = [float(state.speciesMass(name)) for name in self.names]
        if is_dict:
            return {name: values[i] for i, name in enumerate(self.names)}
        return values
