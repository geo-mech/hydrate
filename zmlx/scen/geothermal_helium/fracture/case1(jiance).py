# -*- coding: utf-8 -*-

import csv
import math
import os

import matplotlib.pyplot as mpl_plt
import numpy as np
from typing import Dict, List, Tuple

import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.exsolve.fluid import create
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.ui import gui
from zmlx.tfc._step import add_setting as add_step_setting
from zmlx import PressureController
from zmlx.exts._frac import Dfn2



"""
水平一注一采溶解气体被动运移模型：
SP2真实数据换算版 + 定压生产井 + Dfn2静态注采连通高渗裂缝

第一阶段裂缝处理思路：
1. 使用fracture 中的 Dfn2 定义二维裂缝几何；
2. 裂缝为注入井附近储层 cell 到生产井附近储层 cell 的连通裂缝；
3. 不使用 FracAlg.update_topology 重构 seepage 拓扑；
4. 不显式计算裂缝开度、裂缝扩展、裂缝孔隙体积；
5. 通过 Dfn2.get_fractures() 读取裂缝线段 [x0, y0, x1, y1]；
6. 将裂缝线段映射到当前 seepage 模型的 face 上；
7. 沿裂缝轨迹提高相邻 cell 之间 face 的渗透率；
8. 该裂缝表示为“等效高导流连接面裂缝”。
注：注采连通高渗裂缝能够显著增强井间水力连通性，使注入冷水和低气体质量份额前缘沿裂缝快速推进，
从而诱发流动短路和热突破提前；该类裂缝对采热是不利因素，但会加快溶解态气体的水动力迁移。
注采连通高渗裂缝能够地热系统短路
水力短路：注入水沿高渗裂缝，断层或高渗带快速达到生产井
热短路：冷水没有充分和热储层换热，就提前达到生产井，导致生产井温度过早下降，也就是热突破提前
扫掠路：流体只扫过一条窄通道，储层两侧大量热量和溶解气体没有被有效动用，导致整体采热效率或资源利用率下降
连通型高渗裂缝会造成水力短路和热突破提前，
但也会加速溶解态气体的井间迁移，
从而形成采热稳定性与溶解气体产出效率之间的矛盾。
"""


# ============================================================
# 1. 全局参数
# ============================================================

P_INIT = 20.0e6          # 储层初始压力，Pa
P_PROD = 19.8e6          # 生产井定压压力，Pa

T_RES = 400.0            # 储层初始温度，K
T_INJ = 300.0            # 注入水温度，K

PERM_VALUE = 5.0e-13     # 基质渗透率，m2
POROSITY = 0.3

Q_IN = 1.3e-4            # 注入流量，m3/s

# 井位参数
X_INJ = 300.0
X_PROD = 700.0

Z_RES = 0.0
Z_PROD_VIRTUAL = 10.0
Z_INJ_VIRTUAL = -10.0

# 生产井、注入井虚拟网格体积
PROD_VIRTUAL_VOL = 1.0e8
INJ_VIRTUAL_VOL = 100.0


# 时间、网格与定量输出参数
DAY = 24.0 * 3600.0
YEAR = 365.25 * DAY

# 为保证突破时间和累计产量可复现，显式设置总模拟时间。
# 直连高渗裂缝通常突破较早；25年可同时覆盖早期与长期阶段。
TIME_MAX = 10.0 * YEAR
DT_MAX = 1.0 * DAY

DX = 10.0
DY = 10.0
RESERVOIR_Z_MIN = -2.0
RESERVOIR_Z_MAX = 2.0

# 保留原代码的PressureController设置；需要与其他模型严格比较时，
# 各算例必须统一该开关和虚拟井筒体积。
PRODUCTION_CONTROLLER_MODIFY_PORE = True

# 每个真实时间步积分井面通量；该间隔只控制CSV记录、扫掠计算和曲线采样。
RECORD_INTERVAL = 10.0 * DAY

RHO_WATER_FALLBACK = 1000.0

# C/C0 <= 0.90：生产端溶解组分浓度下降10%。
GAS_DEPLETION_THRESHOLD = 0.90

# theta_T <= 0.90：有效生产温差下降10%。
THERMAL_BREAKTHROUGH_THRESHOLD = 0.90

# 由于当前fluid没有独立示踪剂，使用He质量分数稀释作为注入水比例代理。
# 代理注入水比例达到5%的网格计入扫掠面积。
SWEEP_INJECTED_FRACTION_THRESHOLD = 0.05


# ============================================================
# 1.1 第一阶段裂缝参数
# ============================================================

USE_FRACTURE = True

CASE_NAME = "connecting_fracture" if USE_FRACTURE else "no_fracture"
QUANT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    f"{CASE_NAME}_quantitative_output"
)

# 裂缝等效渗透率
# 当前基质渗透率 PERM_VALUE = 5.0e-13 m2
# 第一阶段先取基质的 100 倍
FRACTURE_PERM = 5.0e-11

# Dfn2.add_frac 的 l_min 参数
# 你的网格 dx = dy = 10 m，因此这里先取 10 m
FRACTURE_L_MIN = 10.0

# 裂缝所在储层平面
Z_FRAC = 0.0


# ============================================================
# 2. SP2 文献数据：气体组成 + 气水比
# ============================================================

SP2_HE_Y = 2.240 / 100.0
SP2_N2_Y = 73.800 / 100.0
SP2_CH4_Y = 12.800 / 100.0

SP2_GAS_WATER_RATIO = 24.2 / 100.0


