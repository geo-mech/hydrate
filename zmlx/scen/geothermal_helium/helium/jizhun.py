# -*- coding: utf-8 -*-
"""
二维水平一注一采地热-氦被动运移模型
============================================================
功能：
1. 只保留溶解态氦 He_sol 作为有效溶质；
2. 注入井注入纯水，Q_IN = 1.88e-4 m3/s；
3. 生产井采用 PressureController 定压生产；
4. 自动开展网格无关性验证：20 m、10 m、5 m；
5. 自动开展最大时间步敏感性验证：24 h、12 h、6 h；
6. 每个算例输出生产流量、实际注入流量、压力、温度、He浓度、
   He瞬时产率、He累计产量、产热功率、累计采热量；
7. 输出水和He质量守恒误差；
8. 输出各算例CSV、汇总CSV及网格/时间步对比曲线。

重要说明：
  本代码按通常科研表达的 1.88 × 10^(-4) m3/s，写成 1.88e-4。
- 当前导入的 fluid.create 可以继续保留 N2_sol 和 CH4_sol 的流体定义，
  但本代码把它们初始化为0，也不读取、不统计，因此有效溶质只有He_sol。
- 为使定压边界在不同时间步下保持一致，PressureController在每个数值步更新，
  extra_plot不再承担压力控制。
- PRODUCTION_CONTROLLER_MODIFY_PORE=False：通过流体转移维持定压，
  比修改孔隙体积更适合产量与质量守恒统计。
"""

import csv
import math
import os
import time
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import zmlx.tfc as tfc
from zmlx import PressureController
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.exsolve.fluid import create
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.tfc._step import add_setting as add_step_setting
from zmlx.ui import gui


# ============================================================
# 1. 基础常数与物理参数
# ============================================================

DAY = 24.0 * 3600.0
YEAR = 365.25 * DAY

P_INIT = 20.0e6
P_PROD = 19.8e6

T_RES = 400.0
T_INJ = 300.0

PERM_VALUE = 5.0e-13
POROSITY = 0.3
PORE_MODULUS = 100.0e6
DENC = 2.0e6
HEAT_COND = 2.56
DIST = 0.8

Q_IN = 1.88e-4

# 产热功率估算所用水比热。
CP_WATER = 4200.0  # J/(kg·K)
RHO_WATER_FALLBACK = 1000.0

X_MIN = 0.0
X_MAX = 1000.0
Y_MIN = 0.0
Y_MAX = 1000.0
Z_MIN = -0.5
Z_MAX = 0.5

X_INJ = 300.0
X_PROD = 700.0
Z_RES = 0.0
Z_PROD_VIRTUAL = 10.0
Z_INJ_VIRTUAL = -10.0

RESERVOIR_Z_MIN = -2.0
RESERVOIR_Z_MAX = 2.0

PROD_VIRTUAL_VOL = 1.0e8
INJ_VIRTUAL_VOL = 100.0
WELL_FACE_AREA = 2.104
WELL_FACE_LENGTH = 1.0

# False表示控制器通过流体转移维持压力，更适合统计真实生产量。
PRODUCTION_CONTROLLER_MODIFY_PORE = False


# ============================================================
# 2. SP2数据换算：只保留He
# ============================================================

SP2_HE_Y = 2.240 / 100.0
SP2_GAS_WATER_RATIO = 24.2 / 100.0


def gas_water_to_he_only_mass_fractions(
        gas_water_ratio: float,
        y_he: float,
        rho_w: float = 1000.0,
        vm: float = 22.414e-3,
) -> Dict[str, float]:
    """
    根据SP2气水比和伴生气He体积分数，计算地热水中的He质量份额。

    计算基准：每1 m3地热水。
    V_He = 气水比 × 气相He体积分数；
    n_He = V_He / 标准摩尔体积；
    m_He = n_He × He摩尔质量；
    r_He = m_He / 水质量；

    仅把水和He纳入质量份额归一化，保持He绝对含量不变。
    """
    m_he_molar = 4.0026e-3  # kg/mol
    v_he = float(gas_water_ratio) * float(y_he)
    n_he = v_he / float(vm)
    m_he = n_he * m_he_molar
    r_he = m_he / float(rho_w)
    total = 1.0 + r_he

    return {
        "h2o": 1.0 / total,
        "he_sol": r_he / total,
    }


HE_ONLY_INIT_S = gas_water_to_he_only_mass_fractions(
    gas_water_ratio=SP2_GAS_WATER_RATIO,
    y_he=SP2_HE_Y,
)


# ============================================================
# 3. 验证设置
# ============================================================

# 建议先用1年完成数值验证。验证通过后，再把正式工况改为25年。
VALIDATION_TIME = 1.0 * YEAR
RECORD_INTERVAL = 5.0 * DAY

# all：全部验证；grid：只做网格；time：只做时间步；baseline：只跑基准。
RUN_MODE = "all"

