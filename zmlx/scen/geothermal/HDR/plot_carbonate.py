"""独立读取碳酸盐岩结果，生成场图、功率/累计采热曲线及增幅表和柱状图。

不导入求解器或CoolProp，不重算，不插值替代缺失年份。
"""

import argparse
import csv
import json
import os
import sys

sys.dont_write_bytecode = True
if __package__:
    from . import settings as cfg
else:
    import settings as cfg
os.environ["MPLCONFIGDIR"] = str(cfg.RESULTS / "runtime" / "matplotlib")
import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter, ScalarFormatter

STYLE = {"font.family": "Microsoft YaHei", "font.size": 14, "legend.fontsize": 11,
         "xtick.direction": "in", "ytick.direction": "in", "xtick.major.size": 3,
         "ytick.major.size": 3, "axes.unicode_minus": False, "mathtext.default": "regular"}
COLORS = ("black", "#377EB8", "#E41A1C", "#4DAF4A", "#984EA3")


def load_data(keys):
    """校验参数和能量一致性后读取各工况的每日曲线、年度快照。

    Args:
        keys: 工况名称序列。

    Returns:
        dict: 按工况索引的日数据和年份场数据。

    Raises:
        ValueError: 参数、时长、网格或能量核对失败。
        FileNotFoundError: 必要结果尚未计算。
    """
    data = {}
    for key in keys:
        folder, case = cfg.RESULTS / key, cfg.BY_NAME[key]
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        if (summary.get("schema") != cfg.SCHEMA or summary.get("days") != cfg.DAYS
                or summary.get("study_settings") != cfg.study_settings()
                or any(summary.get(k) != v for k, v in case.metadata().items())):
            raise ValueError(f"{key}参数与当前settings不一致，请勿混用旧结果")
        with (folder / "daily.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        day = np.asarray([float(row["day"]) for row in rows])
        power = np.asarray([float(row["daily_power_w_per_m"]) for row in rows])
        heat = np.asarray([float(row["cumulative_heat_kwh_per_m"]) for row in rows])
        if not np.array_equal(day, np.arange(1, cfg.DAYS + 1)):
            raise ValueError(f"{key}缺少连续十年日数据")
        if (not np.all(np.isfinite(power)) or not np.all(np.isfinite(heat))
                or not np.allclose(np.diff(np.r_[0, heat]) * 1000 / 24, power)):
            raise ValueError(f"{key}功率与累计采热量增量不一致")
        geometry = json.loads((folder / "fractures.json").read_text(encoding="utf-8"))
        if geometry.get("schema") != cfg.SCHEMA or geometry.get("paths_xz_m") != summary.get("fracture_paths_xz_m"):
            raise ValueError(f"{key}裂缝几何与计算摘要不一致")
        fields = {}
        for target in cfg.SAVE_DAYS:
            with np.load(folder / f"fields_day_{target:04d}.npz", allow_pickle=False) as archive:
                field = dict(archive)
            shape = (len(cfg.grid_nodes())-1,)*2
            if int(field["day"]) != target or field["rock_temperature_c"].shape != shape:
                raise ValueError(f"{key}场时刻或网格错误")
            field["fracture_paths_xz_m"] = geometry["paths_xz_m"]
            fields[target//365] = field
        data[key] = dict(year=day / 365, power=power, heat=heat, fields=fields)
    return data


def save(fig, filename):
    """保存300dpi透明PNG并打印绝对路径。

    Args:
        fig: Matplotlib图。
        filename: 图片文件名。
    """
    folder = cfg.RESULTS / "plots"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    fig.savefig(path, dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"Saved: {path}", flush=True)


def legend(key):
    """返回短图例；基准给具体值，增强组给变化参数。

    Args:
        key: 工况名。

    Returns:
        str: 数学下标格式统一的图例。
    """
    case = cfg.BY_NAME[key]
    if key == "baseline":
        return "基准"
    if key.startswith("A"):
        return rf"{key}: $L_f={case.radius_m:g}\ \mathrm{{m}}$"
    return rf"{key}: $\lambda={case.zone_conductivity_w_mk:g}\ \mathrm{{W}}/(\mathrm{{m}}\cdot\mathrm{{K}})$"


def parameter_note(group):
    """给图下方添加共用参数，缩短各条曲线图例。

    Args:
        group: baseline、radius或thermal。

    Returns:
        str: 明确区分区内和区外的参数文字。
    """
    base = (rf"$k_0={cfg.K0/cfg.MD_M2:.5f}\ \mathrm{{mD}},\quad "
            rf"\lambda_0={cfg.LAMBDA0:g}\ \mathrm{{W}}/(\mathrm{{m}}\cdot\mathrm{{K}})$")
    zone = rf"$k_{{\mathrm{{zone}}}}={cfg.K_ZONE/cfg.MD_M2:.2f}\ \mathrm{{mD}}$"
    if group == "radius":
        return base + "；裂缝带 " + zone + r"，$\lambda=\lambda_0$"
    if group == "thermal":
        return base + "；裂缝带 " + zone + r"，$L_f=10\ \mathrm{m}$；参照 A3"
    return base


def curves(data, keys, group):
    """分别绘制日采热功率与累计采热量，不用百分比曲线挤压小变化。

    Args:
        data: 校验后的结果。
        keys: 本图工况。
        group: 文件名及共用参数类型。
    """
    for quantity, ylabel in (("power", "日采热功率 (W/m)"), ("heat", "累计采热量 (kWh/m)")):
        fig, ax = plt.subplots(figsize=(8, 5.3))
        for key, color in zip(keys, COLORS):
            x, y = data[key]["year"], data[key][quantity]
            if quantity == "heat":
                x, y = np.r_[0, x], np.r_[0, y]
            ax.plot(x, y, label=legend(key), color=color, linewidth=1.8)
        ax.set(xlabel="时间 (年)", ylabel=ylabel, xlim=(0, 10), xticks=np.arange(0, 11, 2))
        if all(np.min(data[key][quantity]) >= 0 for key in keys):
            ax.set_ylim(bottom=0)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda value, pos: "" if value == 0 else f"{value:,.2f}".rstrip("0").rstrip(".")))
        ax.legend(frameon=False)
        ax.grid(ls="--", alpha=0.3)
        fig.text(0.5, 0.02, parameter_note(group), ha="center", fontsize=10)
        fig.tight_layout(rect=(0, 0.09, 1, 1))
        save(fig, f"{group}_{quantity}_10years.png")


