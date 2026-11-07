"""引用原create/solve，运行碳酸盐岩基准及两组各四个增强工况。

默认十年，仅保存数据，不调用绘图。酸压以多条不规则高渗裂缝带表示。
"""

import argparse
import json
import math
import os
import sys

sys.dont_write_bytecode = True
if __package__:
    from zmlx.scen.geothermal.cases.carbonate_enhancement import settings as cfg
    from zmlx.scen.geothermal.cases.carbonate_enhancement.fractures import FractureBands, make_fractures
else:
    import settings as cfg
    from fractures import FractureBands, make_fractures


def prepare_runtime():
    """在导入zmlx前，将运行临时目录限定在本算例results/runtime内。"""
    for key in ("APPDATA", "LOCALAPPDATA", "MPLCONFIGDIR", "TEMP", "TMP"):
        folder = cfg.RESULTS / "runtime" / key.lower()
        folder.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(folder)
    os.environ["disable_feedback"] = "Yes"
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    sys.path.insert(0, str(cfg.GEOTHERMAL.parents[2]))


def hydrostatic_profile(water_density):
    """由地表水位向下积分静水压力，包含实际温压对水密度的影响。

    Args:
        water_density: 项目已有水密度函数(Pa,K)->kg/m³。

    Returns:
        tuple: 深度m和绝对压力Pa数组，覆盖计算域并精确包含井中心深度。

    Raises:
        ValueError: 温压状态或密度无效。
    """
    import numpy as np
    end = cfg.DEPTH_M + 50.0
    depths = np.unique(np.r_[np.arange(0, end, 5.0), cfg.DEPTH_M, end])
    pressures = [cfg.ATMOSPHERE_PA]

    def derivative(depth, pressure):
        """返回dp/dh=ρg，地温沿全水柱按PPT梯度外推。

        Args:
            depth: 地表以下深度m。
            pressure: 当前绝对压力Pa。

        Returns:
            float: 压力梯度Pa/m。

        Raises:
            ValueError: 密度非正或不是有限数。
        """
        temperature = 273.15 + cfg.TEMPERATURE_C + cfg.GRADIENT_K_M * (depth - cfg.DEPTH_M)
        rho = water_density(pressure, temperature)
        if not math.isfinite(rho) or rho <= 0:
            raise ValueError("静水积分遇到无效水密度")
        return rho * cfg.GRAVITY

    for a, b in zip(depths[:-1], depths[1:]):
        p, step = pressures[-1], b - a
        k1 = derivative(a, p)
        k2 = derivative(a + step / 2, p + step * k1 / 2)
        k3 = derivative(a + step / 2, p + step * k2 / 2)
        k4 = derivative(b, p + step * k3)
        pressures.append(p + step * (k1 + 2*k2 + 2*k3 + k4) / 6)
    return depths, np.asarray(pressures)


def configure_zone(model, case, tfc):
    """以原tfc接口将高渗/高导赋给裂缝带，带外保留基质物性。

    Args:
        model: 原create返回的模型。
        case: settings.Case。
        tfc: 已有热流耦合模块。

    Returns:
        FractureBands: 求解实际使用的裂缝几何，用于保存及绘图。
    """
    paths = make_fractures(case.radius_m, seed=cfg.FRACTURE_SEED, count=cfg.FRACTURE_COUNT,
                           vertical_ratio=cfg.FRACTURE_VERTICAL_RATIO)
    bands = FractureBands(paths, cfg.FRACTURE_BAND_WIDTH_M)
    well_id = int(model.get_text(key="well_cell_id"))
    for face in model.faces:
        a, b = face.get_cell(0), face.get_cell(1)
        fraction = bands.fraction(a.pos, b.pos)
        permeability = 1 / (fraction / case.zone_permeability_m2 + (1-fraction) / cfg.K0)
        conductivity = 1 / (fraction / case.zone_conductivity_w_mk + (1-fraction) / cfg.LAMBDA0)
        if well_id in (a.index, b.index):
            permeability = 0.0
        tfc.set_face(face, perm=permeability, heat_cond=conductivity)
    return bands