# 五个唯一算例即可同时组成两套三级验证：
# 网格组：20、10、5 m，统一dt_max=12 h；
# 时间步组：24、12、6 h，统一dx=dy=10 m。
CASE_SPECS = [
    {
        "case_name": "grid_dx20_dt12h",
        "groups": ("grid",),
        "dx": 20.0,
        "dy": 20.0,
        "dt_max": 12.0 * 3600.0,
    },
    {
        "case_name": "baseline_dx10_dt12h",
        "groups": ("grid", "time", "baseline"),
        "dx": 10.0,
        "dy": 10.0,
        "dt_max": 12.0 * 3600.0,
    },
    {
        "case_name": "grid_dx5_dt12h",
        "groups": ("grid",),
        "dx": 5.0,
        "dy": 5.0,
        "dt_max": 12.0 * 3600.0,
    },
    {
        "case_name": "time_dx10_dt24h",
        "groups": ("time",),
        "dx": 10.0,
        "dy": 10.0,
        "dt_max": 24.0 * 3600.0,
    },
    {
        "case_name": "time_dx10_dt6h",
        "groups": ("time",),
        "dx": 10.0,
        "dy": 10.0,
        "dt_max": 6.0 * 3600.0,
    },
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ROOT = os.path.join(SCRIPT_DIR, "he_grid_timestep_validation_output")
CASES_DIR = os.path.join(OUTPUT_ROOT, "cases")
GRID_DIR = os.path.join(OUTPUT_ROOT, "grid_validation")
TIME_DIR = os.path.join(OUTPUT_ROOT, "timestep_validation")


# ============================================================
# 4. 通用函数
# ============================================================


def safe_ratio(numerator: float, denominator: float) -> float:
    if (
            not math.isfinite(float(numerator))
            or not math.isfinite(float(denominator))
            or abs(float(denominator)) <= 1.0e-300
    ):
        return float("nan")
    return float(numerator) / float(denominator)


def finite_max_abs(values) -> float:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return float("nan")
    return float(np.max(np.abs(array)))


def normalize_fid(fid) -> List[int]:
    if isinstance(fid, (list, tuple)):
        return [int(value) for value in fid]
    return [int(fid)]


def find_fid(model, name: str) -> List[int]:
    fid = model.find_fludef(name=name)
    if fid is None:
        raise KeyError(
            f"模型中找不到流体或组分{name!r}。"
            "请确认fluid.py中仍定义liq、h2o和he_sol。"
        )
    return normalize_fid(fid)


def get_temperature_key(model):
    key = model.get_cell_key("temperature")
    if key is None:
        key = tfc.cell_keys(model).temperature
    return key


def is_reservoir_cell(cell) -> bool:
    z = float(cell.pos[2])
    return RESERVOIR_Z_MIN <= z <= RESERVOIR_Z_MAX


def get_well_cells(model, virtual_pos, well_name: str):
    virtual_cell = model.get_nearest_cell(pos=virtual_pos)
    reservoir_neighbors = [
        cell for cell in virtual_cell.cells if is_reservoir_cell(cell)
    ]
    if len(reservoir_neighbors) != 1:
        raise RuntimeError(
            f"{well_name}虚拟网格应只连接1个真实储层网格，"
            f"当前找到{len(reservoir_neighbors)}个。"
        )
    return virtual_cell, reservoir_neighbors[0]


def find_face_between(model, cell_a, cell_b):
    pair = {int(cell_a.index), int(cell_b.index)}
    for face in model.faces:
        c0 = face.get_cell(0)
        c1 = face.get_cell(1)
        if {int(c0.index), int(c1.index)} == pair:
            return face
    raise RuntimeError(
        f"找不到cell {cell_a.index}与cell {cell_b.index}之间的连接面。"
    )


def get_component_mass(cell, fid: List[int]) -> float:
    return float(cell.get_fluid(*fid).mass)


def get_phase_mass(cell, fid: List[int]) -> float:
    return float(cell.get_fluid(*fid).mass)


def get_mass_fraction(
        cell,
        component_fid: List[int],
        liquid_fid: List[int],
) -> float:
    liquid_mass = get_phase_mass(cell, liquid_fid)
    if liquid_mass <= 0.0:
        return 0.0
    return get_component_mass(cell, component_fid) / liquid_mass


def get_phase_density(cell, liquid_fid: List[int]) -> float:
    fluid = cell.get_fluid(*liquid_fid)

    for attr_name in ("den", "density"):
        try:
            value = getattr(fluid, attr_name)
            if callable(value):
                value = value()
            value = float(value)
            if math.isfinite(value) and value > 0.0:
                return value
        except Exception:
            pass

    try:
        mass = float(fluid.mass)
        volume = float(fluid.vol)
        if mass > 0.0 and volume > 0.0:
            value = mass / volume
            if math.isfinite(value) and value > 0.0:
                return value
    except Exception:
        pass

    return RHO_WATER_FALLBACK


def get_cell_temperature(cell, temperature_key) -> float:
    return float(cell.get_attr(temperature_key))


def signed_dv_out_of_reservoir(
        face,
        reservoir_cell,
        virtual_cell,
        liquid_phase_id: int,
) -> Tuple[float, object]:
    """
    读取最近一个数值步穿过井连接面的液相体积。

    返回值：
    signed_dv > 0：真实储层 -> 虚拟井筒；
    signed_dv < 0：虚拟井筒 -> 真实储层。

    当前模型关闭重力，使用井两侧压力判断方向。
    """
    dv_abs = abs(float(face.get_dv(int(liquid_phase_id))))
    p_res = float(reservoir_cell.pre)
    p_virtual = float(virtual_cell.pre)

    if p_res > p_virtual:
        return dv_abs, reservoir_cell
    if p_res < p_virtual:
        return -dv_abs, virtual_cell
    return 0.0, reservoir_cell


def write_rows_csv(path: str, rows: List[Dict]):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# 5. 创建单个验证模型
# ============================================================


def create_model(case_spec: Dict) -> Dict:
    dx = float(case_spec["dx"])
    dy = float(case_spec["dy"])
    dt_max = float(case_spec["dt_max"])

    mesh = create_xy(
        x_min=X_MIN,
        dx=dx,
        x_max=X_MAX,
        y_min=Y_MIN,
        dy=dy,
        y_max=Y_MAX,
        z_min=Z_MIN,
        z_max=Z_MAX,
    )

    y_min, y_max = get_pos_range(mesh, 1)
    y_mid = 0.5 * (y_min + y_max)

    requested_prod_virtual_pos = [X_PROD, y_mid, Z_PROD_VIRTUAL]
    requested_inj_virtual_pos = [X_INJ, y_mid, Z_INJ_VIRTUAL]

    add_cell_face(
        mesh,
        pos=[X_PROD, y_mid, Z_RES],
        offset=[0.0, 0.0, Z_PROD_VIRTUAL],
        vol=PROD_VIRTUAL_VOL,
        area=WELL_FACE_AREA,
        length=WELL_FACE_LENGTH,
    )

    add_cell_face(
        mesh,
        pos=[X_INJ, y_mid, Z_RES],
        offset=[0.0, 0.0, Z_INJ_VIRTUAL],
        vol=INJ_VIRTUAL_VOL,
        area=WELL_FACE_AREA,
        length=WELL_FACE_LENGTH,
    )

    def get_perm(x, y, z):
        return PERM_VALUE

    def get_s(x, y, z):
        # 两个虚拟井筒均初始化为纯水。
        if z < RESERVOIR_Z_MIN or z > RESERVOIR_Z_MAX:
            return {
                "h2o": 1.0,
                "he_sol": 0.0,
                # 当前fluid.py若仍定义另外两种组分，将其显式置零。
                "n2_sol": 0.0,
                "ch4_sol": 0.0,
            }

        # 真实储层只含水和溶解态He。
        return {
            "h2o": HE_ONLY_INIT_S["h2o"],
            "he_sol": HE_ONLY_INIT_S["he_sol"],
            "n2_sol": 0.0,
            "ch4_sol": 0.0,
        }

    def get_denc(x, y, z):
        return DENC

    def get_porosity(x, y, z):
        return POROSITY

    def get_p(x, y, z):
        if z > RESERVOIR_Z_MAX:
            return P_PROD
        return P_INIT

    def get_t(x, y, z):
        if z < RESERVOIR_Z_MIN:
            return T_INJ
        return T_RES

    injectors = [
        {
            "pos": requested_inj_virtual_pos,
            "fluid_id": "h2o",
            "value": Q_IN,
        }
    ]

    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=PORE_MODULUS,
        p=get_p,
        temperature=get_t,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=HEAT_COND,
        dist=DIST,
        dt_max=dt_max,
        gravity=[0.0, 0.0, 0.0],
        injectors=injectors,
        use_mass=True,
    )

    prod_virtual_cell, prod_res_cell = get_well_cells(
        model, requested_prod_virtual_pos, "生产井"
    )
    inj_virtual_cell, inj_res_cell = get_well_cells(
        model, requested_inj_virtual_pos, "注入井"
    )

    reservoir_cells = [cell for cell in model.cells if is_reservoir_cell(cell)]

    return {
        "model": model,
        "case_spec": dict(case_spec),
        "prod_virtual_cell": prod_virtual_cell,
        "prod_res_cell": prod_res_cell,
        "inj_virtual_cell": inj_virtual_cell,
        "inj_res_cell": inj_res_cell,
        "reservoir_cells": reservoir_cells,
    }