def gas_water_to_mass_fractions(
        gas_water_ratio,
        y_he,
        y_n2,
        y_ch4,
        rho_w=1000.0,
        vm=22.414e-3
):
    """
    将“气水比 + 伴生气组分体积分数”换算为 zmlx use_mass=True 下的初始质量份额。

    gas_water_ratio:
        气水比，单位 m3 gas / m3 water。
        例如 24.2% 输入 0.242。

    y_he, y_n2, y_ch4:
        伴生气中 He、N2、CH4 的体积分数。

    rho_w:
        水密度，kg/m3。

    vm:
        标准状态气体摩尔体积，m3/mol。
    """

    M_HE = 4.0026e-3
    M_N2 = 28.0134e-3
    M_CH4 = 16.043e-3

    V_he = gas_water_ratio * y_he
    V_n2 = gas_water_ratio * y_n2
    V_ch4 = gas_water_ratio * y_ch4

    n_he = V_he / vm
    n_n2 = V_n2 / vm
    n_ch4 = V_ch4 / vm

    m_he = n_he * M_HE
    m_n2 = n_n2 * M_N2
    m_ch4 = n_ch4 * M_CH4

    r_he = m_he / rho_w
    r_n2 = m_n2 / rho_w
    r_ch4 = m_ch4 / rho_w

    total = 1.0 + r_he + r_n2 + r_ch4

    return dict(
        h2o=1.0 / total,
        he_sol=r_he / total,
        n2_sol=r_n2 / total,
        ch4_sol=r_ch4 / total
    )


SP2_INIT_S = gas_water_to_mass_fractions(
    gas_water_ratio=SP2_GAS_WATER_RATIO,
    y_he=SP2_HE_Y,
    y_n2=SP2_N2_Y,
    y_ch4=SP2_CH4_Y
)


# ============================================================
# 2.1 储层与井筒网格识别
# ============================================================


def is_reservoir_cell(cell) -> bool:
    return (
        RESERVOIR_Z_MIN
        <= float(cell.pos[2])
        <= RESERVOIR_Z_MAX
    )


def get_well_cells(model, virtual_pos, well_name: str):
    """返回虚拟井筒cell及其唯一相邻真实储层cell。"""
    virtual_cell = model.get_nearest_cell(pos=virtual_pos)
    reservoir_neighbors = [
        cell for cell in virtual_cell.cells
        if is_reservoir_cell(cell)
    ]

    if len(reservoir_neighbors) != 1:
        raise RuntimeError(
            f"{well_name}虚拟井筒应只连接1个真实储层cell，"
            f"当前找到{len(reservoir_neighbors)}个。"
        )

    reservoir_cell = reservoir_neighbors[0]
    print(
        f"{well_name}虚拟井筒cell: index={virtual_cell.index}, "
        f"pos={virtual_cell.pos}"
    )
    print(
        f"{well_name}相邻储层cell: index={reservoir_cell.index}, "
        f"pos={reservoir_cell.pos}"
    )
    return virtual_cell, reservoir_cell


# ============================================================
# 3. 基于第二版 fracture.Dfn2 的裂缝函数
# ============================================================

def create_connecting_dfn2(y_mid):
    """
    使用第二版 fracture 中的 Dfn2 创建一条注采连通二维裂缝。

    裂缝几何：
        [X_INJ, y_mid] -> [X_PROD, y_mid]

    注意：
    这里只定义裂缝几何，不直接修改渗流模型。
    后续通过 apply_dfn2_to_model() 映射到 seepage face。
    """

    dfn = Dfn2()

    # 设置 DFN 的空间范围。
    # 第二版 Dfn2.range 的格式为 [xmin, ymin, xmax, ymax]。
    dfn.range = [0.0, 0.0, 1000.0, 1000.0]

    # 添加一条注采连通裂缝。
    ok = dfn.add_frac(
        x0=X_INJ,
        y0=y_mid,
        x1=X_PROD,
        y1=y_mid,
        l_min=FRACTURE_L_MIN
    )

    fractures = dfn.get_fractures()

    print("\n========== Dfn2 注采连通裂缝网络 ==========")
    print(f"Dfn2.add_frac 返回值 = {ok}")
    print(f"裂缝数量 fracture_n = {dfn.fracture_n}")

    for i, frac_pos in enumerate(fractures):
        print(f"fracture {i}: pos = {frac_pos}")

    print("============================================\n")

    return dfn


