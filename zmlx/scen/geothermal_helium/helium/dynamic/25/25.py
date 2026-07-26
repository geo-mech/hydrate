# -*- coding: utf-8 -*-
"""
简化版：25 年周期性动态注入流量—定压生产 He 被动运移模型

本文件负责：
1. 创建二维 xy 一注一采模型；
2. 按 SP2 前 12 个月水流量逐月更新注入边界，并逐年重复；
3. 每一步维持生产井定压；
4. 调用 show_xy(model) 显示压力、温度和 He 空间场；
5. 积分注采井面流量、产热、产 He 和质量守恒；
6. 输出动态边界 CSV 和长期时间序列 CSV。

本文件不绘制时间曲线。时间曲线与固定—动态对比由独立 CSV 绘图脚本完成。
"""

import csv
import math
import os

import zmlx.tfc as tfc
from zmlx import PressureController
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.helium.fluid import create
from zmlx.scen.geothermal_helium.helium.show import show_xy
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.tfc._step import add_setting as add_step_setting
from zmlx.ui import gui


# ------------------------- 基本参数 -------------------------

P_INIT, P_PROD = 20.0e6, 19.8e6
T_RES, T_INJ = 400.0, 300.0
PERM, POROSITY = 5.0e-13, 0.30

# 固定流量对比基准，也是动态曲线的时长加权年平均值
Q_BASE = 1.88e-4

X_INJ, X_PROD = 300.0, 700.0
Z_RES, Z_PROD, Z_INJ = 0.0, 10.0, -10.0
PROD_VOL, INJ_VOL = 1.0e8, 100.0

DX, DY = 10.0, 10.0
Z_MIN, Z_MAX = -2.0, 2.0

DAY = 24.0 * 3600.0
YEAR = 365.25 * DAY
TIME_MAX = 25.0 * YEAR
DT_MAX = 12.0 * 3600.0
RECORD_INTERVAL = 10.0 * DAY

CP_WATER = 4200.0
RHO_FALLBACK = 1000.0
M_HE = 4.0026e-3
VM_STD = 22.414e-3

SP2_HE_Y = 2.240 / 100.0
SP2_GAS_WATER_RATIO = 24.2 / 100.0

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "he_25year_dynamic_flow_output")
CSV_PATH = os.path.join(
    OUTPUT_DIR,
    "dynamic_long_term_production_history.csv",
)
PROFILE_CSV_PATH = os.path.join(
    OUTPUT_DIR,
    "dynamic_injection_profile.csv",
)


# ------------------------- 动态注入边界 -------------------------

# SP2 前 12 个月井口水流量，单位 m3/h，按 1—12 月逐年重复
SP2_MONTHLY_WATER_FLOW_M3_H = (
    85.0, 85.0, 100.0, 99.0, 73.0, 105.0,
    110.0, 109.0, 106.0, 113.0, 117.0, 120.0,
)

# 现场总流量折算为二维单位厚度模型流量所采用的代表厚度
REPRESENTATIVE_THICKNESS_M = 150.0

CALENDAR_MONTH_DAYS = (
    31.0, 28.0, 31.0, 30.0, 31.0, 30.0,
    31.0, 31.0, 30.0, 31.0, 30.0, 31.0,
)

# 统一缩放至 365.25 天，使一个周期严格等于 YEAR
MONTH_DURATION_S = tuple(
    YEAR * days / sum(CALENDAR_MONTH_DAYS)
    for days in CALENDAR_MONTH_DAYS
)

RAW_MONTHLY_Q_M3_S = tuple(
    flow / REPRESENTATIVE_THICKNESS_M / 3600.0
    for flow in SP2_MONTHLY_WATER_FLOW_M3_H
)

RAW_WEIGHTED_MEAN_Q = sum(
    q * duration
    for q, duration in zip(RAW_MONTHLY_Q_M3_S, MONTH_DURATION_S)
) / YEAR

# 保持动态工况与固定工况每年设定累计注入量相同
DYNAMIC_PROFILE_SCALE = Q_BASE / RAW_WEIGHTED_MEAN_Q
MONTHLY_Q_M3_S = tuple(
    q * DYNAMIC_PROFILE_SCALE
    for q in RAW_MONTHLY_Q_M3_S
)

