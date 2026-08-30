# -*- coding: utf-8 -*-
"""
本文件负责：
1. 创建模型并求解；
2. 每一步控制生产井压力；
3. 调用独立 show.py 中的 show_xy(model) 显示实时空间场。
"""

import zmlx.tfc as tfc
from zmlx import PressureController
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.helium.fluid import create
from zmlx.scen.geothermal_helium.helium.show import show_xy
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.tfc._step import add_setting as add_step_setting
from zmlx.ui import gui


# ------------------------- 参数 -------------------------

P_INIT, P_PROD = 20.0e6, 19.8e6
T_RES, T_INJ = 400.0, 300.0
PERM, POROSITY = 5.0e-13, 0.30
Q_IN = 1.35e-4

X_INJ, X_PROD = 300.0, 700.0
Z_RES, Z_PROD, Z_INJ = 0.0, 10.0, -10.0
PROD_VOL, INJ_VOL = 1.0e8, 100.0

DX, DY = 10.0, 10.0
Z_MIN, Z_MAX = -2.0, 2.0

DAY = 24.0 * 3600.0
YEAR = 365.25 * DAY
TIME_MAX = 25.0 * YEAR
DT_MAX = 12.0 * 3600.0

M_HE = 4.0026e-3
VM_STD = 22.414e-3

SP2_HE_Y = 2.240 / 100.0
SP2_GAS_WATER_RATIO = 24.2 / 100.0


def initial_composition():
    """由气水比和气相 He 体积分数换算初始质量份额。"""
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
    neighbors = [cell for cell in virtual.cells if is_reservoir(cell)]
    if len(neighbors) != 1:
        raise RuntimeError(f"{name}应连接 1 个储层网格，实际为 {len(neighbors)} 个")
    return virtual, neighbors[0]


# ------------------------- 建模 -------------------------

def create_model():
    mesh = create_xy(
        x_min=0.0, dx=DX, x_max=1000.0,
        y_min=0.0, dy=DY, y_max=1000.0,
        z_min=-0.5, z_max=0.5,
    )

    y_min, y_max = get_pos_range(mesh, 1)
    y_mid = 0.5 * (y_min + y_max)
    prod_pos = [X_PROD, y_mid, Z_PROD]
    inj_pos = [X_INJ, y_mid, Z_INJ]

    add_cell_face(
        mesh, pos=[X_PROD, y_mid, Z_RES], offset=[0, 0, Z_PROD],
        vol=PROD_VOL, area=2.104, length=1.0,
    )
    add_cell_face(
        mesh, pos=[X_INJ, y_mid, Z_RES], offset=[0, 0, Z_INJ],
        vol=INJ_VOL, area=2.104, length=1.0,
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
        injectors=[{"pos": inj_pos, "fluid_id": "h2o", "value": Q_IN}],
        use_mass=True,
    )

    prod_virtual, prod_res = find_well_cells(model, prod_pos, "生产井")
    inj_virtual, inj_res = find_well_cells(model, inj_pos, "注入井")

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
    controller = PressureController(
        cell=data["prod_virtual"],
        t=[-1.0e20, 1.0e20],
        p=[P_PROD, P_PROD],
        modify_pore=False,
    )
    controller.update(t=tfc.get_time(model), modify_pore=False)

    def update_pressure():
        controller.update(t=tfc.get_time(model), modify_pore=False)

    def extra_plot():
        """
        调用独立 show.py 中的 show_xy。

        绘图前再次校正生产井压力，避免显示时生产井压力
        与设定压力之间存在一个时间步的偏差。
        """
        controller.update(
            t=tfc.get_time(model),
            modify_pore=False,
        )
        show_xy(model)

    pressure_name = "update_production_pressure"
    add_step_setting(model=model, start=0, step=1, name=pressure_name)

    print(f"注入流量 = {Q_IN:.6e} m3/s")
    print(f"生产压力 = {P_PROD / 1.0e6:.3f} MPa")
    print(f"模拟时间 = {TIME_MAX / YEAR:.1f} year")

    tfc.solve(
        model=model,
        extra_plot=extra_plot,
        slots={
            pressure_name: update_pressure,
        },
        time_max=TIME_MAX,
        state_hint="25-year fixed injection and constant production pressure",
    )

    controller.update(t=tfc.get_time(model), modify_pore=False)

    print(f"最终时间 = {tfc.get_time(model) / YEAR:.6f} year")
    print(f"最终步数 = {tfc.get_step(model)}")
    print(f"最终生产井压力 = {data['prod_virtual'].pre / 1.0e6:.6f} MPa")


def main():
    print(f"初始 He 质量份额 = {INIT_S['he_sol']:.12e}")
    solve(create_model())


if __name__ == "__main__":
    gui.execute(main)