def run_case(case):
    """引用原模型和CoolProp水接口，保存日数据与1/5/10年场。

    Args:
        case: settings.Case；参数在settings.py统一维护。

    Returns:
        dict: 原solve返回的计算摘要。

    Raises:
        ModuleNotFoundError: 当前解释器未安装CoolProp。
        ValueError: 静水压力超出水物性表范围。
        FileExistsError: 已有结果，避免意外覆盖。
    """
    prepare_runtime()
    try:
        from CoolProp import __version__ as coolprop_version
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("此高温工况需要CoolProp，请在运行解释器中安装requirements.txt；不采用旧水公式外推。") from exc
    import numpy as np
    from zmlx import tfc
    from zmlx.fluids.cp import create_fludef, h2o_density
    from zmlx.scen.geothermal.cases.carbonate_enhancement.new._well_cross_section import create, solve

    output = cfg.RESULTS / case.name
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"已有结果：{output}。请先重命名该目录，再运行，避免新旧数据混用。")
    depths, pressures = hydrostatic_profile(h2o_density)
    center_pressure = float(np.interp(cfg.DEPTH_M, depths, pressures))
    local = np.interp([cfg.DEPTH_M - 50, cfg.DEPTH_M + 50], depths, pressures)
    if local.min() <= cfg.WATER_P_MIN or local.max() >= cfg.WATER_P_MAX:
        raise ValueError("局部静水压力超出水表，请先调整settings中的表范围")
    print(f"{case.name}: 井中心静水绝对压力={center_pressure / 1e6:.6f} MPa；水位假设在地表", flush=True)
    nodes = cfg.grid_nodes()
    count = len(nodes) - 1
    outer_center = (nodes[-1] + nodes[-2]) / 2

    def temperature(x, y, z):
        """返回地温K：井中心155.2℃，向上每米减0.0287℃。

        Args:
            x, y, z: 相对井中心坐标m；z向上。

        Returns:
            float: 初始地温K。
        """
        return 273.15 + cfg.TEMPERATURE_C - cfg.GRADIENT_K_M*z

    def pressure(x, y, z):
        """按静水柱插值返回绝对压力Pa，无侧向水头坡度。

        Args:
            x, y, z: 相对井中心坐标m；只使用z。

        Returns:
            float: 初始绝对压力Pa。
        """
        return float(np.interp(cfg.DEPTH_M-z, depths, pressures))

    def rock_density(x, y, z):
        """返回等效骨架密度kg/m³；最外侧列沿用砂岩的大热容热边界。

        Args:
            x, y, z: 相对井中心坐标m；边界只判断x。

        Returns:
            float: 骨架密度或热缓冲等效密度kg/m³。
        """
        return cfg.ROCK_DENSITY * (1e6 if abs(x) >= outer_center - 1e-8 else 1)

    # 复用项目已有CoolProp建表；其比热为温压表域49点平均常数，详见README。
    water = create_fludef("water", t_min=cfg.WATER_T_MIN, t_max=cfg.WATER_T_MAX,
                          p_min=cfg.WATER_P_MIN, p_max=cfg.WATER_P_MAX, name="h2o")
    model = create(jx=count, jz=count, xr=nodes, zr=nodes, well_pos=(0, 0),
                   well_d=cfg.WELL_DIAMETER_M, rock_density=rock_density,
                   rock_heat_capacity=cfg.ROCK_CP, rock_heat_cond=cfg.LAMBDA0,
                   perm=cfg.K0, porosity=cfg.POROSITY, reservoir_temp=temperature,
                   well_temp=cfg.WELL_TEMPERATURE_K, pressure=pressure,
                   fluid_definitions=[water], sealed_well=True, dt_max=86400,
                   track_power=False)
    model.gravity = [0, 0, -cfg.GRAVITY]
    bands = configure_zone(model, case, tfc)
    info = dict(case.metadata(), depth_m=cfg.DEPTH_M, temperature_reference_c=cfg.TEMPERATURE_C,
                geothermal_gradient_k_m=cfg.GRADIENT_K_M, permeability_m2=cfg.K0,
                conductivity_w_mk=cfg.LAMBDA0, porosity=cfg.POROSITY,
                rock_density_kg_m3=cfg.ROCK_DENSITY, rock_cp_j_kgk=cfg.ROCK_CP,
                pressure_center_absolute_pa=center_pressure, gravity_m_s2=cfg.GRAVITY,
                water_level_depth_m=0, pressure_method="RK4 hydrostatic integral; CoolProp pure water; 5 m step",
                water_backend="CoolProp HEOS Water", coolprop_version=coolprop_version,
                water_specific_heat_j_kgk=water.specific_heat,
                water_table_p_pa=[cfg.WATER_P_MIN, cfg.WATER_P_MAX],
                water_table_t_k=[cfg.WATER_T_MIN, cfg.WATER_T_MAX],
                head_gradient=0.0, hydraulic_boundary="closed", sealed_well=True,
                lateral_thermal_buffer=True, grid_nodes_m=nodes, grid_shape=[count, count],
                well_temperature_k=cfg.WELL_TEMPERATURE_K, well_diameter_m=cfg.WELL_DIAMETER_M,
                coefficient_method="harmonic line fraction through union of irregular fracture bands",
                geometry_type="irregular_fracture_bands", fracture_paths_xz_m=bands.paths,
                fracture_band_width_m=cfg.FRACTURE_BAND_WIDTH_M,
                schema=cfg.SCHEMA, days_requested=cfg.DAYS, study_settings=cfg.study_settings())
    output.mkdir(parents=True, exist_ok=True)
    # 建模后、求解前也保存假设和全水柱，便于核查压力来源。
    (output / "parameters.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    geometry = dict(paths_xz_m=bands.paths, band_width_m=cfg.FRACTURE_BAND_WIDTH_M,
                    extent_m=case.radius_m, schema=cfg.SCHEMA)
    (output / "fractures.json").write_text(json.dumps(geometry, ensure_ascii=False, indent=2), encoding="utf-8")
    centers = (np.asarray(nodes[:-1])+np.asarray(nodes[1:]))/2
    mask = bands.mask(centers, centers)
    well_index = int(model.get_text(key="well_cell_id"))
    mask.flat[well_index] = False
    np.savez_compressed(output / "fracture_layout.npz", x_m=centers, depth_m=cfg.DEPTH_M-centers,
                        fracture_mask=mask, permeability_m2=np.where(mask, case.zone_permeability_m2, cfg.K0),
                        conductivity_w_mk=np.where(mask, case.zone_conductivity_w_mk, cfg.LAMBDA0))
    np.savetxt(output / "hydrostatic_profile.csv", np.c_[depths, pressures], delimiter=",",
               header="depth_m,absolute_pressure_pa", comments="")
    return solve(model, count, count, time_max=cfg.DAYS*86400, folder=output,
                 save_days=cfg.SAVE_DAYS, parameters=info)