MONTH_CUM_END_S = []
_running_end = 0.0
for _duration in MONTH_DURATION_S:
    _running_end += _duration
    MONTH_CUM_END_S.append(_running_end)
MONTH_CUM_END_S = tuple(MONTH_CUM_END_S)


def dynamic_profile_state(time_s):
    """返回给定时刻所在的循环年份、月份和动态设定流量。"""

    t = max(float(time_s), 0.0)
    year_index = int(math.floor(t / YEAR))
    phase_s = t - year_index * YEAR

    if phase_s >= YEAR:
        year_index += 1
        phase_s = 0.0

    month_index = 11
    for index, month_end in enumerate(MONTH_CUM_END_S):
        if phase_s < month_end - 1.0e-9:
            month_index = index
            break

    month_start = (
        0.0
        if month_index == 0
        else MONTH_CUM_END_S[month_index - 1]
    )
    month_end = MONTH_CUM_END_S[month_index]
    q_set = MONTHLY_Q_M3_S[month_index]

    return {
        "profile_year_index": year_index + 1,
        "profile_month": month_index + 1,
        "profile_phase_day": phase_s / DAY,
        "profile_month_start_day": month_start / DAY,
        "profile_month_end_day": month_end / DAY,
        "field_flow_m3_h": SP2_MONTHLY_WATER_FLOW_M3_H[month_index],
        "q_set_m3_s": q_set,
        "q_set_over_q_base": q_set / Q_BASE,
    }


def dynamic_injection_rate(time_s):
    return float(dynamic_profile_state(time_s)["q_set_m3_s"])


def integrate_dynamic_injection(t0_s, t1_s):
    """精确积分分段常值动态注入流量，返回设定注入体积 m3。"""

    t0 = max(float(t0_s), 0.0)
    t1 = max(float(t1_s), t0)
    total = 0.0
    t = t0

    while t < t1 - 1.0e-9:
        state = dynamic_profile_state(t + 1.0e-7)
        year_start = math.floor(t / YEAR) * YEAR
        month_index = int(state["profile_month"]) - 1
        boundary = year_start + MONTH_CUM_END_S[month_index]

        if boundary <= t + 1.0e-9:
            boundary = year_start + YEAR

        segment_end = min(t1, boundary)
        total += float(state["q_set_m3_s"]) * (segment_end - t)
        t = segment_end

    return total