def field_panel(ax, field, key, name, levels):
    """绘制正方形六色带等值线图，温度coolwarm，流体场viridis。

    Args:
        ax: 子图。
        field: 已保存的年度场。
        key: 工况名。
        name: 温度或z0的字段名。
        levels: 同类图共用的七个边界值，构成六个色带。
    """
    values = field[name]
    xx = np.r_[-50, field["x_m"], 50]
    dd = np.r_[cfg.DEPTH_M+50, field["depth_m"], cfg.DEPTH_M-50]
    vv = np.ma.masked_invalid(np.pad(values.T, 1, mode="edge"))
    temperature = name == "rock_temperature_c"
    filled = ax.contourf(xx, dd, vv, levels=levels, cmap="coolwarm" if temperature else "viridis")
    inside = levels[(levels > vv.min()) & (levels < vv.max())]
    if len(inside):
        ax.contour(xx, dd, vv, levels=inside, colors="black", linewidths=0.4, alpha=0.5)
    label = "温度 (℃)" if temperature else r"流体 $z_0$ (m)"
    bar = ax.figure.colorbar(filled, ax=ax, ticks=levels, label=label, shrink=0.7)
    formatter = ScalarFormatter(useOffset=False)
    formatter.set_scientific(False)
    bar.ax.yaxis.set_major_formatter(formatter)
    bar.ax.tick_params(direction="in")
    for path in field["fracture_paths_xz_m"]:
        points = np.asarray(path)
        ax.plot(points[:, 0], cfg.DEPTH_M-points[:, 1], color="#303030", linewidth=0.65, alpha=0.8)
    ax.plot(0, cfg.DEPTH_M, "ko", markersize=3)
    ax.set(xlabel="X (m)", ylabel="深度 (m)", xlim=(-50, 50),
           ylim=(cfg.DEPTH_M+50, cfg.DEPTH_M-50), xticks=(-50, -25, 0, 25, 50),
           yticks=cfg.DEPTH_M+np.array([-50, -25, 0, 25, 50]))
    ax.set_box_aspect(1)


