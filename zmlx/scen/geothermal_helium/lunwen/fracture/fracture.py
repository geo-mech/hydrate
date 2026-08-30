# -*- coding: utf-8 -*-
"""
简化版：纯随机裂缝网络下 25 年周期性动态注入流量—定压生产 He 被动运移模型

本文件负责：
1. 创建二维 xy 一注一采模型；
2. 按 SP2 前 12 个月水流量逐月更新注入边界，并逐年重复；
3. 每一步维持生产井定压；
4. 创建并施加固定随机种子控制的纯随机裂缝网络；
5. 调用 show_xy(model) 显示压力、温度和 He 空间场。

"""

import math

import numpy as np
import zmlx.tfc as tfc
from zmlx import (
    Dfn2,
    PressureController,
    point_distance,
    seg_point_distance,
    set_srand,
)
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.helium.fluid import create
from zmlx.scen.geothermal_helium.helium.fracture.show import show_xy
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
X_MIN, X_MAX = 0.0, 1000.0
Y_MIN, Y_MAX = 0.0, 1000.0
Z_MIN, Z_MAX = -2.0, 2.0

DAY = 24.0 * 3600.0
YEAR = 365.25 * DAY
TIME_MAX = 25.0 * YEAR
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


# ------------------------- 随机裂缝网络 -------------------------

USE_FRACTURE = True
RANDOM_SEED = 20260712
RANDOM_FRACTURE_NUMBER = 80
RANDOM_LENGTH_MIN = 60.0
RANDOM_LENGTH_MAX = 220.0
RANDOM_ANGLE_MIN = 0.0
RANDOM_ANGLE_MAX = 180.0
FRACTURE_PERM = 5.0e-11
Z_FRAC = 0.0


def validate_fracture(fracture):
    """检查裂缝端点并统一数据类型。"""

    value = dict(fracture)
    value["fracture_id"] = str(value["fracture_id"])

    for key in ("x0", "y0", "x1", "y1"):
        value[key] = float(value[key])

    if not (
        X_MIN <= value["x0"] <= X_MAX
        and X_MIN <= value["x1"] <= X_MAX
    ):
        raise ValueError(
            f"裂缝 {value['fracture_id']} 的 x 坐标超出模型范围"
        )

    if not (
        Y_MIN <= value["y0"] <= Y_MAX
        and Y_MIN <= value["y1"] <= Y_MAX
    ):
        raise ValueError(
            f"裂缝 {value['fracture_id']} 的 y 坐标超出模型范围"
        )

    if math.hypot(
        value["x1"] - value["x0"],
        value["y1"] - value["y0"],
    ) <= 0.0:
        raise ValueError(
            f"裂缝 {value['fracture_id']} 的起点和终点重合"
        )

    return value


def generate_random_fractures():
    """生成固定随机种子控制的纯随机裂缝网络。"""

    if RANDOM_FRACTURE_NUMBER <= 0:
        raise ValueError("RANDOM_FRACTURE_NUMBER 必须大于 0")

    if RANDOM_LENGTH_MIN <= 0.0:
        raise ValueError("RANDOM_LENGTH_MIN 必须大于 0")

    if RANDOM_LENGTH_MAX < RANDOM_LENGTH_MIN:
        raise ValueError(
            "RANDOM_LENGTH_MAX 不能小于 RANDOM_LENGTH_MIN"
        )

    rng = np.random.default_rng(RANDOM_SEED)
    fractures = []

    for index in range(RANDOM_FRACTURE_NUMBER):
        length = float(
            rng.uniform(RANDOM_LENGTH_MIN, RANDOM_LENGTH_MAX)
        )
        angle_degree = float(
            rng.uniform(RANDOM_ANGLE_MIN, RANDOM_ANGLE_MAX)
        )
        theta = math.radians(angle_degree)

        half_dx = 0.5 * length * math.cos(theta)
        half_dy = 0.5 * length * math.sin(theta)

        center_x = float(
            rng.uniform(
                X_MIN + abs(half_dx),
                X_MAX - abs(half_dx),
            )
        )
        center_y = float(
            rng.uniform(
                Y_MIN + abs(half_dy),
                Y_MAX - abs(half_dy),
            )
        )

        fractures.append(
            validate_fracture({
                "fracture_id": f"R{index + 1:03d}",
                "x0": center_x - half_dx,
                "y0": center_y - half_dy,
                "x1": center_x + half_dx,
                "y1": center_y + half_dy,
                "source_type": "random",
            })
        )

    total_length = sum(
        math.hypot(
            fracture["x1"] - fracture["x0"],
            fracture["y1"] - fracture["y0"],
        )
        for fracture in fractures
    )
    model_area = (X_MAX - X_MIN) * (Y_MAX - Y_MIN)

    print("\n========== 纯随机裂缝网络 ==========")
    print(f"随机种子 = {RANDOM_SEED}")
    print(f"随机裂缝数量 = {len(fractures)}")
    print(f"裂缝总长度 = {total_length:.6f} m")
    print(f"P21 = {total_length / model_area:.8e} 1/m")
    print(f"裂缝渗透率 = {FRACTURE_PERM:.6e} m2")
    print(f"裂缝/基质渗透率倍数 = {FRACTURE_PERM / PERM:.2f}")
    print("人工主通道 = 无")
    print("裂缝交点计算 = 关闭")
    print("====================================\n")

    return fractures