# ============================================================
# 6. 单算例定量监测器
# ============================================================


class ValidationRecorder:
    COMPONENTS = ("h2o", "he")

    def __init__(self, case_data: Dict, case_dir: str):
        self.model = case_data["model"]
        self.case_spec = case_data["case_spec"]
        self.case_name = self.case_spec["case_name"]
        self.case_dir = os.path.abspath(case_dir)
        os.makedirs(self.case_dir, exist_ok=True)

        self.prod_virtual_cell = case_data["prod_virtual_cell"]
        self.prod_res_cell = case_data["prod_res_cell"]
        self.inj_virtual_cell = case_data["inj_virtual_cell"]
        self.inj_res_cell = case_data["inj_res_cell"]
        self.reservoir_cells = case_data["reservoir_cells"]

        self.prod_face = find_face_between(
            self.model, self.prod_res_cell, self.prod_virtual_cell
        )
        self.inj_face = find_face_between(
            self.model, self.inj_res_cell, self.inj_virtual_cell
        )

        self.liquid_fid = find_fid(self.model, "liq")
        self.liquid_phase_id = int(self.liquid_fid[0])
        self.component_fids = {
            "h2o": find_fid(self.model, "h2o"),
            "he": find_fid(self.model, "he_sol"),
        }
        self.temperature_key = get_temperature_key(self.model)

        self.initial_fraction = {
            "h2o": float(HE_ONLY_INIT_S["h2o"]),
            "he": float(HE_ONLY_INIT_S["he_sol"]),
        }

        self.initial_density = get_phase_density(
            self.prod_res_cell, self.liquid_fid
        )
        self.initial_he_concentration = (
            self.initial_density * self.initial_fraction["he"]
        )

        self.initial_reservoir_mass = {
            name: self.sum_reservoir_component_mass(name)
            for name in self.COMPONENTS
        }

        # 生产面累计净外流质量；正值为从储层采出。
        self.cumulative_prod_mass = {
            name: 0.0 for name in self.COMPONENTS
        }

        # 注入面累计“从储层向注入井侧”的带符号外流质量。
        # 正常注水时为负值，其相反数即净注入储层质量。
        self.cumulative_inj_side_out_mass = {
            name: 0.0 for name in self.COMPONENTS
        }

        self.cumulative_heat_j = 0.0
        self.last_step_time = float(tfc.get_time(self.model))
        self.next_record_time = RECORD_INTERVAL

        self.latest_dt = 0.0
        self.latest_q_prod = 0.0
        self.latest_q_in_actual = 0.0
        self.latest_prod_temperature = get_cell_temperature(
            self.prod_res_cell, self.temperature_key
        )
        self.latest_prod_density = get_phase_density(
            self.prod_res_cell, self.liquid_fid
        )
        self.latest_fraction = {
            name: get_mass_fraction(
                self.prod_res_cell,
                self.component_fids[name],
                self.liquid_fid,
            )
            for name in self.COMPONENTS
        }
        self.latest_component_rate = {
            name: 0.0 for name in self.COMPONENTS
        }
        self.latest_thermal_power_w = 0.0

        self.rows: List[Dict] = []
        self.history_csv = os.path.join(self.case_dir, "history.csv")
        self.record(force=True)

    def sum_reservoir_component_mass(self, name: str) -> float:
        fid = self.component_fids[name]
        return float(sum(
            get_component_mass(cell, fid)
            for cell in self.reservoir_cells
        ))

    def reservoir_pressure_statistics(self) -> Tuple[float, float, float]:
        pressures = np.asarray(
            [float(cell.pre) for cell in self.reservoir_cells],
            dtype=float,
        )
        return (
            float(np.mean(pressures)),
            float(np.min(pressures)),
            float(np.max(pressures)),
        )

    def update_one_step(self):
        """每个真实数值步积分注采连接面通量。"""
        now = float(tfc.get_time(self.model))
        dt_s = now - self.last_step_time
        if dt_s <= 0.0:
            return

        prod_dv_out, prod_upstream = signed_dv_out_of_reservoir(
            self.prod_face,
            self.prod_res_cell,
            self.prod_virtual_cell,
            self.liquid_phase_id,
        )
        inj_dv_out, inj_upstream = signed_dv_out_of_reservoir(
            self.inj_face,
            self.inj_res_cell,
            self.inj_virtual_cell,
            self.liquid_phase_id,
        )

        self.latest_dt = dt_s
        self.latest_q_prod = prod_dv_out / dt_s
        self.latest_q_in_actual = -inj_dv_out / dt_s

        self.latest_prod_temperature = get_cell_temperature(
            prod_upstream, self.temperature_key
        )
        self.latest_prod_density = get_phase_density(
            prod_upstream, self.liquid_fid
        )

        for name in self.COMPONENTS:
            fid = self.component_fids[name]
            prod_fraction = get_mass_fraction(
                prod_upstream, fid, self.liquid_fid
            )
            inj_fraction = get_mass_fraction(
                inj_upstream, fid, self.liquid_fid
            )
            prod_density = get_phase_density(
                prod_upstream, self.liquid_fid
            )
            inj_density = get_phase_density(
                inj_upstream, self.liquid_fid
            )

            prod_dm = prod_dv_out * prod_density * prod_fraction
            inj_side_out_dm = inj_dv_out * inj_density * inj_fraction

            self.cumulative_prod_mass[name] += prod_dm
            self.cumulative_inj_side_out_mass[name] += inj_side_out_dm
            self.latest_component_rate[name] = prod_dm / dt_s

        self.latest_fraction = {
            name: get_mass_fraction(
                prod_upstream,
                self.component_fids[name],
                self.liquid_fid,
            )
            for name in self.COMPONENTS
        }

        self.latest_thermal_power_w = (
            self.latest_q_prod
            * self.latest_prod_density
            * CP_WATER
            * (self.latest_prod_temperature - T_INJ)
        )
        self.cumulative_heat_j += self.latest_thermal_power_w * dt_s

        self.last_step_time = now

        if now >= self.next_record_time:
            self.record(force=False)
            while self.next_record_time <= now:
                self.next_record_time += RECORD_INTERVAL

    def build_row(self) -> Dict:
        time_s = float(tfc.get_time(self.model))
        step = int(tfc.get_step(self.model))

        reservoir_mass = {
            name: self.sum_reservoir_component_mass(name)
            for name in self.COMPONENTS
        }

        balance_error = {}
        balance_error_rel = {}
        cumulative_from_balance = {}

        for name in self.COMPONENTS:
            cumulative_from_balance[name] = (
                self.initial_reservoir_mass[name]
                - reservoir_mass[name]
                - self.cumulative_inj_side_out_mass[name]
            )

            # 储层控制体守恒式：
            # M_res + M_prod_out + M_inj_side_out - M0 = 0。
            # 正常注入时 M_inj_side_out < 0。
            error = (
                reservoir_mass[name]
                + self.cumulative_prod_mass[name]
                + self.cumulative_inj_side_out_mass[name]
                - self.initial_reservoir_mass[name]
            )
            balance_error[name] = error
            balance_error_rel[name] = safe_ratio(
                error, self.initial_reservoir_mass[name]
            )

        he_concentration_kg_m3 = (
            self.latest_prod_density * self.latest_fraction["he"]
        )
        mean_p, min_p, max_p = self.reservoir_pressure_statistics()

        normalized_temperature = safe_ratio(
            self.latest_prod_temperature - T_INJ,
            T_RES - T_INJ,
        )

        return {
            "case_name": self.case_name,
            "dx_m": float(self.case_spec["dx"]),
            "dy_m": float(self.case_spec["dy"]),
            "dt_max_s": float(self.case_spec["dt_max"]),
            "dt_max_hour": float(self.case_spec["dt_max"]) / 3600.0,
            "cell_count_reservoir": len(self.reservoir_cells),

            "step": step,
            "time_s": time_s,
            "time_day": time_s / DAY,
            "time_year": time_s / YEAR,
            "last_actual_dt_s": self.latest_dt,

            "q_in_set_m3_s": Q_IN,
            "q_in_actual_m3_s": self.latest_q_in_actual,
            "q_in_actual_m3_day": self.latest_q_in_actual * DAY,
            "q_prod_m3_s": self.latest_q_prod,
            "q_prod_m3_day": self.latest_q_prod * DAY,
            "q_prod_to_q_in_set": safe_ratio(self.latest_q_prod, Q_IN),

            "cum_injected_h2o_kg": -self.cumulative_inj_side_out_mass["h2o"],
            "cum_produced_h2o_kg": self.cumulative_prod_mass["h2o"],
            "res_h2o_mass_kg": reservoir_mass["h2o"],

            "prod_virtual_pressure_MPa": (
                float(self.prod_virtual_cell.pre) / 1.0e6
            ),
            "prod_reservoir_pressure_MPa": (
                float(self.prod_res_cell.pre) / 1.0e6
            ),
            "reservoir_mean_pressure_MPa": mean_p / 1.0e6,
            "reservoir_min_pressure_MPa": min_p / 1.0e6,
            "reservoir_max_pressure_MPa": max_p / 1.0e6,

            "prod_temperature_K": self.latest_prod_temperature,
            "prod_temperature_C": self.latest_prod_temperature - 273.15,
            "normalized_temperature": normalized_temperature,
            "prod_liquid_density_kg_m3": self.latest_prod_density,

            "he_initial_mass_fraction": self.initial_fraction["he"],
            "he_mass_fraction": self.latest_fraction["he"],
            "he_w_over_w0": safe_ratio(
                self.latest_fraction["he"], self.initial_fraction["he"]
            ),
            "he_concentration_kg_m3_water": he_concentration_kg_m3,
            "he_concentration_mg_L": he_concentration_kg_m3 * 1000.0,
            "he_C_over_C0": safe_ratio(
                he_concentration_kg_m3, self.initial_he_concentration
            ),
            "he_instantaneous_rate_kg_s": self.latest_component_rate["he"],
            "he_instantaneous_rate_kg_day": (
                self.latest_component_rate["he"] * DAY
            ),
            "cum_he_prod_kg": self.cumulative_prod_mass["he"],
            "cum_he_prod_from_balance_kg": cumulative_from_balance["he"],
            "res_he_mass_kg": reservoir_mass["he"],
            "he_recovery_ratio": safe_ratio(
                self.cumulative_prod_mass["he"],
                self.initial_reservoir_mass["he"],
            ),

            "thermal_power_W": self.latest_thermal_power_w,
            "thermal_power_MW": self.latest_thermal_power_w / 1.0e6,
            "cum_heat_J": self.cumulative_heat_j,
            "cum_heat_MWh": self.cumulative_heat_j / 3.6e9,

            "h2o_mass_balance_error_kg": balance_error["h2o"],
            "h2o_mass_balance_error_rel": balance_error_rel["h2o"],
            "he_mass_balance_error_kg": balance_error["he"],
            "he_mass_balance_error_rel": balance_error_rel["he"],
        }

    def record(self, force: bool):
        now = float(tfc.get_time(self.model))
        if (
                not force
                and self.rows
                and now <= float(self.rows[-1]["time_s"])
        ):
            return

        row = self.build_row()
        if (
                self.rows
                and abs(float(self.rows[-1]["time_s"]) - now) <= 1.0e-12
        ):
            self.rows[-1] = row
        else:
            self.rows.append(row)

        write_rows_csv(self.history_csv, self.rows)

    def finalize(self):
        self.update_one_step()
        self.record(force=True)
        write_rows_csv(self.history_csv, self.rows)

    def summary(self, runtime_s: float) -> Dict:
        if not self.rows:
            raise RuntimeError(f"算例{self.case_name}没有监测数据。")

        last = self.rows[-1]
        return {
            "case_name": self.case_name,
            "groups": ",".join(self.case_spec.get("groups", ())),
            "dx_m": float(self.case_spec["dx"]),
            "dy_m": float(self.case_spec["dy"]),
            "dt_max_s": float(self.case_spec["dt_max"]),
            "dt_max_hour": float(self.case_spec["dt_max"]) / 3600.0,
            "simulation_time_year": float(last["time_year"]),
            "final_step": int(last["step"]),
            "reservoir_cell_count": int(last["cell_count_reservoir"]),
            "runtime_s": float(runtime_s),

            "final_q_in_actual_m3_s": float(last["q_in_actual_m3_s"]),
            "final_q_prod_m3_s": float(last["q_prod_m3_s"]),
            "final_q_prod_to_q_in_set": float(last["q_prod_to_q_in_set"]),
            "final_reservoir_mean_pressure_MPa": float(
                last["reservoir_mean_pressure_MPa"]
            ),
            "final_reservoir_max_pressure_MPa": float(
                last["reservoir_max_pressure_MPa"]
            ),
            "final_prod_temperature_K": float(last["prod_temperature_K"]),
            "final_prod_temperature_C": float(last["prod_temperature_C"]),
            "final_he_concentration_mg_L": float(
                last["he_concentration_mg_L"]
            ),
            "final_he_C_over_C0": float(last["he_C_over_C0"]),
            "final_cum_he_prod_kg": float(last["cum_he_prod_kg"]),
            "final_cum_he_prod_from_balance_kg": float(
                last["cum_he_prod_from_balance_kg"]
            ),
            "final_he_recovery_ratio": float(last["he_recovery_ratio"]),
            "final_thermal_power_MW": float(last["thermal_power_MW"]),
            "final_cum_heat_MWh": float(last["cum_heat_MWh"]),

            "max_abs_h2o_mass_balance_error_rel": finite_max_abs(
                [row["h2o_mass_balance_error_rel"] for row in self.rows]
            ),
            "max_abs_he_mass_balance_error_rel": finite_max_abs(
                [row["he_mass_balance_error_rel"] for row in self.rows]
            ),
            "max_prod_pressure_target_error_MPa": finite_max_abs([
                float(row["prod_virtual_pressure_MPa"]) - P_PROD / 1.0e6
                for row in self.rows
            ]),
            "history_csv": self.history_csv,
        }