def main():
    """选择基准、单个增强工况或整组计算；不自动绘图。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[*cfg.BY_NAME, "radius", "thermal", "all"], default="all")
    args = parser.parse_args()
    names = {"radius": ("baseline", "A1", "A2", "A3", "A4"),
             "thermal": ("baseline", "A3", "B1", "B2", "B3", "B4"), "all": tuple(cfg.BY_NAME)}
    for name in names.get(args.case, (args.case,)):
        folder = cfg.RESULTS / name
        # 组运行跳过已存在的完整结果，但不对不完整结果静默续算。
        if (folder / "summary.json").is_file() and args.case in names:
            saved = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
            expected = cfg.BY_NAME[name].metadata()
            files = [folder / "daily.csv", folder / "fractures.json", folder / "fracture_layout.npz",
                     *(folder / f"fields_day_{day:04d}.npz" for day in cfg.SAVE_DAYS)]
            if (saved.get("schema") == cfg.SCHEMA and saved.get("days") == cfg.DAYS
                    and saved.get("study_settings") == cfg.study_settings()
                    and all(saved.get(k) == v for k, v in expected.items())
                    and all(path.is_file() for path in files)):
                print(f"跳过参数匹配的完整工况 {name}", flush=True)
                continue
        run_case(cfg.BY_NAME[name])


if __name__ == "__main__":
    main()

