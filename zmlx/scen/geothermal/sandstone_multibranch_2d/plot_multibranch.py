"""独立读取多分支CSV/NPZ，生成采热对比、温度/z₀场及评价表；不求解模型。"""

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
os.environ["MPLCONFIGDIR"] = str(RESULTS / "runtime" / "matplotlib")

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import Circle
from matplotlib.ticker import FuncFormatter, ScalarFormatter

#: 与砂岩plot_sandstone_10years一致的字体、字号、向内刻度和数学字体。
STYLE = {"font.family": "Microsoft YaHei", "font.size": 14, "xtick.direction": "in",
         "ytick.direction": "in", "xtick.major.size": 3, "ytick.major.size": 3,
         "axes.unicode_minus": False, "mathtext.default": "regular"}
COLORS = ("black", "#E41A1C", "#377EB8", "#4DAF4A")


def load_data():
    """读取已完成工况，检查参数相同、各井合计及功率热量一致性。

    Returns:
        dict: 以分支数为键的参数、日数据和快照。

    Raises:
        FileNotFoundError: 缺少N1基准或工况只有未完成的部分结果。
        ValueError: 数据格式、参数或能量统计不一致。
    """
    loaded = {}
    reference = None
    for count in (1, 2, 3, 4):
        folder = RESULTS / f"N{count}"
        if not folder.exists():
            print(f"未找到N{count}，暂不绘制该工况。", flush=True)
            continue
        summary_path = folder / "summary.json"
        if not summary_path.is_file():
            raise FileNotFoundError(f"N{count}尚未完成：{summary_path}")
        info = json.loads(summary_path.read_text(encoding="utf-8"))
        if info.get("schema") != "sandstone-parallel-wells-2d-v1" or info.get("branch_count") != count:
            raise ValueError(f"N{count}结果格式不匹配")
        if reference is None:
            reference = info["parameters"]
        if info["parameters"] != reference:
            raise ValueError("对照工况的网格、井距、时长或砂岩参数不一致，不能直接对比")
        with (folder / "daily.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)]
        days = int(info["days"])
        if len(rows) != days or any(row["day"] != i for i, row in enumerate(rows, 1)):
            raise ValueError(f"N{count}日数据必须连续完整")
        if not all(np.isfinite(value) for row in rows for value in row.values()):
            raise ValueError(f"N{count}日数据有非有限数值")
        power = np.asarray([row["daily_power_w_per_m"] for row in rows])
        heat = np.asarray([row["cumulative_heat_kwh_per_m"] for row in rows])
        if not np.allclose(np.diff(np.r_[0, heat])*1000/24, power, rtol=1e-7, atol=1e-6):
            raise ValueError(f"N{count}日功率与累计热量不一致")
        for row in rows:
            checks = ((sum(row[f"well_{i}_power_w_per_m"] for i in range(1, count+1)), row["daily_power_w_per_m"]),
                      (sum(row[f"well_{i}_heat_kwh_per_m"] for i in range(1, count+1)), row["cumulative_heat_kwh_per_m"]),
                      (row["mean_branch_power_w_per_m"]*count, row["daily_power_w_per_m"]),
                      (row["mean_branch_heat_kwh_per_m"]*count, row["cumulative_heat_kwh_per_m"]))
            if any(not np.isclose(a, b, rtol=1e-7, atol=1e-6) for a, b in checks):
                raise ValueError(f"N{count}合计与各分支统计不一致")
        snapshots = {}
        for day in sorted({d for d in (365, 1825, 3650, days) if d <= days}):
            path = folder / f"fields_day_{day:04d}.npz"
            with np.load(path, allow_pickle=False) as archive:
                field = dict(archive)
            if (int(field["day"]) != day or len(field["well_indices"]) != count or
                    field["rock_temperature_c"].shape != (info["parameters"]["grid_count"],)*2):
                raise ValueError(f"N{count}场时刻、井数或网格不一致")
            if not np.allclose(field["well_positions_xz_m"], info["well_positions_actual_xz_m"]):
                raise ValueError(f"N{count}场数据与摘要井位不一致")
            snapshots[day] = field
        loaded[count] = dict(info=info, rows=rows, power=power, heat=heat, fields=snapshots)
    if 1 not in loaded:
        raise FileNotFoundError("需要先运行N1作为同网格、同参数的单井基准")
    return loaded


def save(fig, filename):
    """保存300dpi图片并关闭图形。

    Args:
        fig: Matplotlib图形。
        filename: PNG文件名。
    """
    folder = RESULTS / "plots"
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / filename, dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"Saved: {folder / filename}", flush=True)