# ============================================================
# 7. 执行单个算例
# ============================================================


def run_case(case_spec: Dict) -> Tuple[List[Dict], Dict]:
    case_name = case_spec["case_name"]
    case_dir = os.path.join(CASES_DIR, case_name)
    os.makedirs(case_dir, exist_ok=True)

    print("\n" + "=" * 72)
    print(f"开始算例：{case_name}")
    print(f"网格：dx={case_spec['dx']} m, dy={case_spec['dy']} m")
    print(f"dt_max={case_spec['dt_max'] / 3600.0:.3f} h")
    print(f"Q_IN={Q_IN:.6e} m3/s")
    print(f"总时间={VALIDATION_TIME / YEAR:.3f} year")
    print("=" * 72)

    case_data = create_model(case_spec)
    model = case_data["model"]
    prod_virtual_cell = case_data["prod_virtual_cell"]

    pressure_controller = PressureController(
        cell=prod_virtual_cell,
        t=[-1.0e20, 1.0e20],
        p=[P_PROD, P_PROD],
        modify_pore=PRODUCTION_CONTROLLER_MODIFY_PORE,
    )
    pressure_controller.update(
        t=tfc.get_time(model),
        modify_pore=PRODUCTION_CONTROLLER_MODIFY_PORE,
    )

    recorder = ValidationRecorder(case_data, case_dir)

    safe_name = case_name.replace("-", "_").replace(" ", "_")
    pressure_slot_name = f"{safe_name}_pressure_control"
    monitor_slot_name = f"{safe_name}_validation_monitor"

    def update_production_pressure():
        pressure_controller.update(
            t=tfc.get_time(model),
            modify_pore=PRODUCTION_CONTROLLER_MODIFY_PORE,
        )

    add_step_setting(
        model=model,
        start=0,
        step=1,
        name=pressure_slot_name,
    )
    add_step_setting(
        model=model,
        start=0,
        step=1,
        name=monitor_slot_name,
    )

    slots = {
        pressure_slot_name: update_production_pressure,
        monitor_slot_name: recorder.update_one_step,
    }

    def extra_plot():
        # 批量验证不显示空间场，只保证绘图回调不会改变物理边界。
        return None

    start_clock = time.perf_counter()
    tfc.solve(
        model=model,
        extra_plot=extra_plot,
        slots=slots,
        time_max=VALIDATION_TIME,
        state_hint=f"He validation: {case_name}",
    )
    runtime_s = time.perf_counter() - start_clock

    recorder.finalize()
    summary = recorder.summary(runtime_s=runtime_s)

    print(f"完成算例：{case_name}")
    print(f"最终步数：{summary['final_step']}")
    print(f"运行耗时：{summary['runtime_s']:.3f} s")
    print(f"最终生产流量：{summary['final_q_prod_m3_s']:.6e} m3/s")
    print(f"最终累计产He：{summary['final_cum_he_prod_kg']:.6e} kg")
    print(
        "最大水相对守恒误差："
        f"{summary['max_abs_h2o_mass_balance_error_rel']:.6e}"
    )
    print(
        "最大He相对守恒误差："
        f"{summary['max_abs_he_mass_balance_error_rel']:.6e}"
    )

    return recorder.rows, summary


