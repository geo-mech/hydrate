# -*- coding: utf-8 -*-
"""
简化版：25 年周期性动态注入流量—定压生产 He 被动运移模型

本文件负责：
1. 创建二维 xy 一注一采模型；
2. 按 SP2 前 12 个月水流量逐月更新注入边界，并逐年重复；
3. 每一步维持生产井定压；
4. 调用 show_xy(model) 显示压力、温度和 He 空间场。

"""

import math

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
TIME_MAX = 1.0 * YEAR
DT_MAX = 12.0 * 3600.0
M_HE = 4.0026e-3
VM_STD = 22.414e-3

SP2_HE_Y = 2.240 / 100.0
SP2_GAS_WATER_RATIO = 24.2 / 100.0

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
    injection_name = "update_dynamic_injection_rate"
    pressure_name = "update_production_pressure"

    def update_pressure():
        pressure_controller.update(
            t=tfc.get_time(model),
            modify_pore=False,
        )

    # 动态流量先更新，随后控制生产压力
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
    print("=================================\n")

    tfc.solve(
        model=model,
        extra_plot=extra_plot,
        slots={
            injection_name: injection_controller.update,
            pressure_name: update_pressure,
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
    solve(create_model())


if __name__ == "__main__":
    gui.execute(main)