def format_axes(ax, days, ylabel):
    """统一曲线坐标、向内刻度和原点标签。

    Args:
        ax: 坐标轴。
        days: 运行天数。
        ylabel: 纵坐标含义和单位。
    """
    ax.set(xlabel="时间 (年)", ylabel=ylabel, xlim=(0, days/365))
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    lo, hi = ax.get_ylim()
    if lo >= 0:
        ax.set_ylim(0, hi)
        ax.yaxis.set_major_formatter(FuncFormatter(
            lambda v, pos: "" if abs(v) < 1e-12 else f"{v:g}"))
    ax.legend(frameon=False, fontsize=11)


def draw_curves(data):
    """绘制合计、单位总井长及各分支采热曲线。

    Args:
        data: 已校验的结果。
    """
    days = data[1]["info"]["days"]
    specs = (("power", False, "合计日采热功率 (W/m)", "total_power.png"),
             ("power", True, "单位总井长日采热功率 (W/m)", "mean_branch_power.png"),
             ("heat", False, "累计采热量合计 (kWh/m)", "total_heat.png"),
             ("heat", True, "单位总井长累计采热量 (kWh/m)", "mean_branch_heat.png"))
    for name, divide, label, filename in specs:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for count, case in data.items():
            x = np.arange(1, days+1)/365
            ax.plot(x, case[name]/(count if divide else 1), color=COLORS[count-1],
                    linewidth=2, label=rf"$N={count}$")
        format_axes(ax, days, label)
        fig.tight_layout()
        save(fig, filename)
    for count, case in data.items():
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for i in range(1, count+1):
            ax.plot(np.arange(1, days+1)/365,
                    [row[f"well_{i}_power_w_per_m"] for row in case["rows"]],
                    linewidth=1.8, label=f"分支 {i}")
        format_axes(ax, days, "分支日采热功率 (W/m)")
        fig.tight_layout()
        save(fig, f"N{count}_individual_power.png")


def panel(ax, field, info, name, levels, label):
    """绘制方形六色带及等值线，标出所有分支，不绘制Darcy流速。

    Args:
        ax: 坐标轴。
        field: NPZ场数据。
        info: 工况摘要。
        name: 需要绘制的场字段。
        levels: 共用的七个边界，对应六个色带。
        label: 色标文字。
    """
    p = info["parameters"]
    half, depth = p["half_width_m"], p["depth_m"]
    x, d = field["x_m"], field["depth_m"]
    values = np.ma.masked_invalid(np.pad(field[name].T, 1, mode="edge"))
    xx, dd = np.r_[-half, x, half], np.r_[depth+half, d, depth-half]
    filled = ax.contourf(xx, dd, values, levels=levels,
                         cmap="coolwarm" if name == "rock_temperature_c" else "viridis")
    inside = levels[(levels > values.min()) & (levels < values.max())]
    if inside.size:
        ax.contour(xx, dd, values, levels=inside, colors="black", linewidths=0.4, alpha=0.45)
    bar = ax.figure.colorbar(filled, ax=ax, ticks=levels, label=label, shrink=0.75)
    formatter = ScalarFormatter(useOffset=False)
    formatter.set_scientific(False)
    bar.ax.yaxis.set_major_formatter(formatter)
    bar.ax.tick_params(direction="in")
    for i, (xw, zw) in enumerate(field["well_positions_xz_m"], 1):
        # 半径2m只是可读性标记，真实井径记录于参数，未按圈面积采热。
        ax.add_patch(Circle((xw, depth-zw), 2, fill=False, color="black", linewidth=0.9))
        ax.annotate(str(i), (xw, depth-zw), xytext=(3, 5), textcoords="offset points", fontsize=9)
    ax.set(xlabel="X (m)", ylabel="深度 (m)", xlim=(-half, half),
           ylim=(depth+half, depth-half), xticks=np.linspace(-half, half, 5),
           yticks=np.linspace(depth-half, depth+half, 5))
    ax.set_box_aspect(1)