# ============================================================
# 8. 对比曲线与收敛数据
# ============================================================


PLOT_SPECS = [
    (
        "q_prod_m3_s",
        "Production flow rate (m3/s)",
        "01_production_flow_rate.png",
    ),
    (
        "reservoir_mean_pressure_MPa",
        "Mean reservoir pressure (MPa)",
        "02_mean_reservoir_pressure.png",
    ),
    (
        "prod_temperature_C",
        "Production temperature (degC)",
        "03_production_temperature.png",
    ),
    (
        "he_concentration_mg_L",
        "He concentration (mg/L)",
        "04_he_concentration.png",
    ),
    (
        "cum_he_prod_kg",
        "Cumulative He production (kg)",
        "05_cumulative_he_production.png",
    ),
    (
        "thermal_power_MW",
        "Thermal power (MW)",
        "06_thermal_power.png",
    ),
    (
        "cum_heat_MWh",
        "Cumulative heat production (MWh)",
        "07_cumulative_heat.png",
    ),
    (
        "h2o_mass_balance_error_rel",
        "Relative water mass-balance error",
        "08_water_mass_balance_error.png",
    ),
    (
        "he_mass_balance_error_rel",
        "Relative He mass-balance error",
        "09_he_mass_balance_error.png",
    ),
]