def apply_dfn2_to_model(
        model,
        dfn,
        z0=0.0,
        face_perm=5.0e-11
):
    """
    将 Dfn2 中的二维裂缝映射到当前 seepage 模型。

    方法：
    1. 读取 dfn.get_fractures()，每条裂缝格式为 [x0, y0, x1, y1]；
    2. 找到裂缝起点和终点附近的储层 cell；
    3. 沿裂缝线段搜索相邻储层 cell；
    4. 对沿途相邻 cell 之间添加/增强 face；
    5. 将这些 face 的渗透率设置为 face_perm。

    注意：
    这不是 FracAlg.update_topology 动态裂缝拓扑模型；
    这是第一阶段的等效高导流 face 裂缝。
    """

    def point_distance_2d(px, py, qx, qy):
        return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5

    def seg_point_distance_2d(xa, ya, xb, yb, px, py):
        """
        计算点 (px, py) 到线段 (xa, ya)-(xb, yb) 的距离。
        """
        vx = xb - xa
        vy = yb - ya
        wx = px - xa
        wy = py - ya

        c1 = vx * wx + vy * wy

        if c1 <= 0.0:
            return point_distance_2d(px, py, xa, ya)

        c2 = vx * vx + vy * vy

        if c2 <= c1:
            return point_distance_2d(px, py, xb, yb)

        b = c1 / c2
        bx = xa + b * vx
        by = ya + b * vy

        return point_distance_2d(px, py, bx, by)

    fractures = dfn.get_fractures()

    total_face_count = 0

    print("\n========== Dfn2 裂缝映射到 seepage face ==========")
    print(f"裂缝条数 = {len(fractures)}")
    print(f"face 裂缝渗透率 = {face_perm:.3e} m2")

    for frac_i, frac_pos in enumerate(fractures):

        if frac_pos is None:
            continue

        x0, y0, x1, y1 = frac_pos

        cell_beg = model.get_nearest_cell(pos=[x0, y0, z0])
        cell_end = model.get_nearest_cell(pos=[x1, y1, z0])

        print(f"\n--- fracture {frac_i} ---")
        print(f"裂缝位置 = [{x0:.3f}, {y0:.3f}, {x1:.3f}, {y1:.3f}]")
        print(f"起点 cell index = {cell_beg.index}, pos = {cell_beg.pos}")
        print(f"终点 cell index = {cell_end.index}, pos = {cell_end.pos}")

        def get_score(cell_pos):
            """
            分数越小，说明该 cell 越贴近裂缝线段且越接近终点。
            """
            d_line = seg_point_distance_2d(
                x0, y0, x1, y1,
                cell_pos[0], cell_pos[1]
            )

            d_end = point_distance_2d(
                cell_pos[0], cell_pos[1],
                cell_end.pos[0], cell_end.pos[1]
            )

            return d_line + d_end

        count = 0
        visited = set()

        while cell_beg.index != cell_end.index:

            visited.add(cell_beg.index)

            neighbors = list(cell_beg.cells)

            if len(neighbors) == 0:
                print("警告：当前 cell 没有邻居，裂缝提前终止。")
                break

            candidates = []

            for i, c in enumerate(neighbors):

                # 避免走回头路
                if c.index in visited:
                    continue

                # 只允许裂缝沿真实储层 cell 前进，避免走进虚拟井筒
                if c.pos[2] < -2.0 or c.pos[2] > 2.0:
                    continue

                score = get_score(c.pos)
                candidates.append((score, i, c))

            if len(candidates) == 0:
                print("警告：没有可继续前进的真实储层邻居 cell，裂缝提前终止。")
                break

            candidates.sort(key=lambda item: item[0])

            _, idx, cell_next = candidates[0]

            # 添加或增强当前 cell 与下一个 cell 之间的 face
            face = model.add_face(cell_beg, cell_next)

            # 设置该 face 为高渗透率裂缝连接面
            tfc.set_face(face=face, perm=face_perm)

            count += 1
            cell_beg = cell_next

            if count > model.cell_number:
                print("警告：裂缝追踪步数超过模型 cell 数，强制终止。")
                break

        print(f"fracture {frac_i} 映射完成，新增/增强 face 数量 = {count}")

        total_face_count += count

    print(f"\nDfn2 裂缝映射完成，总新增/增强 face 数量 = {total_face_count}")
    print("================================================\n")

    return total_face_count


# ============================================================
# 4. 创建模型
# ============================================================
# ============================================================
# 4. 创建模型
# ============================================================


def create_model():
    """创建二维水平一注一采模型，并返回定量监测所需对象。"""

    mesh = create_xy(
        x_min=0.0, dx=DX, x_max=1000.0,
        y_min=0.0, dy=DY, y_max=1000.0,
        z_min=-0.5, z_max=0.5,
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
        area=2.104,
        length=1.0,
    )

    add_cell_face(
        mesh,
        pos=[X_INJ, y_mid, Z_RES],
        offset=[0.0, 0.0, Z_INJ_VIRTUAL],
        vol=INJ_VIRTUAL_VOL,
        area=2.104,
        length=1.0,
    )

    def get_perm(x, y, z):
        return PERM_VALUE

    def get_s(x, y, z):
        if z < RESERVOIR_Z_MIN or z > RESERVOIR_Z_MAX:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0,
            )
        return SP2_INIT_S.copy()

    def get_denc(x, y, z):
        return 2.0e6

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
            value=Q_IN,
        )
    ]

    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100.0e6,
        p=get_p,
        temperature=get_t,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=2.56,
        dist=0.8,
        dt_max=DT_MAX,
        gravity=[0.0, 0.0, 0.0],
        injectors=injectors,
        use_mass=True,
    )

    print("\n========== 井筒连接检查 ==========")
    prod_virtual_cell, prod_res_cell = get_well_cells(
        model, requested_prod_virtual_pos, "生产井"
    )
    inj_virtual_cell, inj_res_cell = get_well_cells(
        model, requested_inj_virtual_pos, "注入井"
    )
    print("==================================\n")

    fracture_face_count = 0
    if USE_FRACTURE:
        dfn = create_connecting_dfn2(y_mid)
        fracture_face_count = apply_dfn2_to_model(
            model=model,
            dfn=dfn,
            z0=Z_FRAC,
            face_perm=FRACTURE_PERM,
        )
    else:
        print("\n当前模型不添加裂缝，为无裂缝基准模型。\n")

    print("========== 模型与定量输出设置 ==========")
    print(f"CASE_NAME = {CASE_NAME}")
    print(f"USE_FRACTURE = {USE_FRACTURE}")
    print(f"裂缝映射face数量 = {fracture_face_count}")
    print(f"生产井虚拟体积 = {PROD_VIRTUAL_VOL:.6e} m3")
    print(
        "PressureController.modify_pore = "
        f"{PRODUCTION_CONTROLLER_MODIFY_PORE}"
    )
    print(f"总模拟时间 = {TIME_MAX / YEAR:.3f} year")
    print(f"CSV记录间隔 = {RECORD_INTERVAL / DAY:.3f} day")
    print(f"定量结果目录 = {QUANT_OUTPUT_DIR}")
    print("========================================\n")

    return dict(
        model=model,
        prod_virtual_pos=list(prod_virtual_cell.pos),
        inj_virtual_pos=list(inj_virtual_cell.pos),
        prod_virtual_cell=prod_virtual_cell,
        inj_virtual_cell=inj_virtual_cell,
        prod_res_cell=prod_res_cell,
        inj_res_cell=inj_res_cell,
        fracture_face_count=fracture_face_count,
    )


