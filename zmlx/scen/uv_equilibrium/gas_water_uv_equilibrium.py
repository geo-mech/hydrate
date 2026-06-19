# -*- coding: utf-8 -*-
"""
gas_water_uv_equilibrium.py

基于 Reaktoro 的气-水平衡 UV 计算类。

用途
----
给定初始温度、压力，以及水相 / 气相中各气体的质量，计算刚性、绝热、
封闭体系中的气-水平衡。数学上对应固定体积 V 和固定内能 U 的平衡问题：

    V = V0
    U = U0

其中 V0 和 U0 默认由初始 ChemicalState 计算得到；也可以由外部传入固定体积，
用于和网格模型中的孔隙体积耦合。

外部单位约定
------------
温度：K
压力：Pa
质量：kg
体积：m3
"""

from reaktoro import *


class GasWaterUVEquilibrium:
    """
    气-水溶解 / 脱溶平衡计算器。

    特点：
    1. 数据库、化学系统、平衡约束、求解器只初始化一次；
    2. 单网格只需调用 solve；
    3. 外部输入输出均为 kg、K、Pa、m3；
    4. 支持 He、N2、H2、CH4、CO2 等气体；
    5. 若 CH4(aq) 在 supcrtbl 中缺失，可自动切换到 supcrtbl-organics。
    """

    def __init__(
        self,
        database_name="supcrtbl",
        gas_components=("He", "N2"),
        extra_aqueous_species=None,
        mineral_species=None,
        include_water_vapor=True,
        epsilon=1.0e-30,
        auto_use_organics=True,
        component_species=None,
    ):
        """
        初始化计算器。

        Parameters
        ----------
        database_name : str
            请求使用的 SUPCRT 数据库名称。常用："supcrtbl" 或 "supcrtbl-organics"。
        gas_components : tuple[str]
            需要考虑的气体组分，例如 ("He", "N2", "H2", "CH4", "CO2")。
        extra_aqueous_species : list[str] | None
            额外水相物种，例如 ["Na+", "Cl-"]。
        mineral_species : list[str] | None
            可选矿物，例如 ["Calcite", "Quartz"]。
            第一版建议不启用矿物，以免引入瞬时矿物平衡。
        include_water_vapor : bool
            是否在气相中加入 H2O(g)。
        epsilon : float | None
            平衡求解时的物种量下限。痕量气体建议取较小值。
        auto_use_organics : bool
            当 database_name="supcrtbl" 且某些有机物种缺失时，是否自动尝试
            database_name="supcrtbl-organics"。为保证 CH4(aq) 可用，建议保持 True。
        component_species : dict | None
            自定义组分到 Reaktoro 物种名的映射。一般无需传入。
            示例：
            {
                "CH4": {"aq": "CH4(aq)", "gas": "CH4(g)"},
                "He":  {"aq": "He(aq)",  "gas": "He(g)"}
            }
        """

        self.requested_database_name = database_name
        self.gas_components = tuple(gas_components)
        self.extra_aqueous_species = list(extra_aqueous_species or [])
        self.mineral_species = list(mineral_species or [])
        self.include_water_vapor = bool(include_water_vapor)
        self.epsilon = epsilon
        self.auto_use_organics = bool(auto_use_organics)
        self.component_species = component_species or {}

        # 尝试数据库顺序。
        # 当用户请求 supcrtbl 但其中缺少 CH4(aq) 等有机水相物种时，自动尝试 supcrtbl-organics。
        database_candidates = [database_name]
        if auto_use_organics and database_name == "supcrtbl":
            database_candidates.append("supcrtbl-organics")

        errors = {}
        for db_name in database_candidates:
            try:
                self._build_backend(db_name)
                self.database_name = db_name
                self.database_used = db_name
                self.fallback_errors = errors
                break
            except Exception as exc:
                errors[db_name] = str(exc)
        else:
            message = ["无法初始化 GasWaterUVEquilibrium。已尝试数据库："]
            for db_name, err in errors.items():
                message.append(f"  - {db_name}: {err.splitlines()[0]}")
            message.append("建议：若需要 CH4(aq)，请使用 database_name='supcrtbl-organics'。")
            raise RuntimeError("\n".join(message))

    def _build_backend(self, database_name):
        """
        构建 Reaktoro 数据库、相、化学系统、UV 约束和求解器。
        该函数若失败，会由 __init__ 捕获，并尝试下一个数据库。
        """

        # 1. 读取数据库。
        db = SupcrtDatabase(database_name)

        # 2. 构建水相 / 气相物种名映射。
        water_aq = "H2O(aq)"
        water_gas = "H2O(g)"

        aq_gas_species = {}
        gas_species = {}
        for comp in self.gas_components:
            custom = self.component_species.get(comp, {})
            aq_gas_species[comp] = custom.get("aq", f"{comp}(aq)")
            gas_species[comp] = custom.get("gas", f"{comp}(g)")

        # 3. 定义水相和气相。
        aq_species = [water_aq] + list(aq_gas_species.values()) + self.extra_aqueous_species
        gas_phase_species = list(gas_species.values())
        if self.include_water_vapor:
            gas_phase_species = [water_gas] + gas_phase_species

        aqueous = AqueousPhase(" ".join(aq_species))
        gases = GaseousPhase(" ".join(gas_phase_species))

        phases = [gases, aqueous]
        if self.mineral_species:
            minerals = MineralPhases(" ".join(self.mineral_species))
            phases.append(minerals)
        else:
            minerals = None

        # 4. 创建化学系统。若某个物种不存在，此处通常会抛出异常。
        system = ChemicalSystem(db, *phases)

        # 5. 创建固定体积、固定内能平衡约束。
        specs = EquilibriumSpecs(system)
        specs.volume()
        specs.internalEnergy()

        solver = EquilibriumSolver(specs)
        if self.epsilon is not None:
            options = EquilibriumOptions()
            options.epsilon = self.epsilon
            solver.setOptions(options)

        # 6. 缓存系统信息。
        species_names = [sp.name() for sp in system.species()]
        species_index = {name: i for i, name in enumerate(species_names)}
        molar_mass = {sp.name(): float(sp.molarMass()) for sp in system.species()}  # kg/mol

        # 7. 全部成功后再写入 self，避免失败时留下半初始化状态。
        self.db = db
        self.water_aq = water_aq
        self.water_gas = water_gas
        self.aq_gas_species = aq_gas_species
        self.gas_species = gas_species
        self.aqueous = aqueous
        self.gases = gases
        self.minerals = minerals
        self.system = system
        self.specs = specs
        self.solver = solver
        self.species_names = species_names
        self.species_index = species_index
        self.molar_mass = molar_mass

    def solve(
        self,
        temperature_K,
        pressure_Pa,
        water_kg,
        aq_gas_kg=None,
        gas_kg=None,
        extra_aqueous_kg=None,
        minerals_kg=None,
        fixed_volume_m3=None,
        temperature_bounds_K=(250.0, 500.0),
        pressure_bounds_Pa=(1.0e5, 1.0e8),
    ):
        """
        求解单个网格或单个封闭体系中的气-水平衡。

        Parameters
        ----------
        temperature_K : float
            初始温度，K。
        pressure_Pa : float
            初始压力，Pa。
        water_kg : float
            初始液态水质量，kg，赋给 H2O(aq)。
        aq_gas_kg : dict[str, float]
            初始溶解态气体质量，kg，例如 {"He": 1e-9, "CH4": 1e-5}。
        gas_kg : dict[str, float]
            初始游离气体质量，kg，例如 {"He": 1e-9, "CH4": 1e-4}。
        extra_aqueous_kg : dict[str, float]
            额外水相物种质量，kg，例如 {"Na+": 1e-3, "Cl-": 1e-3}。
        minerals_kg : dict[str, float]
            矿物质量，kg，例如 {"Calcite": 1e-3}。
        fixed_volume_m3 : float | None
            固定体积，m3。若为 None，则由初始状态计算 V0。
            若接入网格模型，建议传入孔隙体积。
        temperature_bounds_K : tuple[float, float]
            平衡求解温度上下限，K。
        pressure_bounds_Pa : tuple[float, float]
            平衡求解压力上下限，Pa。

        Returns
        -------
        dict
            平衡结果和诊断信息。
        """

        aq_gas_kg = aq_gas_kg or {}
        gas_kg = gas_kg or {}
        extra_aqueous_kg = extra_aqueous_kg or {}
        minerals_kg = minerals_kg or {}

        # 1. 构造初始状态。
        state0 = ChemicalState(self.system)
        state0.temperature(float(temperature_K), "K")
        state0.pressure(float(pressure_Pa), "Pa")

        self._set_mass_kg(state0, self.water_aq, water_kg)

        for comp, mass in aq_gas_kg.items():
            self._check_component(comp)
            self._set_mass_kg(state0, self.aq_gas_species[comp], mass)

        for comp, mass in gas_kg.items():
            self._check_component(comp)
            self._set_mass_kg(state0, self.gas_species[comp], mass)

        for species, mass in extra_aqueous_kg.items():
            self._set_mass_kg(state0, species, mass)

        for species, mass in minerals_kg.items():
            self._set_mass_kg(state0, species, mass)

        # 2. 初始体积和内能。
        props0 = ChemicalProps(state0)
        V0 = float(props0.volume()) if fixed_volume_m3 is None else float(fixed_volume_m3)
        U0 = float(props0.internalEnergy())

        # 3. 设置 UV 条件。
        conditions = EquilibriumConditions(self.specs)
        conditions.volume(V0)
        conditions.internalEnergy(U0)
        conditions.setLowerBoundTemperature(float(temperature_bounds_K[0]), "K")
        conditions.setUpperBoundTemperature(float(temperature_bounds_K[1]), "K")
        conditions.setLowerBoundPressure(float(pressure_bounds_Pa[0]), "Pa")
        conditions.setUpperBoundPressure(float(pressure_bounds_Pa[1]), "Pa")

        # 4. 求解平衡。
        state = ChemicalState(state0)
        try:
            self.solver.solve(state, conditions)
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "database_used": self.database_used,
                "temperature_K": None,
                "pressure_Pa": None,
                "aq_gas_kg": None,
                "gas_kg": None,
                "diagnostics": {"V0_m3": V0, "U0_J": U0},
            }

        # 5. 输出结果。
        props = ChemicalProps(state)
        all_species_kg = self.get_species_masses_kg(state)

        return {
            "success": True,
            "error": "",
            "database_requested": self.requested_database_name,
            "database_used": self.database_used,
            "temperature_K": float(state.temperature()),
            "pressure_Pa": float(state.pressure()),
            "water_kg": all_species_kg.get(self.water_aq, 0.0),
            "aq_gas_kg": {
                comp: all_species_kg.get(species, 0.0)
                for comp, species in self.aq_gas_species.items()
            },
            "gas_kg": {
                comp: all_species_kg.get(species, 0.0)
                for comp, species in self.gas_species.items()
            },
            "extra_aqueous_kg": {
                species: all_species_kg.get(species, 0.0)
                for species in extra_aqueous_kg.keys()
            },
            "minerals_kg": {
                species: all_species_kg.get(species, 0.0)
                for species in minerals_kg.keys()
            },
            "all_species_kg": all_species_kg,
            "diagnostics": {
                "V0_m3": V0,
                "U0_J": U0,
                "V_final_m3": float(props.volume()),
                "U_final_J": float(props.internalEnergy()),
                "volume_error_m3": float(props.volume()) - V0,
                "internal_energy_error_J": float(props.internalEnergy()) - U0,
            },
        }

    def get_species_masses_kg(self, state):
        """
        返回当前 ChemicalState 中所有物种质量，单位 kg。
        """
        out = {}
        for species in self.species_names:
            n_mol = self._get_amount_mol(state, species)
            out[species] = n_mol * self.molar_mass[species]
        return out

    def print_species(self):
        """
        打印当前 ChemicalSystem 中所有物种名称。
        """
        print(f"Database used: {self.database_used}")
        for name in self.species_names:
            print(name)

    def describe(self):
        """
        返回当前计算器的关键配置信息，便于平台日志记录。
        """
        return {
            "database_requested": self.requested_database_name,
            "database_used": self.database_used,
            "gas_components": self.gas_components,
            "aqueous_species_map": dict(self.aq_gas_species),
            "gas_species_map": dict(self.gas_species),
            "fallback_errors": dict(getattr(self, "fallback_errors", {})),
        }

    def _set_mass_kg(self, state, species, mass_kg):
        """
        按 kg 设置物种质量。内部转换为 mol 后传给 Reaktoro。
        """
        if mass_kg is None or float(mass_kg) <= 0.0:
            return
        if species not in self.species_index:
            raise KeyError(f"物种 {species!r} 不在当前 ChemicalSystem 中。")
        amount_mol = float(mass_kg) / self.molar_mass[species]
        state.set(species, amount_mol, "mol")

    def _get_amount_mol(self, state, species):
        """
        获取某物种物质的量，单位 mol。兼容不同 Reaktoro Python 构建。
        """
        try:
            return float(state.speciesAmount(species))
        except Exception:
            amounts = state.speciesAmounts()
            if hasattr(amounts, "asarray"):
                amounts = amounts.asarray()
            return float(amounts[self.species_index[species]])

    def _check_component(self, comp):
        """
        检查气体组分是否已注册。
        """
        if comp not in self.aq_gas_species or comp not in self.gas_species:
            raise KeyError(
                f"气体组分 {comp!r} 未在初始化时注册。"
                f"当前可用组分为：{list(self.gas_components)}"
            )


if __name__ == "__main__":
    # 简单测试：包含甲烷。若 supcrtbl 缺少 CH4(aq)，会自动切换到 supcrtbl-organics。
    eq = GasWaterUVEquilibrium(
        database_name="supcrtbl",
        gas_components=("He", "N2", "H2", "CH4", "CO2"),
        auto_use_organics=True,
    )

    print(eq.describe())

    result = eq.solve(
        temperature_K=298.15,
        pressure_Pa=10.0e6,
        water_kg=1.0,
        aq_gas_kg={"He": 2e-8, "N2": 2e-5, "H2": 1e-6, "CH4": 5e-6, "CO2": 2e-4},
        gas_kg={"He": 5e-8, "N2": 8e-4, "H2": 1e-4, "CH4": 4e-4, "CO2": 2e-3},
        temperature_bounds_K=(273.15, 800.0),
        pressure_bounds_Pa=(1.0e5, 200.0e6),
    )

    print("success:", result["success"])
    print("database_used:", result.get("database_used"))
    print("T/K:", result["temperature_K"])
    print("P/Pa:", result["pressure_Pa"])
    print("aq gas/kg:", result["aq_gas_kg"])
    print("gas/kg:", result["gas_kg"])
    print("diagnostics:", result["diagnostics"])