def plot_validation_group(
        group_name: str,
        case_specs: List[Dict],
        histories: Dict[str, List[Dict]],
        output_dir: str,
):
    os.makedirs(output_dir, exist_ok=True)

    for key, ylabel, filename in PLOT_SPECS:
        fig, ax = plt.subplots(figsize=(8.8, 5.4))

        for spec in case_specs:
            name = spec["case_name"]
            rows = histories[name]
            x = np.asarray([row["time_year"] for row in rows], dtype=float)
            y = np.asarray([row[key] for row in rows], dtype=float)

            if group_name == "grid":
                label = f"dx=dy={spec['dx']:g} m"
            else:
                label = f"dt_max={spec['dt_max'] / 3600.0:g} h"

            ax.plot(x, y, label=label)

        ax.set_xlabel("Time (year)")
        ax.set_ylabel(ylabel)
        ax.set_title(
            "Grid-independence comparison"
            if group_name == "grid"
            else "Time-step sensitivity comparison"
        )
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, filename), dpi=300)
        plt.close(fig)


def relative_difference(value: float, reference: float) -> float:
    return safe_ratio(float(value) - float(reference), float(reference))


def write_convergence_summary(
        group_name: str,
        case_specs: List[Dict],
        summaries: Dict[str, Dict],
        output_path: str,
):
    if group_name == "grid":
        reference_spec = min(case_specs, key=lambda item: float(item["dx"]))
    else:
        reference_spec = min(case_specs, key=lambda item: float(item["dt_max"]))

    reference = summaries[reference_spec["case_name"]]

    compare_fields = [
        "final_q_prod_m3_s",
        "final_reservoir_mean_pressure_MPa",
        "final_prod_temperature_K",
        "final_he_concentration_mg_L",
        "final_cum_he_prod_kg",
        "final_thermal_power_MW",
        "final_cum_heat_MWh",
    ]

    rows = []
    for spec in case_specs:
        summary = summaries[spec["case_name"]]
        row = {
            "group": group_name,
            "case_name": spec["case_name"],
            "reference_case": reference_spec["case_name"],
            "dx_m": float(spec["dx"]),
            "dy_m": float(spec["dy"]),
            "dt_max_hour": float(spec["dt_max"]) / 3600.0,
            "reservoir_cell_count": summary["reservoir_cell_count"],
            "final_step": summary["final_step"],
            "runtime_s": summary["runtime_s"],
            "max_abs_h2o_mass_balance_error_rel": (
                summary["max_abs_h2o_mass_balance_error_rel"]
            ),
            "max_abs_he_mass_balance_error_rel": (
                summary["max_abs_he_mass_balance_error_rel"]
            ),
        }

        for field in compare_fields:
            value = float(summary[field])
            ref_value = float(reference[field])
            row[field] = value
            row[f"{field}_relative_difference_vs_reference"] = (
                relative_difference(value, ref_value)
            )

        rows.append(row)

    write_rows_csv(output_path, rows)