def write_dynamic_profile_csv():
    """输出一个年度循环的 12 个月动态注入边界表。"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = []
    start_s = 0.0

    for index in range(12):
        end_s = MONTH_CUM_END_S[index]
        rows.append({
            "month": index + 1,
            "field_water_flow_m3_h": SP2_MONTHLY_WATER_FLOW_M3_H[index],
            "month_duration_day": MONTH_DURATION_S[index] / DAY,
            "raw_model_q_m3_s": RAW_MONTHLY_Q_M3_S[index],
            "scale_factor": DYNAMIC_PROFILE_SCALE,
            "dynamic_q_m3_s": MONTHLY_Q_M3_S[index],
            "dynamic_q_m3_day": MONTHLY_Q_M3_S[index] * DAY,
            "q_over_q_base": MONTHLY_Q_M3_S[index] / Q_BASE,
            "month_start_day": start_s / DAY,
            "month_end_day": end_s / DAY,
        })
        start_s = end_s

    with open(
        PROFILE_CSV_PATH,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dynamic_annual = integrate_dynamic_injection(0.0, YEAR)
    constant_annual = Q_BASE * YEAR

    print("\n========== 动态边界年度检查 ==========")
    print(f"原始时长加权平均流量 = {RAW_WEIGHTED_MEAN_Q:.12e} m3/s")
    print(f"目标年平均流量 = {Q_BASE:.12e} m3/s")
    print(f"统一缩放系数 = {DYNAMIC_PROFILE_SCALE:.12e}")
    print(f"动态年度设定注入量 = {dynamic_annual:.12e} m3")
    print(f"固定年度设定注入量 = {constant_annual:.12e} m3")
    print(
        "相对差 = "
        f"{(dynamic_annual - constant_annual) / constant_annual:.12e}"
    )
    print(f"动态边界 CSV = {PROFILE_CSV_PATH}")
    print("=====================================\n")


class DynamicInjectionController:
    """每个求解步开始时更新第 0 个注入器的流量。"""

    def __init__(self, model):
        self.model = model

        if int(model.injector_number) < 1:
            raise RuntimeError("模型中没有注入器")

        self.injector = model.get_injector(0)
        if self.injector is None:
            raise RuntimeError("无法取得模型第 0 个注入器")

        self.current_state = None
        self.current_q = float("nan")
        self.update()

    def update(self):
        self.current_state = dynamic_profile_state(tfc.get_time(self.model))
        self.current_q = float(self.current_state["q_set_m3_s"])
        self.injector.value = self.current_q


# ------------------------- 初始 He 组成 -------------------------

def initial_composition():
    he_volume = SP2_GAS_WATER_RATIO * SP2_HE_Y
    he_mass_per_m3_water = he_volume / VM_STD * M_HE
    mass_ratio = he_mass_per_m3_water / 1000.0

    return {
        "h2o": 1.0 / (1.0 + mass_ratio),
        "he_sol": mass_ratio / (1.0 + mass_ratio),
    }


INIT_S = initial_composition()


# ------------------------- 基础函数 -------------------------

def is_reservoir(cell):
    return Z_MIN <= float(cell.pos[2]) <= Z_MAX


def find_well_cells(model, virtual_pos, name):
    virtual = model.get_nearest_cell(pos=virtual_pos)
    neighbors = [
        cell for cell in virtual.cells
        if is_reservoir(cell)
    ]

    if len(neighbors) != 1:
        raise RuntimeError(
            f"{name}应连接 1 个储层网格，实际为 {len(neighbors)} 个"
        )

    return virtual, neighbors[0]


def fid(model, name):
    value = model.find_fludef(name=name)

    if value is None:
        raise KeyError(f"模型中找不到组分：{name}")

    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]

    return [int(value)]


def component_mass(cell, fluid_id):
    return float(cell.get_fluid(*fluid_id).mass)


def mass_fraction(cell, component_id, liquid_id):
    liquid_mass = component_mass(cell, liquid_id)

    if liquid_mass <= 0.0:
        return 0.0

    return component_mass(cell, component_id) / liquid_mass


def density(cell, liquid_id):
    fluid = cell.get_fluid(*liquid_id)

    for name in ("den", "density"):
        try:
            value = getattr(fluid, name)
            value = value() if callable(value) else value
            value = float(value)

            if math.isfinite(value) and value > 0.0:
                return value
        except Exception:
            pass

    try:
        value = float(fluid.mass) / float(fluid.vol)

        if math.isfinite(value) and value > 0.0:
            return value
    except Exception:
        pass

    return RHO_FALLBACK


def ratio(a, b):
    if (
        not math.isfinite(a)
        or not math.isfinite(b)
        or abs(b) < 1.0e-300
    ):
        return float("nan")

    return a / b


def find_face(model, cell_a, cell_b):
    cell_ids = {int(cell_a.index), int(cell_b.index)}

    for face in model.faces:
        face_ids = {
            int(face.get_cell(0).index),
            int(face.get_cell(1).index),
        }
        if face_ids == cell_ids:
            return face

    raise RuntimeError("未找到井筒与储层之间的连接面")


def signed_outflow(face, reservoir, virtual, phase_id):
    """
    最近一步离开储层的液相体积：
    正值为储层流向虚拟井，负值为虚拟井流向储层。
    """

    dv = abs(float(face.get_dv(phase_id)))

    if reservoir.pre > virtual.pre:
        return dv, reservoir

    if reservoir.pre < virtual.pre:
        return -dv, virtual

    return 0.0, reservoir


# ------------------------- 建模 -------------------------

def create_model():
    mesh = create_xy(
        x_min=0.0,
        dx=DX,
        x_max=1000.0,
        y_min=0.0,
        dy=DY,
        y_max=1000.0,
        z_min=-0.5,
        z_max=0.5,
    )

    y_min, y_max = get_pos_range(mesh, 1)
    y_mid = 0.5 * (y_min + y_max)

    prod_pos = [X_PROD, y_mid, Z_PROD]
    inj_pos = [X_INJ, y_mid, Z_INJ]

    add_cell_face(
        mesh,
        pos=[X_PROD, y_mid, Z_RES],
        offset=[0.0, 0.0, Z_PROD],
        vol=PROD_VOL,
        area=2.104,
        length=1.0,
    )

    add_cell_face(
        mesh,
        pos=[X_INJ, y_mid, Z_RES],
        offset=[0.0, 0.0, Z_INJ],
        vol=INJ_VOL,
        area=2.104,
        length=1.0,
    )

    def get_s(_x, _y, z):
        if z < Z_MIN or z > Z_MAX:
            return {"h2o": 1.0, "he_sol": 0.0}

        return INIT_S.copy()

    def get_p(_x, _y, z):
        return P_PROD if z > Z_MAX else P_INIT

    def get_t(_x, _y, z):
        return T_INJ if z < Z_MIN else T_RES

    model = create(
        mesh=mesh,
        porosity=lambda _x, _y, _z: POROSITY,
        pore_modulus=100.0e6,
        p=get_p,
        temperature=get_t,
        denc=lambda _x, _y, _z: 2.0e6,
        s=get_s,
        perm=lambda _x, _y, _z: PERM,
        heat_cond=2.56,
        dist=0.8,
        dt_max=DT_MAX,
        gravity=[0.0, 0.0, 0.0],
        injectors=[
            {
                "pos": inj_pos,
                "fluid_id": "h2o",
                "value": dynamic_injection_rate(0.0),
            }
        ],
        use_mass=True,
    )

    prod_virtual, prod_res = find_well_cells(
        model,
        prod_pos,
        "生产井",
    )
    inj_virtual, inj_res = find_well_cells(
        model,
        inj_pos,
        "注入井",
    )

    return {
        "model": model,
        "prod_virtual": prod_virtual,
        "prod_res": prod_res,
        "inj_virtual": inj_virtual,
        "inj_res": inj_res,
    }


# ------------------------- CSV 监测 -------------------------

class Recorder:
    # 与固定流量简化版保持相同的公共列名，并增加动态边界信息
    FIELDS = [
        "step", "time_day", "time_year", "dt_s",
        "profile_year_index", "profile_month", "profile_phase_day",
        "field_flow_m3_h", "q_in_set_over_q_base",

        "q_in_set_m3_s", "q_in_actual_m3_s", "q_prod_m3_s",
        "q_prod_to_q_in", "q_prod_to_q_in_set",
        "cum_in_set_m3", "cum_in_baseline_m3",
        "cum_in_set_to_baseline_ratio",
        "cum_in_actual_m3", "cum_prod_m3",
        "cum_prod_to_cum_in",

        "p_prod_virtual_MPa", "p_prod_res_MPa",
        "p_inj_virtual_MPa", "p_inj_res_MPa",
        "p_res_avg_MPa", "p_res_min_MPa", "p_res_max_MPa",

        "prod_temperature_C", "normalized_temperature",
        "thermal_power_MW", "cum_heat_MWh",

        "he_mass_fraction", "he_concentration_mg_L", "he_C_over_C0",
        "he_rate_kg_day", "he_std_rate_m3_day",
        "cum_he_prod_kg", "cum_he_std_m3", "he_recovery_ratio",

        "res_h2o_mass_kg", "res_he_mass_kg",
        "h2o_mass_balance_error_kg", "he_mass_balance_error_kg",
        "h2o_mass_balance_error_rel", "he_mass_balance_error_rel",
    ]

    def __init__(self, data):
        self.model = data["model"]
        self.pv, self.pr = data["prod_virtual"], data["prod_res"]
        self.iv, self.ir = data["inj_virtual"], data["inj_res"]

        self.prod_face = find_face(self.model, self.pr, self.pv)
        self.inj_face = find_face(self.model, self.ir, self.iv)

        self.liq = fid(self.model, "liq")
        self.phase_id = int(self.liq[0])
        self.ids = {
            "h2o": fid(self.model, "h2o"),
            "he": fid(self.model, "he_sol"),
        }

        self.temp_key = self.model.get_cell_key("temperature")
        if self.temp_key is None:
            self.temp_key = tfc.cell_keys(self.model).temperature

        self.res_cells = [
            cell for cell in self.model.cells
            if is_reservoir(cell)
        ]

        self.initial_mass = {
            name: self.sum_mass(name)
            for name in self.ids
        }

        self.prod_mass_net = {"h2o": 0.0, "he": 0.0}
        self.inj_out_mass_net = {"h2o": 0.0, "he": 0.0}

        self.cum_in_set = 0.0
        self.cum_in = 0.0
        self.cum_prod = 0.0
        self.cum_he = 0.0
        self.cum_heat = 0.0

        self.last_step_time = float(tfc.get_time(self.model))
        self.next_record = RECORD_INTERVAL
        self.last_record = -1.0

        self.dt = 0.0
        self.profile = dynamic_profile_state(0.0)
        self.q_set = float(self.profile["q_set_m3_s"])
        self.q_in = 0.0
        self.q_prod = 0.0

        self.prod_temp = T_RES
        self.prod_den = density(self.pr, self.liq)
        self.he_fraction = mass_fraction(
            self.pr,
            self.ids["he"],
            self.liq,
        )
        self.he_c0 = self.prod_den * self.he_fraction
        self.he_rate = 0.0
        self.power = 0.0

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        with open(
            CSV_PATH,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            csv.DictWriter(
                file,
                fieldnames=self.FIELDS,
            ).writeheader()

        self.write(force=True)

    def sum_mass(self, name):
        return sum(
            component_mass(cell, self.ids[name])
            for cell in self.res_cells
        )

    def update(self):
        now = float(tfc.get_time(self.model))
        dt = now - self.last_step_time

        if dt <= 0.0:
            return

        prod_dv, prod_upstream = signed_outflow(
            self.prod_face,
            self.pr,
            self.pv,
            self.phase_id,
        )
        inj_dv, inj_upstream = signed_outflow(
            self.inj_face,
            self.ir,
            self.iv,
            self.phase_id,
        )

        self.dt = dt

        # face.get_dv 对应刚结束的时间区间，使用区间中点代表该步流量
        middle_time = 0.5 * (self.last_step_time + now)
        self.profile = dynamic_profile_state(middle_time)
        self.q_set = float(self.profile["q_set_m3_s"])
        self.cum_in_set += integrate_dynamic_injection(
            self.last_step_time,
            now,
        )

        self.q_prod = max(prod_dv / dt, 0.0)
        self.q_in = max(-inj_dv / dt, 0.0)

        self.cum_prod += max(prod_dv, 0.0)
        self.cum_in += max(-inj_dv, 0.0)

        self.prod_temp = float(
            prod_upstream.get_attr(self.temp_key)
        )
        self.prod_den = density(prod_upstream, self.liq)

        for name, component_id in self.ids.items():
            prod_fraction = mass_fraction(
                prod_upstream,
                component_id,
                self.liq,
            )
            inj_fraction = mass_fraction(
                inj_upstream,
                component_id,
                self.liq,
            )

            prod_dm = (
                prod_dv
                * density(prod_upstream, self.liq)
                * prod_fraction
            )
            inj_dm = (
                inj_dv
                * density(inj_upstream, self.liq)
                * inj_fraction
            )

            self.prod_mass_net[name] += prod_dm
            self.inj_out_mass_net[name] += inj_dm

            if name == "he":
                self.he_fraction = prod_fraction
                self.he_rate = max(prod_dm, 0.0) / dt
                self.cum_he += max(prod_dm, 0.0)

        self.power = (
            self.q_prod
            * self.prod_den
            * CP_WATER
            * max(self.prod_temp - T_INJ, 0.0)
        )
        self.cum_heat += self.power * dt
        self.last_step_time = now

        if now >= self.next_record:
            self.write()

            while self.next_record <= now:
                self.next_record += RECORD_INTERVAL

    def make_row(self):
        time_s = float(tfc.get_time(self.model))
        pressures = [
            float(cell.pre)
            for cell in self.res_cells
        ]

        res_mass = {
            name: self.sum_mass(name)
            for name in self.ids
        }

        error = {
            name: (
                res_mass[name]
                + self.prod_mass_net[name]
                + self.inj_out_mass_net[name]
                - self.initial_mass[name]
            )
            for name in self.ids
        }

        he_concentration = self.prod_den * self.he_fraction
        he_std_rate = self.he_rate / M_HE * VM_STD * DAY
        cum_he_std = self.cum_he / M_HE * VM_STD
        baseline_volume = Q_BASE * time_s

        return {
            "step": int(tfc.get_step(self.model)),
            "time_day": time_s / DAY,
            "time_year": time_s / YEAR,
            "dt_s": self.dt,

            "profile_year_index": int(
                self.profile["profile_year_index"]
            ),
            "profile_month": int(self.profile["profile_month"]),
            "profile_phase_day": float(
                self.profile["profile_phase_day"]
            ),
            "field_flow_m3_h": float(
                self.profile["field_flow_m3_h"]
            ),
            "q_in_set_over_q_base": float(
                self.profile["q_set_over_q_base"]
            ),

            "q_in_set_m3_s": self.q_set,
            "q_in_actual_m3_s": self.q_in,
            "q_prod_m3_s": self.q_prod,
            "q_prod_to_q_in": ratio(self.q_prod, self.q_in),
            "q_prod_to_q_in_set": ratio(
                self.q_prod,
                self.q_set,
            ),

            "cum_in_set_m3": self.cum_in_set,
            "cum_in_baseline_m3": baseline_volume,
            "cum_in_set_to_baseline_ratio": ratio(
                self.cum_in_set,
                baseline_volume,
            ),
            "cum_in_actual_m3": self.cum_in,
            "cum_prod_m3": self.cum_prod,
            "cum_prod_to_cum_in": ratio(
                self.cum_prod,
                self.cum_in,
            ),

            "p_prod_virtual_MPa": float(self.pv.pre) / 1.0e6,
            "p_prod_res_MPa": float(self.pr.pre) / 1.0e6,
            "p_inj_virtual_MPa": float(self.iv.pre) / 1.0e6,
            "p_inj_res_MPa": float(self.ir.pre) / 1.0e6,
            "p_res_avg_MPa": sum(pressures) / len(pressures) / 1.0e6,
            "p_res_min_MPa": min(pressures) / 1.0e6,
            "p_res_max_MPa": max(pressures) / 1.0e6,

            "prod_temperature_C": self.prod_temp - 273.15,
            "normalized_temperature": ratio(
                self.prod_temp - T_INJ,
                T_RES - T_INJ,
            ),
            "thermal_power_MW": self.power / 1.0e6,
            "cum_heat_MWh": self.cum_heat / 3.6e9,

            "he_mass_fraction": self.he_fraction,
            "he_concentration_mg_L": he_concentration * 1000.0,
            "he_C_over_C0": ratio(
                he_concentration,
                self.he_c0,
            ),
            "he_rate_kg_day": self.he_rate * DAY,
            "he_std_rate_m3_day": he_std_rate,
            "cum_he_prod_kg": self.cum_he,
            "cum_he_std_m3": cum_he_std,
            "he_recovery_ratio": ratio(
                self.cum_he,
                self.initial_mass["he"],
            ),

            "res_h2o_mass_kg": res_mass["h2o"],
            "res_he_mass_kg": res_mass["he"],
            "h2o_mass_balance_error_kg": error["h2o"],
            "he_mass_balance_error_kg": error["he"],
            "h2o_mass_balance_error_rel": ratio(
                error["h2o"],
                self.initial_mass["h2o"],
            ),
            "he_mass_balance_error_rel": ratio(
                error["he"],
                self.initial_mass["he"],
            ),
        }

    def write(self, force=False):
        now = float(tfc.get_time(self.model))

        if now <= self.last_record and not force:
            return

        if abs(now - self.last_record) <= 1.0e-12:
            return

        row = self.make_row()

        with open(
            CSV_PATH,
            "a",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            csv.DictWriter(
                file,
                fieldnames=self.FIELDS,
            ).writerow(row)

        self.last_record = now

        print(
            f"{row['time_year']:.3f} year | "
            f"month={row['profile_month']:02d} | "
            f"Qset={row['q_in_set_m3_s']:.6e} m3/s | "
            f"Qp/Qi={row['q_prod_to_q_in']:.4f} | "
            f"T={row['prod_temperature_C']:.2f} C | "
            f"He C/C0={row['he_C_over_C0']:.4f}"
        )

    def finish(self):
        self.update()
        self.write(force=True)
        print(f"\n动态历史 CSV 已保存：{CSV_PATH}\n")


# ------------------------- 求解 -------------------------

def solve(data):
    model = data["model"]

    pressure_controller = PressureController(
        cell=data["prod_virtual"],
        t=[-1.0e20, 1.0e20],
        p=[P_PROD, P_PROD],
        modify_pore=False,
    )
    pressure_controller.update(
        t=tfc.get_time(model),
        modify_pore=False,
    )

    injection_controller = DynamicInjectionController(model)
    recorder = Recorder(data)

    injection_name = "update_dynamic_injection_rate"
    pressure_name = "update_production_pressure"
    recorder_name = "record_dynamic_history"

    def update_pressure():
        pressure_controller.update(
            t=tfc.get_time(model),
            modify_pore=False,
        )

    # 动态流量先更新，随后控制生产压力和记录结果
    add_step_setting(
        model=model,
        start=0,
        step=1,
        name=injection_name,
    )
    add_step_setting(
        model=model,
        start=0,
        step=1,
        name=pressure_name,
    )
    add_step_setting(
        model=model,
        start=0,
        step=1,
        name=recorder_name,
    )

    def extra_plot():
        # 绘图前再次更新当前动态流量并校正生产井压力
        injection_controller.update()
        pressure_controller.update(
            t=tfc.get_time(model),
            modify_pore=False,
        )
        show_xy(model)

    print("\n========== 动态工况设置 ==========")
    print(f"动态年平均流量 = {Q_BASE:.6e} m3/s")
    print(f"动态最小月流量 = {min(MONTHLY_Q_M3_S):.6e} m3/s")
    print(f"动态最大月流量 = {max(MONTHLY_Q_M3_S):.6e} m3/s")
    print(f"生产压力 = {P_PROD / 1.0e6:.3f} MPa")
    print(f"模拟时间 = {TIME_MAX / YEAR:.1f} year")
    print(f"CSV 间隔 = {RECORD_INTERVAL / DAY:.1f} day")
    print(f"动态历史 CSV = {CSV_PATH}")
    print("=================================\n")

    tfc.solve(
        model=model,
        extra_plot=extra_plot,
        slots={
            injection_name: injection_controller.update,
            pressure_name: update_pressure,
            recorder_name: recorder.update,
        },
        time_max=TIME_MAX,
        state_hint=(
            "25-year repeated monthly dynamic injection "
            "and constant production pressure"
        ),
    )

    pressure_controller.update(
        t=tfc.get_time(model),
        modify_pore=False,
    )
    recorder.finish()

    print("========== 计算结束 ==========")
    print(f"最终时间 = {tfc.get_time(model) / YEAR:.6f} year")
    print(f"最终步数 = {tfc.get_step(model)}")
    print(
        "最终生产井压力 = "
        f"{float(data['prod_virtual'].pre) / 1.0e6:.6f} MPa"
    )
    print("==============================\n")


def main():
    print(f"初始 He 质量份额 = {INIT_S['he_sol']:.12e}")
    write_dynamic_profile_csv()
    solve(create_model())


if __name__ == "__main__":
    gui.execute(main)