def fields(data, keys, years, prefix):
    """只生成温度/z0合并图并叠加实际裂缝中心线，色标跨工况跨年份共用。

    Args:
        data: 已校验结果。
        keys: 工况名。
        years: 已保存年份。
        prefix: 文件名前缀。
    """
    names = ("rock_temperature_c", "fluid_z0_m")
    all_fields = [data[key]["fields"][year] for key in data for year in (1, 5, 10)]
    bounds = {}
    for name in names:
        low = min(np.nanmin(f[name]) for f in all_fields)
        high = max(np.nanmax(f[name]) for f in all_fields)
        bounds[name] = np.linspace(low, high if high > low else low+1, 7)
    for year in years:
        fig, axes = plt.subplots(len(keys), 2, figsize=(11, 4.4*len(keys)), layout="constrained", squeeze=False)
        fig.suptitle(f"第{year}年：温度场与流体 $z_0$；灰线为裂缝中心线")
        for row, key in enumerate(keys):
            for col, name in enumerate(names[:2]):
                field_panel(axes[row, col], data[key]["fields"][year], key, name, bounds[name])
                axes[row, col].set_title(legend(key) + (" · 温度场" if col == 0 else r" · 流体 $z_0$"), fontsize=12)
        save(fig, f"{prefix}_temperature_z0_year{year}.png")


def export_table_and_bars(data, keys, group):
    """导出1/5/10年评价表，并用累计采热量增幅柱状图显示增强效果。

    Args:
        data: 日数据。
        keys: 本组工况（含参照）。
        group: radius参照baseline；thermal参照A3。
    """
    reference = "baseline" if group == "radius" else "A3"
    rows = []
    for key in keys:
        case = cfg.BY_NAME[key]
        for year in (1, 5, 10):
            index = 365*year-1
            heat = data[key]["heat"][index]
            ref_heat = data[reference]["heat"][index]
            base_heat = data["baseline"]["heat"][index]
            rows.append(dict(case=key, year=year, fracture_extent_m=case.radius_m,
                             zone_permeability_md=case.zone_permeability_m2/cfg.MD_M2,
                             zone_conductivity_w_mk=case.zone_conductivity_w_mk,
                             daily_power_w_per_m=data[key]["power"][index], cumulative_heat_kwh_per_m=heat,
                             reference=reference, additional_heat_kwh_per_m=heat-ref_heat,
                             gain_vs_reference_pct=100*(heat/ref_heat-1) if ref_heat else float("nan"),
                             gain_vs_baseline_pct=100*(heat/base_heat-1) if base_heat else float("nan")))
    path = cfg.RESULTS / f"{group}_evaluation.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {path}", flush=True)
    targets = [key for key in keys if key != reference]
    fig, ax = plt.subplots(figsize=(8, 5.3))
    x = np.arange(len(targets))
    for i, year in enumerate((1, 5, 10)):
        values = [next(row["gain_vs_reference_pct"] for row in rows if row["case"] == key and row["year"] == year) for key in targets]
        bars = ax.bar(x+(i-1)*0.24, values, width=0.24, label=f"第{year}年")
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)
    ax.set(xticks=x, xticklabels=targets, ylabel=f"累计采热量相对{reference}增幅 (%)")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.legend(frameon=False)
    ax.margins(y=0.18)
    ax.grid(axis="y", ls="--", alpha=0.3)
    fig.text(0.5, 0.02, "；".join(legend(key) for key in targets), ha="center", fontsize=10)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    save(fig, f"{group}_cumulative_heat_gain_bars.png")


def main():
    """按组读取已有结果并出图；缺少结果时报出具体路径，不自动运行计算。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("all", "radius", "thermal", "baseline"), default="all")
    args = parser.parse_args()
    radius = ("baseline", "A1", "A2", "A3", "A4")
    thermal = ("A3", "B1", "B2", "B3", "B4")
    needed = {"all": tuple(cfg.BY_NAME), "radius": radius,
              "thermal": ("baseline", *thermal), "baseline": ("baseline",)}
    data = load_data(needed[args.group])
    with plt.rc_context(STYLE):
        curves(data, ("baseline",), "baseline")
        fields(data, ("baseline",), (1, 5, 10), "baseline")
        for group, keys in (("radius", radius), ("thermal", thermal)):
            if args.group in ("all", group):
                curves(data, keys, group)
                fields(data, keys, (1, 5, 10), group)
                export_table_and_bars(data, keys, group)


if __name__ == "__main__":
    main()