def selected_specs() -> List[Dict]:
    mode = str(RUN_MODE).strip().lower()
    if mode == "all":
        return list(CASE_SPECS)
    if mode == "grid":
        return [spec for spec in CASE_SPECS if "grid" in spec["groups"]]
    if mode == "time":
        return [spec for spec in CASE_SPECS if "time" in spec["groups"]]
    if mode == "baseline":
        return [spec for spec in CASE_SPECS if "baseline" in spec["groups"]]
    raise ValueError(
        f"未知RUN_MODE={RUN_MODE!r}，可选all/grid/time/baseline。"
    )


# ============================================================
# 9. 主函数
# ============================================================


def main():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    os.makedirs(CASES_DIR, exist_ok=True)
    os.makedirs(GRID_DIR, exist_ok=True)
    os.makedirs(TIME_DIR, exist_ok=True)

    print("\n========== He-only模型参数 ==========")
    print(f"Q_IN = {Q_IN:.6e} m3/s")
    print(f"SP2气水比 = {SP2_GAS_WATER_RATIO:.6e} m3/m3")
    print(f"SP2气相He体积分数 = {SP2_HE_Y:.6e}")
    print(f"储层初始He质量份额 = {HE_ONLY_INIT_S['he_sol']:.12e}")
    print(f"储层初始水质量份额 = {HE_ONLY_INIT_S['h2o']:.12e}")
    print(f"验证时间 = {VALIDATION_TIME / YEAR:.6f} year")
    print(f"RUN_MODE = {RUN_MODE}")
    print(f"输出目录 = {OUTPUT_ROOT}")
    print("=====================================\n")

    histories: Dict[str, List[Dict]] = {}
    summaries: Dict[str, Dict] = {}

    specs = selected_specs()
    for spec in specs:
        rows, summary = run_case(spec)
        histories[spec["case_name"]] = rows
        summaries[spec["case_name"]] = summary

    all_summary_rows = [summaries[spec["case_name"]] for spec in specs]
    write_rows_csv(
        os.path.join(OUTPUT_ROOT, "all_cases_summary.csv"),
        all_summary_rows,
    )

    grid_specs = [
        spec for spec in specs
        if "grid" in spec["groups"] and spec["case_name"] in histories
    ]
    if len(grid_specs) >= 2:
        grid_specs = sorted(grid_specs, key=lambda item: float(item["dx"]), reverse=True)
        plot_validation_group("grid", grid_specs, histories, GRID_DIR)
        write_convergence_summary(
            group_name="grid",
            case_specs=grid_specs,
            summaries=summaries,
            output_path=os.path.join(
                GRID_DIR, "grid_convergence_summary.csv"
            ),
        )

    time_specs = [
        spec for spec in specs
        if "time" in spec["groups"] and spec["case_name"] in histories
    ]
    if len(time_specs) >= 2:
        time_specs = sorted(
            time_specs,
            key=lambda item: float(item["dt_max"]),
            reverse=True,
        )
        plot_validation_group("time", time_specs, histories, TIME_DIR)
        write_convergence_summary(
            group_name="time",
            case_specs=time_specs,
            summaries=summaries,
            output_path=os.path.join(
                TIME_DIR, "timestep_convergence_summary.csv"
            ),
        )

    print("\n========== 全部验证计算完成 ==========")
    print(f"总汇总CSV：{os.path.join(OUTPUT_ROOT, 'all_cases_summary.csv')}")
    print(f"各算例历史数据：{CASES_DIR}")
    if len(grid_specs) >= 2:
        print(f"网格验证曲线与汇总：{GRID_DIR}")
    if len(time_specs) >= 2:
        print(f"时间步验证曲线与汇总：{TIME_DIR}")
    print("======================================\n")


if __name__ == "__main__":
    gui.execute(main)