def draw_fields(data):
    """输出第1、5、10年温度与z₀组合图以及N1的第1/10年组合。

    Args:
        data: 已校验的结果。
    """
    fields = [f for case in data.values() for f in case["fields"].values()]
    specs = []
    for name, label, title in (("rock_temperature_c", "温度 (℃)", "温度场"),
                               ("fluid_z0_m", r"$z_0$ (m)", r"流体 $z_0$")):
        lo = np.floor(min(np.nanmin(f[name]) for f in fields))
        hi = np.ceil(max(np.nanmax(f[name]) for f in fields))
        specs.append((name, np.linspace(lo, max(lo+1, hi), 7), label, title))
    for day in data[1]["fields"]:
        fig, axes = plt.subplots(len(data), 2, figsize=(12, 5*len(data)),
                                 layout="constrained", squeeze=False)
        fig.suptitle(f"第{day/365:g}年：平行分支数量对比")
        for row, (count, case) in enumerate(data.items()):
            for col, (name, levels, label, title) in enumerate(specs):
                panel(axes[row, col], case["fields"][day], case["info"], name, levels, label)
                axes[row, col].set_title(f"N={count} · {title}")
        save(fig, f"fields_day_{day:04d}_comparison.png")
    days = [day for day in (365, 3650) if day in data[1]["fields"]]
    if days:
        fig, axes = plt.subplots(len(days), 2, figsize=(12, 5*len(days)),
                                 layout="constrained", squeeze=False)
        for row, day in enumerate(days):
            for col, (name, levels, label, title) in enumerate(specs):
                panel(axes[row, col], data[1]["fields"][day], data[1]["info"], name, levels, label)
                axes[row, col].set_title(f"N=1 · 第{day/365:g}年 · {title}")
        save(fig, "N1_temperature_z0_year1_year10.png")


def write_evaluation(data):
    """输出逐日对比表和关键年份表、末日累计热量及增幅柱状图。

    Args:
        data: 已校验的同参数工况。

    Raises:
        ValueError: N1功率或累计热量为零，不能求相对指标。
    """
    base = data[1]
    days = base["info"]["days"]
    evaluated = []
    for day in range(1, days+1):
        p0, q0 = base["power"][day-1], base["heat"][day-1]
        if p0 <= 0 or q0 <= 0:
            raise ValueError("N1参考输出非正，无法计算增幅与独立井参考比")
        for count, case in data.items():
            p, q = case["power"][day-1], case["heat"][day-1]
            evaluated.append(dict(day=day, year=day/365, branch_count=count,
                                  total_power_w_per_m=p, total_heat_kwh_per_m=q,
                                  per_total_well_length_power_w_per_m=p/count,
                                  per_total_well_length_heat_kwh_per_m=q/count,
                                  power_gain_percent=100*(p/p0-1), heat_gain_percent=100*(q/q0-1),
                                  independent_well_reference_ratio=q/(count*q0)))
    folder = RESULTS / "tables"
    folder.mkdir(parents=True, exist_ok=True)
    selected = {d for d in (365, 1825, 3650, days) if d <= days}
    for filename, rows in (("daily_comparison.csv", evaluated),
                           ("selected_years.csv", [r for r in evaluated if r["day"] in selected])):
        with (folder / filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved: {folder / filename}", flush=True)
    final = [r for r in evaluated if r["day"] == days]
    lines = [f"# 第{days/365:g}年累计采热评价", "",
             "合计按各分支共同轴向1m统计；单位总井长值=合计/N。参考比=Q_N/(N Q_1)。", "",
             "|分支数|合计累计采热(kWh/m)|单位总井长(kWh/m)|累计增幅(%)|独立井参考比|",
             "|---|---|---|---|---|"]
    for r in final:
        lines.append(f"|{r['branch_count']}|{r['total_heat_kwh_per_m']:.2f}|"
                     f"{r['per_total_well_length_heat_kwh_per_m']:.2f}|{r['heat_gain_percent']:.2f}|"
                     f"{r['independent_well_reference_ratio']:.4f}|")
    (folder / "final_heat_evaluation.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for ax, name, label, digits in ((axes[0], "total_heat_kwh_per_m", "累计采热量合计 (kWh/m)", 1),
                                    (axes[1], "heat_gain_percent", "相对单井累计采热增幅 (%)", 2)):
        values = [r[name] for r in final]
        bars = ax.bar([f"N={r['branch_count']}" for r in final], values,
                      color=[COLORS[r["branch_count"]-1] for r in final], width=0.55)
        ax.bar_label(bars, fmt=f"%.{digits}f", fontsize=10, padding=3)
        ax.set_ylabel(label)
        ax.margins(y=0.17)
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        ax.set_title(f"第{days/365:g}年")
    save(fig, "final_cumulative_heat_bars.png")


def main():
    """校验结果后单独出图和评价表，不调用任何模型求解入口。"""
    data = load_data()
    with plt.rc_context(STYLE):
        draw_curves(data)
        draw_fields(data)
        write_evaluation(data)


if __name__ == "__main__":
    main()