# ============================================================
# 5. 定量监测基础函数
# ============================================================


def normalize_fid(fid) -> List[int]:
    if isinstance(fid, (list, tuple)):
        return [int(value) for value in fid]
    return [int(fid)]


def find_fid(model, name: str) -> List[int]:
    fid = model.find_fludef(name=name)
    if fid is None:
        raise KeyError(f"模型中找不到流体或组分：{name}")
    return normalize_fid(fid)


def get_temperature_key(model):
    key = model.get_cell_key("temperature")
    if key is None:
        key = tfc.cell_keys(model).temperature
    return key


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
    """兼容不同ZMLX版本读取液相密度，单位kg/m3。"""
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

    return float(RHO_WATER_FALLBACK)


def get_cell_temperature(cell, temperature_key) -> float:
    return float(cell.get_attr(temperature_key))


def safe_ratio(numerator: float, denominator: float) -> float:
    if (
            not math.isfinite(numerator)
            or not math.isfinite(denominator)
            or abs(denominator) <= 1.0e-300
    ):
        return float("nan")
    return numerator / denominator


def find_face_between(model, cell_a, cell_b):
    a_id = int(cell_a.index)
    b_id = int(cell_b.index)

    for face in model.faces:
        c0 = face.get_cell(0)
        c1 = face.get_cell(1)
        if {int(c0.index), int(c1.index)} == {a_id, b_id}:
            return face

    raise RuntimeError(
        f"没有找到cell {a_id}与cell {b_id}之间的连接面。"
    )


def signed_dv_out_of_reservoir(
        face,
        reservoir_cell,
        virtual_cell,
        liquid_phase_id: int,
) -> Tuple[float, object]:
    """
    返回最近一个数值步离开真实储层的带符号液相体积。

    正值：真实储层 -> 虚拟井筒；
    负值：虚拟井筒 -> 真实储层。

    face.get_dv原始符号依赖face内部cell顺序，因此这里用压力差判别方向。
    当前模型关闭重力，井连接面无毛细压，该方法适用于本算例。
    """
    dv_abs = abs(float(face.get_dv(int(liquid_phase_id))))
    p_res = float(reservoir_cell.pre)
    p_virtual = float(virtual_cell.pre)

    if p_res > p_virtual:
        return dv_abs, reservoir_cell
    if p_res < p_virtual:
        return -dv_abs, virtual_cell
    return 0.0, reservoir_cell


# ============================================================
# 6. 定量监测器
# ============================================================