def add_fractures_like_egs(model, source_fractures):
    """
    按 EGS 示例将每条随机线段映射为一系列高渗透 face。

    两个正式裂缝工况必须使用相同的随机种子和几何参数，
    从而保证固定流量与动态流量之间只存在注入边界差异。
    """

    set_srand(RANDOM_SEED)

    dfn = Dfn2()
    dfn.range = [X_MIN, Y_MIN, X_MAX, Y_MAX]

    fracture_ids = []
    source_types = []

    for fracture in source_fractures:
        dfn.add_frac(
            x0=fracture["x0"],
            y0=fracture["y0"],
            x1=fracture["x1"],
            y1=fracture["y1"],
        )
        fracture_ids.append(fracture["fracture_id"])
        source_types.append(fracture.get("source_type", "random"))

    fracture_records = []
    all_face_ids = []

    for fracture_id, source_type, geometry in zip(
        fracture_ids,
        source_types,
        dfn.get_fractures(),
    ):
        x0, y0, x1, y1 = [float(value) for value in geometry]

        cell_beg = model.get_nearest_cell(
            pos=[x0, y0, Z_FRAC]
        )
        cell_end = model.get_nearest_cell(
            pos=[x1, y1, Z_FRAC]
        )

        path_cell_ids = [int(cell_beg.index)]
        face_ids = []
        count = 0

        def get_dist(cell_pos):
            return (
                seg_point_distance(
                    [[x0, y0], [x1, y1]],
                    cell_pos[0:2],
                )
                + point_distance(cell_pos, cell_end.pos)
            )

        while cell_beg.index != cell_end.index:
            neighbors = list(cell_beg.cells)

            if not neighbors:
                raise RuntimeError(
                    f"裂缝 {fracture_id} 在 cell "
                    f"{cell_beg.index} 没有相邻 cell"
                )

            distances = [
                get_dist(cell.pos)
                for cell in neighbors
            ]
            next_index = min(
                range(len(distances)),
                key=distances.__getitem__,
            )

            cell = cell_beg.get_cell(next_index)
            face = model.add_face(cell_beg, cell)
            tfc.set_face(face=face, perm=FRACTURE_PERM)

            face_ids.append(int(face.index))
            all_face_ids.append(int(face.index))
            path_cell_ids.append(int(cell.index))

            count += 1
            if count > model.cell_number:
                raise RuntimeError(
                    f"裂缝 {fracture_id} 未能到达终点，"
                    "相邻 cell 搜索可能出现循环"
                )

            cell_beg = cell

        fracture_records.append({
            "fracture_id": fracture_id,
            "source_type": source_type,
            "geometry": [x0, y0, x1, y1],
            "cell_ids": path_cell_ids,
            "face_ids": sorted(set(face_ids)),
            "mapped_xy": [
                [
                    float(model.get_cell(cell_id).pos[0]),
                    float(model.get_cell(cell_id).pos[1]),
                ]
                for cell_id in path_cell_ids
            ],
            "face_perm": FRACTURE_PERM,
        })

    model.temps["fracture_records"] = fracture_records
    model.temps["fracture_face_ids"] = sorted(set(all_face_ids))
    model.temps["fracture_face_perm"] = FRACTURE_PERM
    model.temps["fracture_connectivity"] = {}
    model.temps["random_fracture_metadata"] = {
        "fracture_mode": "fully_random",
        "random_seed": RANDOM_SEED,
        "random_fracture_number": RANDOM_FRACTURE_NUMBER,
        "total_fracture_number": len(fracture_records),
        "length_min": RANDOM_LENGTH_MIN,
        "length_max": RANDOM_LENGTH_MAX,
        "angle_min": RANDOM_ANGLE_MIN,
        "angle_max": RANDOM_ANGLE_MAX,
    }

    return fracture_records


# ------------------------- 建模 -------------------------

def create_model():
    mesh = create_xy(
        x_min=X_MIN,
        dx=DX,
        x_max=X_MAX,
        y_min=Y_MIN,
        dy=DY,
        y_max=Y_MAX,
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

    model.temps["injector_xy"] = [
        float(inj_res.pos[0]),
        float(inj_res.pos[1]),
    ]
    model.temps["producer_xy"] = [
        float(prod_res.pos[0]),
        float(prod_res.pos[1]),
    ]

    source_fractures = generate_random_fractures()
    fracture_records = add_fractures_like_egs(
        model,
        source_fractures,
    )

    return {
        "model": model,
        "prod_virtual": prod_virtual,
        "prod_res": prod_res,
        "inj_virtual": inj_virtual,
        "inj_res": inj_res,
        "fracture_records": fracture_records,
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

    print("\n========== 裂缝动态工况设置 ==========")
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
            "25-year fractured reservoir with repeated monthly "
            "dynamic injection and constant production pressure"
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
