# -*- coding: utf-8 -*-

"""
水平二维一注一采 + 溶解气体被动运移 + 纯随机裂缝网络
本算例只研究随机裂缝网络本身的影响：
1. 使用固定随机种子生成可复现随机裂缝；
2. 不添加任何人工主通道；
3. 裂缝按 EGS 示例逐条映射为高渗透 face；
4. 裂缝网络图由外部 show5.py 绘制，只显示裂缝线。
"""

import math
import numpy as np
from typing import Dict, List, Tuple

import zmlx.tfc as tfc
from zmlx import (
    Dfn2,
    PressureController,
    point_distance,
    seg_point_distance,
    set_srand,
)
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.exsolve.fluid import create
from zmlx.scen.geothermal_helium.fracture.show5 import show_xy
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.tfc._step import add_setting as add_step_setting
from zmlx.ui import gui


# ============================================================
# 1. 时间参数
# ============================================================

DAY = 24.0 * 3600.0
YEAR = 365.25 * DAY

TIME_MAX = 10.0 * YEAR
DT_MAX = 10.0 * DAY


# ============================================================
# 2. 储层、网格与井参数
# ============================================================

X_MIN = 0.0
X_MAX = 1000.0
Y_MIN = 0.0
Y_MAX = 1000.0

DX = 10.0
DY = 10.0

Z_MIN = -0.5
Z_MAX = 0.5
Z_RES = 0.0

RESERVOIR_Z_MIN = -2.0
RESERVOIR_Z_MAX = 2.0

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

Q_IN = 1.3e-4

X_INJ = 300.0
X_PROD = 700.0

Z_PROD_VIRTUAL = 10.0
Z_INJ_VIRTUAL = -10.0

PROD_VIRTUAL_VOL = 100.0
INJ_VIRTUAL_VOL = 100.0

WELL_FACE_AREA = 2.104
WELL_FACE_LENGTH = 1.0


# ============================================================
# 3. EGS 风格随机裂缝设置
# ============================================================

USE_FRACTURE = True

# 本算例只包含随机裂缝，不设置任何人工骨架或主通道。

# 固定随机种子，保证每次生成相同的裂缝几何。
RANDOM_SEED = 20260712

# 随机裂缝数量、长度范围和角度范围。
RANDOM_FRACTURE_NUMBER = 80
RANDOM_LENGTH_MIN = 60.0
RANDOM_LENGTH_MAX = 220.0
RANDOM_ANGLE_MIN = 0.0
RANDOM_ANGLE_MAX = 180.0

FRACTURE_PERM = 5.0e-11
Z_FRAC = 0.0

# 裂缝图由外部 show5.py 统一绘制。


# ============================================================
# 4. SP2 气体组成与气水比
# ============================================================

SP2_HE_Y_RAW = 2.240 / 100.0
SP2_N2_Y_RAW = 73.800 / 100.0
SP2_CH4_Y_RAW = 12.800 / 100.0
SP2_GAS_WATER_RATIO = 24.2 / 100.0

# 不对 He、N2、CH4 的原始体积分数进行归一化。
# SP2_GAS_WATER_RATIO 表示全部产出气体与水的体积比，
# 因此各目标气体应直接使用其在全部气体中的原始体积分数。
NORMALIZE_SELECTED_GASES = False


def prepare_selected_gas_composition(
        y_he: float,
        y_n2: float,
        y_ch4: float
) -> Tuple[float, float, float]:
    total = y_he + y_n2 + y_ch4
    if total <= 0.0:
        raise ValueError("He、N2、CH4 体积分数之和必须大于0。")
    if total > 1.0 + 1.0e-12:
        raise ValueError(
            "He、N2、CH4 原始体积分数之和不能大于1，"
            f"当前为 {total:.8f}。"
        )

    ignored_fraction = max(0.0, 1.0 - total)

    print("\n========== SP2 气体组成 ==========")
    print(f"He、N2、CH4 原始体积分数之和 = {total:.6f}")
    print("气体组分不归一化，直接使用原始体积分数换算绝对含量。")
    print(f"未建模其他气体体积分数 = {ignored_fraction:.6f}")
    print(f"He  = {y_he:.8f}")
    print(f"N2  = {y_n2:.8f}")
    print(f"CH4 = {y_ch4:.8f}")
    print("==================================\n")

    return y_he, y_n2, y_ch4


