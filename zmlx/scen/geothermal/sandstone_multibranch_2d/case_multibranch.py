# ** desc = '砂岩二维平行多分支井：1、2、3、4分支十年对照'
"""引用原create/solve运行二维多井截面对照，仅保存数据、不自动绘图。"""

import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from zmlx.scen.geothermal.cases.sandstone_multibranch_2d.settings import (
    COUNTS, RESULTS, SCHEMA, Parameters,
)


def prepare_runtime():
    """将临时文件和绘图缓存限定在新算例文件夹内。"""
    for key in ("APPDATA", "LOCALAPPDATA", "MPLCONFIGDIR", "TEMP", "TMP"):
        folder = RESULTS / "runtime" / key.lower()
        folder.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(folder)
    os.environ["disable_feedback"] = "Yes"
    os.environ.setdefault("OMP_NUM_THREADS", "1")


def run_case(count, p=Parameters()):
    """直接调用原截面模型和保存求解器运行一个分支数。

    Args:
        count: 分支数，标准组为1、2、3、4。
        p: 各工况共用参数。

    Returns:
        dict: 合计和各分支采热摘要。

    Raises:
        ValueError: 参数、网格映射或边界间距无效。
        FileExistsError: 目标目录已有结果，避免覆盖。
        RuntimeError: 原求解器停止推进或出现非有限结果。
    """
    positions = p.positions(count)
    output = RESULTS / f"N{count}"
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"已有结果：{output}。请先重命名该目录，再运行。")
    prepare_runtime()
    from zmlx.scen.geothermal._fludefs import create_fludefs
    from zmlx.scen.geothermal._well_cross_section import create, get_well_cells, solve

    def temperature(x, y, z):
        """按相对高程返回初始地温K。

        Args:
            x, y, z: 单元坐标m，z向上。

        Returns:
            float: 井外初始温度K。
        """
        return 273.15 + p.temperature_c - p.gradient_k_m*z

    def density(x, y, z):
        """返回岩石密度及左右大热容边界的等效密度。

        Args:
            x, y, z: 单元坐标m。

        Returns:
            float: 密度kg/m³；最外侧列放大10⁶倍。
        """
        dx = 2*p.half_width_m/p.grid_count
        return p.rock_density_kg_m3 * (1e6 if abs(x) > p.half_width_m-dx else 1)

    def pressure(x, y, z):
        """复用砂岩基准的近静水初压关系，不设置侧向水头差。

        Args:
            x, y, z: 单元坐标m，仅z参与初压计算。

        Returns:
            float: 初始压力Pa。
        """
        t = 273.15+p.temperature_c
        rho = sum(weight * 999.8*(1-0.0002*((t-p.gradient_k_m*z*fraction-277)/5.6)**2)
                  for fraction, weight in ((0, 1), (0.5, 4), (1, 1)))/6
        return p.pressure_center_pa + (p.pressure_center_pa+2e9)*math.expm1(
            -p.gravity_m_s2*z*rho/2e9)

    model = create(jx=p.grid_count, jz=p.grid_count,
                   xr=(-p.half_width_m, p.half_width_m), zr=(-p.half_width_m, p.half_width_m),
                   well_positions=positions, well_d=p.well_diameter_m,
                   rock_density=density, rock_heat_capacity=p.rock_cp_j_kgk,
                   rock_heat_cond=p.conductivity_w_mk, perm=p.permeability_m2,
                   porosity=p.porosity, reservoir_temp=temperature,
                   well_temp=p.well_temperature_k, pressure=pressure,
                   fluid_definitions=create_fludefs(t_min=275, t_max=370),
                   sealed_well=True, dt_max=p.dt_max_s, record_step_power=False)
    model.gravity = [0, 0, -p.gravity_m_s2]
    wells = get_well_cells(model)
    actual = [[c.pos[0], c.pos[2]] for c in wells]
    gaps = [actual[i+1][0]-actual[i][0] for i in range(count-1)]
    dx = 2*p.half_width_m/p.grid_count
    if any(abs(z) > 1e-7 for _, z in actual) or any(gap <= 2*dx for gap in gaps):
        raise ValueError("井位未映射同一深度，或井距不足两个网格宽度")
    info = dict(schema=SCHEMA, branch_count=count, depth_m=p.depth_m,
                permeability_m2=p.permeability_m2, conductivity_w_mk=p.conductivity_w_mk,
                head_gradient=0.0, hydraulic_boundary="closed", sealed_well=True,
                lateral_thermal_buffer=True, parameters=asdict(p),
                well_positions_requested_xz_m=positions, well_positions_actual_xz_m=actual,
                actual_spacing_m=gaps, well_indices=[c.index for c in wells],
                minimum_lateral_boundary_distance_m=min(p.half_width_m-abs(x) for x, _ in actual),
                geometry="parallel_y_horizontal_wells_xz_cross_section",
                axial_thickness_m=1.0,
                normalization="sum across branches per shared axial metre; mean=sum/N")
    output.mkdir(parents=True, exist_ok=True)
    (output / "parameters.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"N={count}，实际井位={actual}，网格={p.grid_count}×{p.grid_count}", flush=True)
    return solve(model, p.grid_count, p.grid_count, time_max=p.days*86400,
                 folder=output, save_days=p.save_days(), parameters=info)


def main():
    """解析运行参数，逐组求解；不调用绘图脚本。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("N1", "N2", "N3", "N4", "all"), default="all")
    parser.add_argument("--days", type=int, default=3650)
    parser.add_argument("--spacing", type=float, default=20.0, help="分支目标中心距m")
    parser.add_argument("--half-width", type=float, default=50.0, help="X、Z方向计算域半宽m")
    parser.add_argument("--grid", type=int, default=101, help="X、Z方向网格数，奇数")
    args = parser.parse_args()
    p = Parameters(days=args.days, spacing_m=args.spacing,
                   half_width_m=args.half_width, grid_count=args.grid)
    counts = COUNTS if args.case == "all" else (int(args.case[1:]),)
    # 启动前校验整组选定几何，避免跑完前几组才发现末组井位越界。
    for count in counts:
        p.positions(count)
        folder = RESULTS / f"N{count}"
        if folder.exists() and any(folder.iterdir()):
            raise FileExistsError(f"已有结果：{folder}。请先重命名该目录。")
    for count in counts:
        run_case(count, p)


if __name__ == "__main__":
    main()