class QuantitativeRecorder:
    """
    输出生产流量、生产温度、He浓度、He产率与累计产量、突破时间、
    水和溶解气体质量守恒误差，以及基于He稀释的注入水扫掠面积。

    用户所称“He瞬时功率”在量纲上不是功率。本代码按物理意义输出
    He瞬时质量产率，单位kg/s和kg/day。
    """

    ALL_COMPONENTS = ("h2o", "he", "n2", "ch4")
    GAS_COMPONENTS = ("he", "n2", "ch4")

    def __init__(self, case_data):
        self.model = case_data["model"]
        self.prod_virtual_cell = case_data["prod_virtual_cell"]
        self.prod_res_cell = case_data["prod_res_cell"]
        self.inj_virtual_cell = case_data["inj_virtual_cell"]
        self.inj_res_cell = case_data["inj_res_cell"]

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
            "n2": find_fid(self.model, "n2_sol"),
            "ch4": find_fid(self.model, "ch4_sol"),
        }
        self.temperature_key = get_temperature_key(self.model)

        self.reservoir_cells = [
            cell for cell in self.model.cells
            if is_reservoir_cell(cell)
        ]

        self.initial_fraction = {
            "h2o": float(SP2_INIT_S["h2o"]),
            "he": float(SP2_INIT_S["he_sol"]),
            "n2": float(SP2_INIT_S["n2_sol"]),
            "ch4": float(SP2_INIT_S["ch4_sol"]),
        }

        self.initial_density = get_phase_density(
            self.prod_res_cell, self.liquid_fid
        )
        self.initial_concentration = {
            name: self.initial_density * self.initial_fraction[name]
            for name in self.GAS_COMPONENTS
        }

        self.initial_reservoir_mass = {
            name: self.sum_reservoir_component_mass(name)
            for name in self.ALL_COMPONENTS
        }

        # 两个边界面的累计净外流质量；负值表示净流入储层。
        self.cumulative_prod_mass = {
            name: 0.0 for name in self.ALL_COMPONENTS
        }
        self.cumulative_inj_side_out_mass = {
            name: 0.0 for name in self.ALL_COMPONENTS
        }

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
            for name in self.ALL_COMPONENTS
        }
        self.latest_component_rate = {
            name: 0.0 for name in self.ALL_COMPONENTS
        }

        self.rows: List[Dict] = []

        os.makedirs(QUANT_OUTPUT_DIR, exist_ok=True)
        self.history_csv = os.path.join(
            QUANT_OUTPUT_DIR, "production_history.csv"
        )
        self.summary_csv = os.path.join(
            QUANT_OUTPUT_DIR, "breakthrough_summary.csv"
        )

        self.initialize_csv()
        self.record(force=True)

        print("\n========== 定量监测器初始化 ==========")
        print(f"输出目录 = {QUANT_OUTPUT_DIR}")
        print(f"真实储层cell数量 = {len(self.reservoir_cells)}")
        print(
            f"初始储层He质量 = "
            f"{self.initial_reservoir_mass['he']:.6e} kg"
        )
        print(
            f"初始He浓度 = "
            f"{self.initial_concentration['he']:.6e} kg/m3"
        )
        print(
            "气体贫化判据 = "
            f"C/C0 <= {GAS_DEPLETION_THRESHOLD:.3f}"
        )
        print(
            "热突破判据 = "
            f"theta_T <= {THERMAL_BREAKTHROUGH_THRESHOLD:.3f}"
        )
        print(
            "扫掠判据 = "
            f"1-w_He/w_He0 >= "
            f"{SWEEP_INJECTED_FRACTION_THRESHOLD:.3f}"
        )
        print("====================================\n")

    @staticmethod
    def fieldnames() -> List[str]:
        return [
            "case_name",
            "step",
            "time_s",
            "time_day",
            "time_year",
            "dt_s",

            "q_prod_m3_s",
            "q_prod_m3_day",
            "q_prod_to_q_in_set",
            "q_in_actual_m3_s",
            "q_in_actual_m3_day",

            "prod_temperature_K",
            "prod_temperature_C",
            "normalized_temperature",

            "prod_liquid_density_kg_m3",
            "he_mass_fraction",
            "he_concentration_kg_m3_water",
            "he_concentration_mg_L",
            "he_w_over_w0",
            "he_C_over_C0",
            "n2_C_over_C0",
            "ch4_C_over_C0",

            "he_instantaneous_rate_kg_s",
            "he_instantaneous_rate_kg_day",
            "cum_he_prod_kg",
            "cum_he_prod_from_balance_kg",

            "res_h2o_mass_kg",
            "res_he_mass_kg",
            "res_n2_mass_kg",
            "res_ch4_mass_kg",

            "h2o_mass_balance_error_kg",
            "he_mass_balance_error_kg",
            "n2_mass_balance_error_kg",
            "ch4_mass_balance_error_kg",
            "h2o_mass_balance_error_rel",
            "he_mass_balance_error_rel",
            "n2_mass_balance_error_rel",
            "ch4_mass_balance_error_rel",

            "swept_area_m2",
            "swept_fraction",
            "mean_injected_water_fraction_proxy",
        ]

    def initialize_csv(self):
        with open(
                self.history_csv,
                "w",
                newline="",
                encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames())
            writer.writeheader()

    def sum_reservoir_component_mass(self, name: str) -> float:
        fid = self.component_fids[name]
        return sum(
            get_component_mass(cell, fid)
            for cell in self.reservoir_cells
        )

    @staticmethod
    def cell_horizontal_area(_cell) -> float:
        return float(DX * DY)

    def calculate_sweep(self) -> Tuple[float, float, float]:
        """
        使用He质量分数稀释估算注入水扫掠面积：
            f_inj_proxy = clip(1-w_He/w_He0, 0, 1)。

        仅在初始He均匀、注入水无He、He不反应且不脱溶时成立。
        """
        he0 = self.initial_fraction["he"]
        swept_area = 0.0
        total_area = 0.0
        weighted_injected_fraction = 0.0

        for cell in self.reservoir_cells:
            area = self.cell_horizontal_area(cell)
            he_fraction = get_mass_fraction(
                cell,
                self.component_fids["he"],
                self.liquid_fid,
            )
            he_normalized = safe_ratio(he_fraction, he0)

            if math.isfinite(he_normalized):
                injected_fraction = min(
                    1.0, max(0.0, 1.0 - he_normalized)
                )
            else:
                injected_fraction = 0.0

            total_area += area
            weighted_injected_fraction += injected_fraction * area

            if injected_fraction >= SWEEP_INJECTED_FRACTION_THRESHOLD:
                swept_area += area

        return (
            swept_area,
            safe_ratio(swept_area, total_area),
            safe_ratio(weighted_injected_fraction, total_area),
        )

    def update_one_step(self):
        """每个真实数值步积分生产井与注入井连接面通量。"""
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

        # 生产组分和温度取生产连接面的上游流体，而非巨大虚拟井筒平均值。
        self.latest_prod_temperature = get_cell_temperature(
            prod_upstream, self.temperature_key
        )
        self.latest_prod_density = get_phase_density(
            prod_upstream, self.liquid_fid
        )

        for name in self.ALL_COMPONENTS:
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
            for name in self.ALL_COMPONENTS
        }

        self.last_step_time = now

        if now >= self.next_record_time:
            self.record(force=False)
            while self.next_record_time <= now:
                self.next_record_time += RECORD_INTERVAL

    def build_row(self) -> Dict:
        time_s = float(tfc.get_time(self.model))
        step = int(tfc.get_step(self.model))

        temp_k = float(self.latest_prod_temperature)
        normalized_temperature = safe_ratio(
            temp_k - T_INJ,
            T_RES - T_INJ,
        )

        concentration = {
            name: self.latest_prod_density * self.latest_fraction[name]
            for name in self.GAS_COMPONENTS
        }
        normalized_concentration = {
            name: safe_ratio(
                concentration[name], self.initial_concentration[name]
            )
            for name in self.GAS_COMPONENTS
        }

        reservoir_mass = {
            name: self.sum_reservoir_component_mass(name)
            for name in self.ALL_COMPONENTS
        }

        balance_error = {}
        balance_error_rel = {}
        cumulative_from_balance = {}

        for name in self.ALL_COMPONENTS:
            cumulative_from_balance[name] = (
                self.initial_reservoir_mass[name]
                - reservoir_mass[name]
                - self.cumulative_inj_side_out_mass[name]
            )
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

        swept_area, swept_fraction, mean_injected_fraction = (
            self.calculate_sweep()
        )

        he_concentration_kg_m3 = concentration["he"]

        return {
            "case_name": CASE_NAME,
            "step": step,
            "time_s": time_s,
            "time_day": time_s / DAY,
            "time_year": time_s / YEAR,
            "dt_s": self.latest_dt,

            "q_prod_m3_s": self.latest_q_prod,
            "q_prod_m3_day": self.latest_q_prod * DAY,
            "q_prod_to_q_in_set": safe_ratio(
                self.latest_q_prod, Q_IN
            ),
            "q_in_actual_m3_s": self.latest_q_in_actual,
            "q_in_actual_m3_day": self.latest_q_in_actual * DAY,

            "prod_temperature_K": temp_k,
            "prod_temperature_C": temp_k - 273.15,
            "normalized_temperature": normalized_temperature,

            "prod_liquid_density_kg_m3": self.latest_prod_density,
            "he_mass_fraction": self.latest_fraction["he"],
            "he_concentration_kg_m3_water": he_concentration_kg_m3,
            "he_concentration_mg_L": he_concentration_kg_m3 * 1000.0,
            "he_w_over_w0": safe_ratio(
                self.latest_fraction["he"], self.initial_fraction["he"]
            ),
            "he_C_over_C0": normalized_concentration["he"],
            "n2_C_over_C0": normalized_concentration["n2"],
            "ch4_C_over_C0": normalized_concentration["ch4"],

            "he_instantaneous_rate_kg_s":
                self.latest_component_rate["he"],
            "he_instantaneous_rate_kg_day":
                self.latest_component_rate["he"] * DAY,
            "cum_he_prod_kg": self.cumulative_prod_mass["he"],
            "cum_he_prod_from_balance_kg":
                cumulative_from_balance["he"],

            "res_h2o_mass_kg": reservoir_mass["h2o"],
            "res_he_mass_kg": reservoir_mass["he"],
            "res_n2_mass_kg": reservoir_mass["n2"],
            "res_ch4_mass_kg": reservoir_mass["ch4"],

            "h2o_mass_balance_error_kg": balance_error["h2o"],
            "he_mass_balance_error_kg": balance_error["he"],
            "n2_mass_balance_error_kg": balance_error["n2"],
            "ch4_mass_balance_error_kg": balance_error["ch4"],
            "h2o_mass_balance_error_rel": balance_error_rel["h2o"],
            "he_mass_balance_error_rel": balance_error_rel["he"],
            "n2_mass_balance_error_rel": balance_error_rel["n2"],
            "ch4_mass_balance_error_rel": balance_error_rel["ch4"],

            "swept_area_m2": swept_area,
            "swept_fraction": swept_fraction,
            "mean_injected_water_fraction_proxy":
                mean_injected_fraction,
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

        if self.rows and abs(
                float(self.rows[-1]["time_s"])
                - float(row["time_s"])
        ) <= 1.0e-12:
            self.rows[-1] = row
            with open(
                    self.history_csv,
                    "w",
                    newline="",
                    encoding="utf-8-sig",
            ) as file:
                writer = csv.DictWriter(
                    file, fieldnames=self.fieldnames()
                )
                writer.writeheader()
                writer.writerows(self.rows)
            return

        self.rows.append(row)
        with open(
                self.history_csv,
                "a",
                newline="",
                encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames())
            writer.writerow(row)

    @staticmethod
    def crossing_time(
            rows: List[Dict],
            key: str,
            threshold: float,
    ) -> float:
        """线性插值得到目标量首次下降到阈值的时间，单位year。"""
        previous = None

        for row in rows:
            time_year = float(row["time_year"])
            value = float(row[key])
            if not math.isfinite(value):
                continue

            if value <= threshold:
                if previous is None:
                    return time_year

                t0, v0 = previous
                if v0 <= threshold or abs(value - v0) <= 1.0e-300:
                    return time_year

                fraction = (v0 - threshold) / (v0 - value)
                fraction = min(1.0, max(0.0, fraction))
                return t0 + fraction * (time_year - t0)

            previous = (time_year, value)

        return float("nan")

    @staticmethod
    def max_abs_finite(rows: List[Dict], key: str) -> float:
        values = [
            abs(float(row[key]))
            for row in rows
            if math.isfinite(float(row[key]))
        ]
        return max(values) if values else float("nan")

    def write_summary(self) -> Dict:
        depletion_times = {
            name: self.crossing_time(
                self.rows,
                f"{name}_C_over_C0",
                GAS_DEPLETION_THRESHOLD,
            )
            for name in self.GAS_COMPONENTS
        }
        thermal_time = self.crossing_time(
            self.rows,
            "normalized_temperature",
            THERMAL_BREAKTHROUGH_THRESHOLD,
        )

        last = self.rows[-1]
        fields = [
            "case_name",
            "simulation_time_year",
            "gas_depletion_threshold_C_over_C0",
            "he_depletion_time_day",
            "he_depletion_time_year",
            "n2_depletion_time_day",
            "n2_depletion_time_year",
            "ch4_depletion_time_day",
            "ch4_depletion_time_year",
            "thermal_breakthrough_threshold_theta_T",
            "thermal_breakthrough_time_day",
            "thermal_breakthrough_time_year",
            "sweep_injected_fraction_threshold",
            "final_swept_area_m2",
            "final_swept_fraction",
            "final_cum_he_prod_kg",
            "final_cum_he_prod_from_balance_kg",
            "max_abs_h2o_mass_balance_error_rel",
            "max_abs_he_mass_balance_error_rel",
            "max_abs_n2_mass_balance_error_rel",
            "max_abs_ch4_mass_balance_error_rel",
        ]

        row = {
            "case_name": CASE_NAME,
            "simulation_time_year": float(last["time_year"]),
            "gas_depletion_threshold_C_over_C0":
                GAS_DEPLETION_THRESHOLD,
            "he_depletion_time_day": depletion_times["he"] * 365.25,
            "he_depletion_time_year": depletion_times["he"],
            "n2_depletion_time_day": depletion_times["n2"] * 365.25,
            "n2_depletion_time_year": depletion_times["n2"],
            "ch4_depletion_time_day": depletion_times["ch4"] * 365.25,
            "ch4_depletion_time_year": depletion_times["ch4"],
            "thermal_breakthrough_threshold_theta_T":
                THERMAL_BREAKTHROUGH_THRESHOLD,
            "thermal_breakthrough_time_day": thermal_time * 365.25,
            "thermal_breakthrough_time_year": thermal_time,
            "sweep_injected_fraction_threshold":
                SWEEP_INJECTED_FRACTION_THRESHOLD,
            "final_swept_area_m2": last["swept_area_m2"],
            "final_swept_fraction": last["swept_fraction"],
            "final_cum_he_prod_kg": last["cum_he_prod_kg"],
            "final_cum_he_prod_from_balance_kg":
                last["cum_he_prod_from_balance_kg"],
            "max_abs_h2o_mass_balance_error_rel":
                self.max_abs_finite(
                    self.rows, "h2o_mass_balance_error_rel"
                ),
            "max_abs_he_mass_balance_error_rel":
                self.max_abs_finite(
                    self.rows, "he_mass_balance_error_rel"
                ),
            "max_abs_n2_mass_balance_error_rel":
                self.max_abs_finite(
                    self.rows, "n2_mass_balance_error_rel"
                ),
            "max_abs_ch4_mass_balance_error_rel":
                self.max_abs_finite(
                    self.rows, "ch4_mass_balance_error_rel"
                ),
        }

        with open(
                self.summary_csv,
                "w",
                newline="",
                encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)

        return row

    def plot_results(self):
        time_year = np.asarray(
            [float(row["time_year"]) for row in self.rows],
            dtype=float,
        )

        def values(key: str):
            return np.asarray(
                [float(row[key]) for row in self.rows],
                dtype=float,
            )

        # 1. 生产井流量
        fig, ax = mpl_plt.subplots(figsize=(8.5, 5.2))
        ax.plot(time_year, values("q_prod_m3_day"), label="Production")
        ax.axhline(
            Q_IN * DAY,
            linestyle="--",
            label="Set injection rate",
        )
        ax.set_xlabel("Time (year)")
        ax.set_ylabel("Flow rate (m3/day)")
        ax.set_title("Production-well flow rate")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(
            os.path.join(QUANT_OUTPUT_DIR, "01_production_flow_rate.png"),
            dpi=300,
        )
        mpl_plt.close(fig)

        # 2. 生产井温度
        fig, ax = mpl_plt.subplots(figsize=(8.5, 5.2))
        ax.plot(
            time_year,
            values("prod_temperature_C"),
            label="Production temperature",
        )
        threshold_temperature_c = (
            T_INJ
            + THERMAL_BREAKTHROUGH_THRESHOLD * (T_RES - T_INJ)
            - 273.15
        )
        ax.axhline(
            threshold_temperature_c,
            linestyle="--",
            label="10% thermal-breakthrough threshold",
        )
        ax.set_xlabel("Time (year)")
        ax.set_ylabel("Production temperature (degC)")
        ax.set_title("Production-well temperature")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(
            os.path.join(
                QUANT_OUTPUT_DIR, "02_production_temperature.png"
            ),
            dpi=300,
        )
        mpl_plt.close(fig)

        # 3. He绝对浓度和归一化浓度
        fig, ax1 = mpl_plt.subplots(figsize=(8.5, 5.2))
        ax1.plot(
            time_year,
            values("he_concentration_mg_L"),
            label="He concentration",
        )
        ax1.set_xlabel("Time (year)")
        ax1.set_ylabel("He concentration (mg/L)")
        ax1.grid(True)

        ax2 = ax1.twinx()
        ax2.plot(
            time_year,
            values("he_C_over_C0"),
            linestyle="--",
            label="He C/C0",
        )
        ax2.axhline(
            GAS_DEPLETION_THRESHOLD,
            linestyle=":",
            label="10% depletion threshold",
        )
        ax2.set_ylabel("Normalized He concentration, C/C0")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2)
        ax1.set_title("Produced He concentration")
        fig.tight_layout()
        fig.savefig(
            os.path.join(QUANT_OUTPUT_DIR, "03_he_concentration.png"),
            dpi=300,
        )
        mpl_plt.close(fig)

        # 4. He瞬时质量产率和累计产量
        fig, ax1 = mpl_plt.subplots(figsize=(8.5, 5.2))
        ax1.plot(
            time_year,
            values("he_instantaneous_rate_kg_day"),
            label="Instantaneous He rate",
        )
        ax1.set_xlabel("Time (year)")
        ax1.set_ylabel("He rate (kg/day)")
        ax1.grid(True)

        ax2 = ax1.twinx()
        ax2.plot(
            time_year,
            values("cum_he_prod_kg"),
            linestyle="--",
            label="Face-integrated cumulative He",
        )
        ax2.plot(
            time_year,
            values("cum_he_prod_from_balance_kg"),
            linestyle=":",
            label="Balance-derived cumulative He",
        )
        ax2.set_ylabel("Cumulative produced He (kg)")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2)
        ax1.set_title("He instantaneous rate and cumulative production")
        fig.tight_layout()
        fig.savefig(
            os.path.join(QUANT_OUTPUT_DIR, "04_he_production.png"),
            dpi=300,
        )
        mpl_plt.close(fig)

        # 5. 水和溶解气体质量守恒误差
        fig, ax = mpl_plt.subplots(figsize=(8.5, 5.2))
        for name, label in (
                ("h2o", "H2O"),
                ("he", "He"),
                ("n2", "N2"),
                ("ch4", "CH4"),
        ):
            error = np.abs(values(f"{name}_mass_balance_error_rel"))
            error[error <= 0.0] = np.nan
            ax.plot(time_year, error, label=label)
        ax.set_yscale("log")
        ax.set_xlabel("Time (year)")
        ax.set_ylabel("Absolute relative mass-balance error")
        ax.set_title("Reservoir-control-volume mass-balance error")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(
            os.path.join(QUANT_OUTPUT_DIR, "05_mass_balance_error.png"),
            dpi=300,
        )
        mpl_plt.close(fig)

        # 6. 注入水扫掠面积代理
        fig, ax1 = mpl_plt.subplots(figsize=(8.5, 5.2))
        ax1.plot(
            time_year,
            values("swept_area_m2"),
            label="Swept area proxy",
        )
        ax1.set_xlabel("Time (year)")
        ax1.set_ylabel("Swept area (m2)")
        ax1.grid(True)

        ax2 = ax1.twinx()
        ax2.plot(
            time_year,
            values("swept_fraction"),
            linestyle="--",
            label="Swept fraction",
        )
        ax2.set_ylabel("Swept fraction")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2)
        ax1.set_title("Injection-water swept area proxy")
        fig.tight_layout()
        fig.savefig(
            os.path.join(
                QUANT_OUTPUT_DIR,
                "06_injection_water_sweep_area.png",
            ),
            dpi=300,
        )
        mpl_plt.close(fig)

    def finalize(self):
        self.update_one_step()
        self.record(force=True)
        summary = self.write_summary()
        self.plot_results()

        print("\n========== 定量结果输出完成 ==========")
        print(f"历史数据CSV = {self.history_csv}")
        print(f"突破汇总CSV = {self.summary_csv}")
        print(
            f"He贫化时间(年) = "
            f"{summary['he_depletion_time_year']}"
        )
        print(
            f"热突破时间(年) = "
            f"{summary['thermal_breakthrough_time_year']}"
        )
        print(
            "最终He累计产量(kg) = "
            f"{summary['final_cum_he_prod_kg']:.6e}"
        )
        print(
            "最终注入水扫掠面积(m2) = "
            f"{summary['final_swept_area_m2']:.6e}"
        )
        print(
            "He最大相对质量守恒误差 = "
            f"{summary['max_abs_he_mass_balance_error_rel']:.6e}"
        )
        print("曲线PNG = 01至06")
        print("=====================================\n")