SP2_HE_Y, SP2_N2_Y, SP2_CH4_Y = prepare_selected_gas_composition(
    SP2_HE_Y_RAW,
    SP2_N2_Y_RAW,
    SP2_CH4_Y_RAW
)


def gas_water_to_mass_fractions(
        gas_water_ratio: float,
        y_he: float,
        y_n2: float,
        y_ch4: float,
        rho_w: float = 1000.0,
        vm: float = 22.414e-3
) -> Dict[str, float]:
    if gas_water_ratio < 0.0:
        raise ValueError("gas_water_ratio 不能小于0。")
    if rho_w <= 0.0 or vm <= 0.0:
        raise ValueError("rho_w 和 vm 必须大于0。")

    m_he = gas_water_ratio * y_he / vm * 4.0026e-3
    m_n2 = gas_water_ratio * y_n2 / vm * 28.0134e-3
    m_ch4 = gas_water_ratio * y_ch4 / vm * 16.043e-3
    m_water = rho_w

    total_mass = m_water + m_he + m_n2 + m_ch4

    result = dict(
        h2o=m_water / total_mass,
        he_sol=m_he / total_mass,
        n2_sol=m_n2 / total_mass,
        ch4_sol=m_ch4 / total_mass
    )

    print("========== SP2 初始质量份额 ==========")
    for key, value in result.items():
        print(f"{key:8s} = {value:.12e}")
    print(f"质量份额之和 = {sum(result.values()):.12f}")
    print("======================================\n")

    return result


SP2_INIT_S = gas_water_to_mass_fractions(
    gas_water_ratio=SP2_GAS_WATER_RATIO,
    y_he=SP2_HE_Y,
    y_n2=SP2_N2_Y,
    y_ch4=SP2_CH4_Y
)




# ============================================================
# 5. 井筒与储层 cell
# ============================================================


def is_reservoir_cell(cell) -> bool:
    return RESERVOIR_Z_MIN <= float(cell.pos[2]) <= RESERVOIR_Z_MAX


def get_well_cells(model, virtual_pos, well_name: str):
    virtual_cell = model.get_nearest_cell(pos=virtual_pos)
    reservoir_neighbors = [
        cell for cell in virtual_cell.cells
        if is_reservoir_cell(cell)
    ]

    if len(reservoir_neighbors) != 1:
        raise RuntimeError(
            f"{well_name}虚拟井筒应只连接1个真实储层 cell，"
            f"当前找到 {len(reservoir_neighbors)} 个。"
        )

    reservoir_cell = reservoir_neighbors[0]

    print(f"{well_name}虚拟井筒 cell: index={virtual_cell.index}, pos={virtual_cell.pos}")
    print(f"{well_name}连接储层 cell: index={reservoir_cell.index}, pos={reservoir_cell.pos}")

    return virtual_cell, reservoir_cell


# ============================================================
# 6. 随机裂缝生成与 EGS 风格添加
# ============================================================


def validate_fracture(fracture: Dict) -> Dict:
    """检查一条裂缝并统一坐标类型。"""
    value = dict(fracture)
    fracture_id = str(value["fracture_id"])

    for key in ["x0", "y0", "x1", "y1"]:
        value[key] = float(value[key])

    x0, y0 = value["x0"], value["y0"]
    x1, y1 = value["x1"], value["y1"]

    if not (X_MIN <= x0 <= X_MAX and X_MIN <= x1 <= X_MAX):
        raise ValueError(f"裂缝 {fracture_id} 的 x 坐标超出模型范围。")
    if not (Y_MIN <= y0 <= Y_MAX and Y_MIN <= y1 <= Y_MAX):
        raise ValueError(f"裂缝 {fracture_id} 的 y 坐标超出模型范围。")
    if math.hypot(x1 - x0, y1 - y0) <= 0.0:
        raise ValueError(f"裂缝 {fracture_id} 的起点和终点重合。")

    value["fracture_id"] = fracture_id
    return value


