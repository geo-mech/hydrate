# -*- coding: utf-8 -*-

import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.exsolve.fluid import create
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.ui import gui
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


# ============================================================
# 1.1 第一阶段裂缝参数
# ============================================================

USE_FRACTURE = True

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

def create_model():
    """
    创建二维 xy 水平对井模型。

    返回：
        model:
            zmlx seepage 模型。

        prod_virtual_pos:
            生产井虚拟网格位置，用于创建 PressureController。
    """

    mesh = create_xy(
        x_min=0.0, dx=10.0, x_max=1000.0,
        y_min=0.0, dy=10.0, y_max=1000.0,
        z_min=-0.5, z_max=0.5,
    )

    y_min, y_max = get_pos_range(mesh, 1)
    y_mid = (y_min + y_max) / 2.0

    prod_virtual_pos = [X_PROD, y_mid, Z_PROD_VIRTUAL]
    inj_virtual_pos = [X_INJ, y_mid, Z_INJ_VIRTUAL]

    # ============================================================
    # 4.1 添加生产井和注入井虚拟网格
    # ============================================================

    add_cell_face(
        mesh,
        pos=[X_PROD, y_mid, Z_RES],
        offset=[0, 0, Z_PROD_VIRTUAL],
        vol=PROD_VIRTUAL_VOL,
        area=2.104,
        length=1
    )

    add_cell_face(
        mesh,
        pos=[X_INJ, y_mid, Z_RES],
        offset=[0, 0, Z_INJ_VIRTUAL],
        vol=INJ_VIRTUAL_VOL,
        area=2.104,
        length=1
    )

    # ============================================================
    # 4.2 储层物性
    # ============================================================

    def get_perm(x, y, z):
        return PERM_VALUE

    def get_s(x, y, z):
        if z < -2.0:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0
            )

        elif z > 2.0:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0
            )

        else:
            return SP2_INIT_S.copy()

    def get_denc(x, y, z):
        return 2.0e6

    def get_porosity(x, y, z):
        return POROSITY

    def get_p(x, y, z):
        if z > 2.0:
            return P_PROD
        else:
            return P_INIT

    def get_t(x, y, z):
        if z < -2.0:
            return T_INJ
        else:
            return T_RES

    # ============================================================
    # 4.3 注入器
    # ============================================================

    my_injectors = [
        {
            "pos": inj_virtual_pos,
            "fluid_id": "h2o",
            "value": Q_IN,
        }
    ]

    # ============================================================
    # 4.4 创建 seepage 模型
    # ============================================================

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
        dt_max=3600.0 * 24.0 * 1.0,
        gravity=[0, 0, 0],
        injectors=my_injectors,
        use_mass=True
    )

    # ============================================================
    # 4.5 第一阶段：基于 Dfn2 添加注采连通高渗裂缝
    # ============================================================

    if USE_FRACTURE:
        dfn = create_connecting_dfn2(y_mid)

        apply_dfn2_to_model(
            model=model,
            dfn=dfn,
            z0=Z_FRAC,
            face_perm=FRACTURE_PERM
        )
    else:
        print("\n当前模型不添加裂缝，为无裂缝基准模型。\n")

    return model, prod_virtual_pos


# ============================================================
# 5. 定压生产井求解
# ============================================================

def solve_with_pressure_controller(
        model,
        prod_virtual_pos
):

    from zmlx.scen.geothermal_helium.exsolve.show3 import show_xy

    prod_cell = model.get_nearest_cell(pos=prod_virtual_pos)

    p_ctrl = PressureController(
        cell=prod_cell,
        t=[-1.0e20, 1.0e20],
        p=[P_PROD, P_PROD],
        modify_pore=True
    )

    p_ctrl.update(t=tfc.get_time(model), modify_pore=True)

    print(f"初始控制后生产井压力 = {prod_cell.pre / 1.0e6:.6f} MPa\n")

    def extra_plot():
        p_ctrl.update(t=tfc.get_time(model), modify_pore=True)
        show_xy(model)
        p_ctrl.update(t=tfc.get_time(model), modify_pore=True)

    tfc.solve(
        model=model,
        extra_plot=extra_plot,
    )


# ============================================================
# 6. 主函数
# ============================================================

def main():
    model, prod_virtual_pos = create_model()

    solve_with_pressure_controller(
        model=model,
        prod_virtual_pos=prod_virtual_pos,
    )


if __name__ == '__main__':
    gui.execute(main)