# ============================================================
# 7. 定压生产、逐步监测和求解
# ============================================================


def solve_with_pressure_controller(case_data):
    from zmlx.scen.geothermal_helium.exsolve.show3 import show_xy

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

    recorder = QuantitativeRecorder(case_data)

    pressure_slot_name = "connecting_fracture_update_production_pressure"
    monitor_slot_name = "connecting_fracture_quantitative_monitor"

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
        pressure_controller.update(
            t=tfc.get_time(model),
            modify_pore=PRODUCTION_CONTROLLER_MODIFY_PORE,
        )
        show_xy(model)

    print("========== 定压生产与定量监测 ==========")
    print(
        "PressureController.modify_pore = "
        f"{PRODUCTION_CONTROLLER_MODIFY_PORE}"
    )
    print("生产井面通量积分频率 = 每个求解步1次")
    print(f"CSV和扫掠记录间隔 = {RECORD_INTERVAL / DAY:.3f} day")
    print(f"总模拟时间 = {TIME_MAX / YEAR:.3f} year")
    print(f"生产井目标压力 = {P_PROD / 1.0e6:.6f} MPa")
    print(f"定量输出目录 = {QUANT_OUTPUT_DIR}")
    print("======================================\n")

    tfc.solve(
        model=model,
        extra_plot=extra_plot,
        slots=slots,
        time_max=TIME_MAX,
        state_hint=(
            "Dfn2 connecting fracture + quantitative monitoring"
            if USE_FRACTURE
            else "No fracture + quantitative monitoring"
        ),
    )

    recorder.finalize()

    print("\n========== 计算结束 ==========")
    print(f"最终时间 = {tfc.get_time(model) / YEAR:.6f} year")
    print(f"最终步数 = {tfc.get_step(model)}")
    print(
        f"生产井计算压力 = "
        f"{prod_virtual_cell.pre / 1.0e6:.6f} MPa"
    )
    print(
        "相对目标压力误差 = "
        f"{(prod_virtual_cell.pre - P_PROD) / 1.0e6:.6e} MPa"
    )
    print("==============================\n")


# ============================================================
# 8. 主函数
# ============================================================


def main():
    case_data = create_model()
    solve_with_pressure_controller(case_data)


if __name__ == "__main__":
    gui.execute(main)