def generate_random_fractures() -> List[Dict]:
    """
    生成固定数量、可复现且端点位于模型内部的随机裂缝。

    随机几何只负责给出线段端点；后续网格映射完全使用 EGS 的
    相邻 cell 搜索方法，不处理任何裂缝交点。
    """
    if RANDOM_FRACTURE_NUMBER <= 0:
        raise ValueError("RANDOM_FRACTURE_NUMBER 必须大于0。")
    if RANDOM_LENGTH_MIN <= 0.0:
        raise ValueError("RANDOM_LENGTH_MIN 必须大于0。")
    if RANDOM_LENGTH_MAX < RANDOM_LENGTH_MIN:
        raise ValueError("RANDOM_LENGTH_MAX 不能小于 RANDOM_LENGTH_MIN。")
    if RANDOM_ANGLE_MAX <= RANDOM_ANGLE_MIN:
        raise ValueError("RANDOM_ANGLE_MAX 必须大于 RANDOM_ANGLE_MIN。")

    rng = np.random.default_rng(RANDOM_SEED)
    fractures = []

    for index in range(RANDOM_FRACTURE_NUMBER):
        length = float(rng.uniform(RANDOM_LENGTH_MIN, RANDOM_LENGTH_MAX))
        angle_degree = float(rng.uniform(RANDOM_ANGLE_MIN, RANDOM_ANGLE_MAX))
        theta = math.radians(angle_degree)

        half_dx = 0.5 * length * math.cos(theta)
        half_dy = 0.5 * length * math.sin(theta)

        center_x = float(rng.uniform(
            X_MIN + abs(half_dx),
            X_MAX - abs(half_dx)
        ))
        center_y = float(rng.uniform(
            Y_MIN + abs(half_dy),
            Y_MAX - abs(half_dy)
        ))

        fractures.append(validate_fracture(dict(
            fracture_id=f"R{index + 1:03d}",
            x0=center_x - half_dx,
            y0=center_y - half_dy,
            x1=center_x + half_dx,
            y1=center_y + half_dy,
            source_type="random"
        )))

    return fractures


def create_fracture_geometry() -> List[Dict]:
    """只返回固定随机种子生成的随机裂缝。"""
    fractures = generate_random_fractures()

    total_length = sum(
        math.hypot(
            fracture["x1"] - fracture["x0"],
            fracture["y1"] - fracture["y0"]
        )
        for fracture in fractures
    )
    model_area = (X_MAX - X_MIN) * (Y_MAX - Y_MIN)
    p21 = total_length / model_area

    print("\n==========纯随机裂缝网络 ==========")
    print(f"随机种子 = {RANDOM_SEED}")
    print(f"随机裂缝数量 = {len(fractures)}")
    print(f"裂缝总长度 = {total_length:.6f} m")
    print(f"P21 = {p21:.8e} 1/m")
    print("人工主通道 = 无")
    print("裂缝交点计算 = 关闭")
    print("============================================\n")

    return fractures


def add_fractures_like_egs(model, source_fractures: List[Dict]) -> List[Dict]:
    """
    按照 EGS 示例逐条添加裂缝。

    每条裂缝独立从起点 cell 走到终点 cell，不计算几何交点，
    也不强制随机裂缝之间形成网格连通关系。
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
            y1=fracture["y1"]
        )
        fracture_ids.append(fracture["fracture_id"])
        source_types.append(fracture.get("source_type", "random"))

    fractures = dfn.get_fractures()


    fracture_records = []
    all_face_ids = []

    for fracture_id, source_type, geometry in zip(
            fracture_ids, source_types, fractures
    ):
        x0, y0, x1, y1 = [float(value) for value in geometry]

        print(
            f"add fracture {fracture_id}: "
            f"{[x0, y0, x1, y1]}. ",
            end=""
        )

        cell_beg = model.get_nearest_cell(pos=[x0, y0, Z_FRAC])
        cell_end = model.get_nearest_cell(pos=[x1, y1, Z_FRAC])

        path_cell_ids = [int(cell_beg.index)]
        face_ids = []
        count = 0

        def get_dist(cell_pos):
            return (
                seg_point_distance(
                    [[x0, y0], [x1, y1]],
                    cell_pos[0:2]
                )
                + point_distance(cell_pos, cell_end.pos)
            )

        while cell_beg.index != cell_end.index:
            dist = [get_dist(cell.pos) for cell in cell_beg.cells]

            if len(dist) == 0:
                raise RuntimeError(
                    f"裂缝 {fracture_id} 在 cell "
                    f"{cell_beg.index} 没有相邻 cell。"
                )

            idx = 0
            for i in range(1, len(dist)):
                if dist[i] < dist[idx]:
                    idx = i

            cell = cell_beg.get_cell(idx)
            face = model.add_face(cell_beg, cell)
            tfc.set_face(face=face, perm=FRACTURE_PERM)

            face_ids.append(int(face.index))
            all_face_ids.append(int(face.index))
            path_cell_ids.append(int(cell.index))

            count += 1
            if count > model.cell_number:
                raise RuntimeError(
                    f"裂缝 {fracture_id} 未能到达终点，"
                    "相邻 cell 搜索可能出现循环。"
                )

            cell_beg = cell

        print(f"count of face modified: {count}")

        fracture_records.append(dict(
            fracture_id=fracture_id,
            source_type=source_type,
            geometry=[x0, y0, x1, y1],
            cell_ids=path_cell_ids,
            face_ids=sorted(set(face_ids)),
            mapped_xy=[
                [
                    float(model.get_cell(cell_id).pos[0]),
                    float(model.get_cell(cell_id).pos[1])
                ]
                for cell_id in path_cell_ids
            ],
            face_perm=FRACTURE_PERM
        ))

    # 直接把裂缝记录交给外部 show5.py。
    # show5.py 只绘制裂缝线，不绘制裂缝编号、端点或交点。
    model.temps["fracture_records"] = fracture_records
    model.temps["fracture_face_ids"] = sorted(set(all_face_ids))
    model.temps["fracture_face_perm"] = FRACTURE_PERM
    model.temps["fracture_connectivity"] = {}
    model.temps["random_fracture_metadata"] = dict(
        fracture_mode="fully_random",
        random_seed=RANDOM_SEED,
        random_fracture_number=RANDOM_FRACTURE_NUMBER,
        total_fracture_number=len(fracture_records),
        length_min=RANDOM_LENGTH_MIN,
        length_max=RANDOM_LENGTH_MAX,
        angle_min=RANDOM_ANGLE_MIN,
        angle_max=RANDOM_ANGLE_MAX
    )

    return fracture_records


# ============================================================
# 7. 创建模型
# ============================================================


def create_model():
    mesh = create_xy(
        x_min=X_MIN,
        dx=DX,
        x_max=X_MAX,
        y_min=Y_MIN,
        dy=DY,
        y_max=Y_MAX,
        z_min=Z_MIN,
        z_max=Z_MAX
    )

    y_min_mesh, y_max_mesh = get_pos_range(mesh, 1)
    y_mid = 0.5 * (y_min_mesh + y_max_mesh)

    requested_prod_virtual_pos = [X_PROD, y_mid, Z_PROD_VIRTUAL]
    requested_inj_virtual_pos = [X_INJ, y_mid, Z_INJ_VIRTUAL]

    add_cell_face(
        mesh,
        pos=[X_PROD, y_mid, Z_RES],
        offset=[0.0, 0.0, Z_PROD_VIRTUAL],
        vol=PROD_VIRTUAL_VOL,
        area=WELL_FACE_AREA,
        length=WELL_FACE_LENGTH
    )

    add_cell_face(
        mesh,
        pos=[X_INJ, y_mid, Z_RES],
        offset=[0.0, 0.0, Z_INJ_VIRTUAL],
        vol=INJ_VIRTUAL_VOL,
        area=WELL_FACE_AREA,
        length=WELL_FACE_LENGTH
    )

    def get_perm(x, y, z):
        return PERM_VALUE

    def get_s(x, y, z):
        if z < RESERVOIR_Z_MIN or z > RESERVOIR_Z_MAX:
            return dict(h2o=1.0, he_sol=0.0, n2_sol=0.0, ch4_sol=0.0)
        return SP2_INIT_S.copy()

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
        dict(
            pos=requested_inj_virtual_pos,
            fluid_id="h2o",
            value=Q_IN
        )
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
        dt_max=DT_MAX,
        gravity=[0.0, 0.0, 0.0],
        injectors=injectors,
        use_mass=True
    )

    print("\n========== 井筒连接检查 ==========")
    prod_virtual_cell, prod_res_cell = get_well_cells(
        model, requested_prod_virtual_pos, "生产井"
    )
    inj_virtual_cell, inj_res_cell = get_well_cells(
        model, requested_inj_virtual_pos, "注入井"
    )
    print("==================================\n")

    model.temps["injector_xy"] = [
        float(inj_res_cell.pos[0]),
        float(inj_res_cell.pos[1])
    ]
    model.temps["producer_xy"] = [
        float(prod_res_cell.pos[0]),
        float(prod_res_cell.pos[1])
    ]

    if USE_FRACTURE:
        source_fractures = create_fracture_geometry()
        fracture_records = add_fractures_like_egs(model, source_fractures)
    else:
        fracture_records = []
        model.temps["fracture_records"] = []
        model.temps["fracture_face_ids"] = []
        model.temps["fracture_face_perm"] = None
        model.temps["fracture_connectivity"] = {}
        model.temps["random_fracture_metadata"] = {}
        print("当前运行无裂缝基准模型。\n")

    print("========== 模型设置 ==========")
    print(f"USE_FRACTURE = {USE_FRACTURE}")
    print(f"RANDOM_SEED = {RANDOM_SEED}")
    print(f"RANDOM_FRACTURE_NUMBER = {RANDOM_FRACTURE_NUMBER}")
    print("裂缝方法 = 随机线段 + Dfn2 + EGS 相邻 cell 搜索")
    print("裂缝交点计算 = 关闭")
    print("单独随机裂缝网络图 = 关闭")
    print("裂缝图 = 调用 fracture/show5.py")
    print(f"基质渗透率 = {PERM_VALUE:.6e} m2")
    if USE_FRACTURE:
        print(f"裂缝 face 渗透率 = {FRACTURE_PERM:.6e} m2")
        print(f"裂缝/基质渗透率倍数 = {FRACTURE_PERM / PERM_VALUE:.2f}")
    print(f"注入流量 = {Q_IN:.6e} m3/s")
    print(f"生产井目标压力 = {P_PROD / 1.0e6:.6f} MPa")
    print(f"模拟时间 = {TIME_MAX / YEAR:.3f} year")
    print("==============================\n")

    return dict(
        model=model,
        prod_virtual_pos=list(prod_virtual_cell.pos),
        inj_virtual_pos=list(inj_virtual_cell.pos),
        prod_virtual_cell=prod_virtual_cell,
        inj_virtual_cell=inj_virtual_cell,
        prod_res_cell=prod_res_cell,
        inj_res_cell=inj_res_cell,
        fracture_records=fracture_records
    )


# ============================================================
# 8. 每步定压生产和求解
# ============================================================


def solve_with_pressure_controller(case_data):
    model = case_data["model"]
    prod_virtual_cell = case_data["prod_virtual_cell"]

    pressure_controller = PressureController(
        cell=prod_virtual_cell,
        t=[-1.0e20, 1.0e20],
        p=[P_PROD, P_PROD],
        modify_pore=False
    )

    pressure_controller.update(
        t=tfc.get_time(model),
        modify_pore=False
    )

    slot_name = "stage4_egs_random_update_production_pressure"

    def update_production_pressure():
        pressure_controller.update(
            t=tfc.get_time(model),
            modify_pore=False
        )

    add_step_setting(
        model=model,
        start=0,
        step=1,
        name=slot_name
    )

    slots = {slot_name: update_production_pressure}

    def extra_plot():
        show_xy(model)

    print("========== 定压生产设置 ==========")
    print("PressureController.modify_pore = False")
    print("生产井定压更新频率 = 每个求解步1次")
    print(f"生产井目标压力 = {P_PROD / 1.0e6:.6f} MPa")
    print("==================================\n")

    tfc.solve(
        model=model,
        extra_plot=extra_plot,
        slots=slots,
        time_max=TIME_MAX,
        state_hint=(
            "纯随机裂缝网络"
            if USE_FRACTURE
            else "无裂缝基准"
        )
    )

    print("\n========== 计算结束 ==========")
    print(f"最终时间 = {tfc.get_time(model) / YEAR:.6f} year")
    print(f"最终步数 = {tfc.get_step(model)}")
    print(f"生产井计算压力 = {prod_virtual_cell.pre / 1.0e6:.6f} MPa")
    print(
        "相对目标压力误差 = "
        f"{(prod_virtual_cell.pre - P_PROD) / 1.0e6:.6e} MPa"
    )
    print("==============================\n")


# ============================================================
# 9. 主函数
# ============================================================


def main():
    case_data = create_model()
    solve_with_pressure_controller(case_data)


if __name__ == "__main__":
    gui.execute(main)
