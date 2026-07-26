"""Gas-aqueous migration with batched PyTorch/Reaktoro equilibrium."""

from concurrent.futures import ThreadPoolExecutor
from os import cpu_count
from pathlib import Path
from threading import local

import numpy as np

from zmlx import *


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / (
    "gas_aq_uv_surrogate_augmented_round5_scale_invariant_h256"
) / "gas_aq_uv_surrogate_h256_e1000_trajectory.pt"
# 每隔 ANCHOR_INTERVAL 次平衡调用，强制所有网格使用 Reaktoro 重新锚定，
# 防止代理模型误差在连续时间步中累积。
ANCHOR_INTERVAL = 25

# 代理模型训练域的组分总质量上限；乘以 1.05 留出约 5% 的边界裕量。
# 超出该范围的网格不使用代理模型，而直接回退到 Reaktoro。
DOMAIN_LIMITS = np.array((3.0e3, 2.0e2, 5.0, 20.0)) * 1.05

# ------------------------- 松弛因子相关参数 -------------------------
# 参考流动时间步：4 天。当前时间步相对该值的比例用于调整允许变化幅度。
RELAX_REFERENCE_DT = 4.0 * 24.0 * 3600.0

# 在参考时间步内，单次允许的气相质量分数变化基准值为 0.05。
RELAX_FRACTION_REF = 0.05
# 无论时间步多大或多小，气相质量分数的允许变化限制在 0.01～0.10。
RELAX_FRACTION_RANGE = (0.01, 0.10)
# 若代理模型预测的单次气相质量分数跃变超过 0.30，认为预测过于激烈，
# 不再使用松弛后的代理结果，而直接回退到 Reaktoro。
RELAX_FRACTION_HARD = 0.30

# 在参考时间步内，单次允许的温度变化基准值为 2 K。
RELAX_TEMPERATURE_REF = 2.0
# 温度允许变化范围限制在 0.5～5 K。
RELAX_TEMPERATURE_RANGE = (0.5, 5.0)
# 若代理模型预测的温度跃变超过 20 K，直接回退到 Reaktoro。
RELAX_TEMPERATURE_HARD = 20.0

# 松弛系数 alpha 的下限。即使预测变化很大，每次仍至少推进目标变化的 5%，
# 避免状态完全冻结；alpha 最大为 1，表示直接接受目标平衡状态。
RELAX_ALPHA_MIN = 0.05

# 判断 CH4、N2、He 组分是否“实际存在”的相对质量阈值。
# 极微量组分不参与最大相分数跳变的计算，避免数值噪声主导松弛系数。
RELAX_PRESENCE_FRACTION = 1.0e-12

_pool = ThreadPoolExecutor(max_workers=cpu_count() or 1)
_rtk_local = local()
_surrogate = None
_calls = {}


def _get_surrogate():
    global _surrogate
    if _surrogate is None:
        import torch
        from zmlx.scen.uv_equilibrium.train_gas_aq_uv_surrogate import (
            GasAqueousUVSurrogate,
        )
        torch.set_num_threads(1)
        _surrogate = GasAqueousUVSurrogate.from_checkpoint(MODEL_PATH)
    return _surrogate


def _get_reaktoro():
    if not hasattr(_rtk_local, "solver"):
        from zmlx.scen.uv_equilibrium.gas_aq_uv_equilibrium import (
            GasAqueousUVEquilibrium,
        )
        _rtk_local.solver = GasAqueousUVEquilibrium()
    return _rtk_local.solver


def _solve_reaktoro(args):
    index, temperature, pressure, masses = args
    solver = _get_reaktoro()
    result = solver.solve(temperature, pressure, masses)
    value = solver.last_temperature if result is not None else temperature
    return index, value, result


def _domain_mask(temperature, pressure, masses):
    totals = np.maximum(masses[:, :4], 0.0) + np.maximum(masses[:, 4:], 0.0)
    return (
        (temperature >= 273.15) & (temperature <= 800.0)
        & (pressure >= 1.0e6) & (pressure <= 200.0e6)
        & np.all(totals <= DOMAIN_LIMITS, axis=1)
    )


def _conserve(before, predicted):
    # 对每个化学组分分别计算平衡前的总质量（气相质量 + 水相质量）。
    # 后续只采用预测的气/水分配比例，再用原始总质量重构两相质量，
    # 从而严格保证 H2O、CH4、N2、He 各组分在一次平衡调用前后质量守恒。
    totals = np.maximum(before[:, :4], 0.0) + np.maximum(before[:, 4:], 0.0)
    safe = np.where(np.isfinite(predicted) & (predicted > 0.0), predicted, 0.0)
    predicted_totals = safe[:, :4] + safe[:, 4:]
    fraction = np.divide(
        safe[:, :4], predicted_totals,
        out=np.zeros_like(totals), where=predicted_totals > 0.0,
    )
    gas = totals * fraction
    return np.concatenate((gas, totals - gas), axis=1)


def _relax_surrogate(before_temperature, target_temperature, before_masses,
                     target_masses, dt):
    # 对代理模型给出的目标平衡状态进行自适应欠松弛。
    # 松弛公式为：new = old + alpha * (target - old)。
    # alpha 同时受气相质量分数跃变和温度跃变约束，并取两者中更严格者。
    # 该处理用于抑制“流动计算—瞬时化学平衡”交替耦合产生的相态振荡；
    # 异常的大跳变不会仅靠松弛处理，而是直接回退到 Reaktoro 求解。
    before_temperature = np.asarray(before_temperature, dtype=float)
    target_temperature = np.asarray(target_temperature, dtype=float)
    before = np.maximum(np.asarray(before_masses, dtype=float), 0.0)
    target = np.maximum(np.asarray(target_masses, dtype=float), 0.0)
    # 质量矩阵前 4 列为气相 H2O/CH4/N2/He，后 4 列为对应水相组分。
    # 这里求出平衡前和代理模型目标状态下的各组分总质量。
    totals = before[:, :4] + before[:, 4:]
    target_totals = target[:, :4] + target[:, 4:]
    # 将绝对质量转换为“各组分进入气相的质量分数”。
    # 松弛作用于相分配比例，而不是直接对气相、水相质量分别线性插值，
    # 因而更容易在保持组分总质量不变的条件下抑制相态突跳。
    current_fraction = np.divide(
        before[:, :4], totals, out=np.zeros_like(totals), where=totals > 0.0,
    )
    target_fraction = np.divide(
        target[:, :4], target_totals,
        out=np.zeros_like(target_totals), where=target_totals > 0.0,
    )
    # 只检查实际存在的 CH4、N2、He；第 0 列 H2O 不用于控制气体相分数松弛。
    # 对低于相对阈值的痕量组分忽略其分数变化，避免“极小分母”造成虚假大跳变。
    active = totals[:, 1:4] > (
        totals.sum(axis=1, keepdims=True) * RELAX_PRESENCE_FRACTION
    )
    # 代理目标与当前状态之间的气相分数差值。
    # 每个网格以 CH4、N2、He 中最大的有效跳变作为该网格的控制量。
    fraction_delta = target_fraction[:, 1:4] - current_fraction[:, 1:4]
    max_fraction_jump = np.max(
        np.where(active, np.abs(fraction_delta), 0.0), axis=1,
    )
    # 温度变化也可能诱发流动—平衡耦合振荡，因此与相分数变化共同限制 alpha。
    temperature_jump = np.abs(target_temperature - before_temperature)

    # 时间步越大，允许一次平衡校正推进得越多；时间步越小，允许变化越小。
    # clip 仍会把实际允许值限制在预设的上下界内。
    scale = max(float(dt), 1.0) / RELAX_REFERENCE_DT
    fraction_limit = np.clip(
        RELAX_FRACTION_REF * scale, *RELAX_FRACTION_RANGE,
    )
    temperature_limit = np.clip(
        RELAX_TEMPERATURE_REF * scale, *RELAX_TEMPERATURE_RANGE,
    )
    # 若预测跳变没有超过允许值，则对应 alpha 为 1；
    # 若超过允许值，则 alpha = 允许跳变 / 预测跳变，使实际更新恰好受限。
    alpha_fraction = np.divide(
        fraction_limit, max_fraction_jump,
        out=np.ones_like(max_fraction_jump), where=max_fraction_jump > 0.0,
    )
    alpha_temperature = np.divide(
        temperature_limit, temperature_jump,
        out=np.ones_like(temperature_jump), where=temperature_jump > 0.0,
    )
    # 取相分数约束和温度约束中较小的 alpha，保证两种变化都不过快。
    # 最终 alpha 范围为 [RELAX_ALPHA_MIN, 1]。
    alpha = np.clip(
        np.minimum(alpha_fraction, alpha_temperature), RELAX_ALPHA_MIN, 1.0,
    )
    # “硬阈值”不同于普通松弛限制：一旦代理预测超过硬阈值，
    # 说明该网格可能处于强相变、外推或异常区域，不应仅靠欠松弛掩盖误差，
    # 后续将该网格标记为 fallback，并使用 Reaktoro 重新精确求解。
    fallback = (
        (max_fraction_jump > RELAX_FRACTION_HARD)
        | (temperature_jump > RELAX_TEMPERATURE_HARD)
    )

    # 对 CH4、N2、He 的气相分数执行：f_new = f_old + alpha*(f_target-f_old)。
    # H2O 的目标气相分数保持代理模型给出的值，随后在 balance 中重新并入水相。
    relaxed_fraction = target_fraction.copy()
    relaxed_fraction[:, 1:4] = (
        current_fraction[:, 1:4] + alpha[:, None] * fraction_delta
    )
    # 由松弛后的气相分数和原始组分总质量重构气相、水相质量。
    # 因此每个组分均满足：m_gas + m_aq = m_total。
    gas = totals * np.clip(relaxed_fraction, 0.0, 1.0)
    masses = np.concatenate((gas, totals - gas), axis=1)
    # 温度采用与相分数相同的网格级 alpha，保持热状态和相分配更新步调一致。
    temperature = before_temperature + alpha * (
        target_temperature - before_temperature
    )
    return temperature, masses, fallback


def _solve_batch(temperature, pressure, masses, anchor,
                 dt=RELAX_REFERENCE_DT):
    # anchor=True 时不允许使用代理模型，所有网格都由 Reaktoro 求解；
    # 非锚定步仅对处于训练域内的网格使用代理模型。
    candidates = (
        np.zeros(len(temperature), dtype=bool) if anchor
        else _domain_mask(temperature, pressure, masses)
    )
    next_temperature = temperature.copy()
    predicted = masses.copy()
    solved = np.zeros(len(temperature), dtype=bool)
    if np.any(candidates):
        try:
            values = _get_surrogate().solve_batch(
                temperature[candidates], pressure[candidates], masses[candidates]
            )
            valid = (
                np.isfinite(values[0]) & np.isfinite(values[1])
                & np.all(np.isfinite(values[2]), axis=1)
            )
            rows = np.flatnonzero(candidates)[valid]
            # 对代理模型预测的温度和气水相分配实施自适应松弛。
            relaxed_temperature, relaxed_masses, fallback = _relax_surrogate(
                temperature[rows], values[0][valid], masses[rows],
                values[2][valid], dt,
            )
            # 未触发硬阈值的网格接受松弛后的代理结果；
            # 触发 fallback 的网格保持 solved=False，随后自动转交 Reaktoro。
            accepted = ~fallback
            accepted_rows = rows[accepted]
            next_temperature[accepted_rows] = relaxed_temperature[accepted]
            predicted[accepted_rows] = relaxed_masses[accepted]
            solved[accepted_rows] = True
        except Exception:
            print("Surrogate failed; using Reaktoro fallback", flush=True)

    # 包括锚定步网格、代理域外网格、无效预测网格和硬阈值回退网格，
    # 统一使用 Reaktoro 并行求解。
    rtk_rows = np.flatnonzero(~solved)
    failed = []
    arguments = (
        (row, temperature[row], pressure[row], masses[row]) for row in rtk_rows
    )
    for row, value, result in _pool.map(_solve_reaktoro, arguments):
        if result is None:
            failed.append(row)
        else:
            next_temperature[row] = value
            predicted[row] = result

    # 温度出现非有限值时恢复到平衡前温度；随后对全部结果再次执行质量守恒修正。
    next_temperature = np.where(np.isfinite(next_temperature), next_temperature, temperature)
    corrected = _conserve(masses, predicted)
    if failed:
        corrected[failed] = masses[failed]
        print(f"Reaktoro warning cells: {len(failed)}/{len(rtk_rows)}", flush=True)
    return next_temperature, corrected


def _mass_matrix(mass):
    h2o, ch4aq, n2aq, heaq = (
        mass[name] for name in ("H2O", "CH4(aq)", "N2(aq)", "He(aq)")
    )
    ch4, n2, he = (mass[name] for name in ("CH4", "N2", "He"))
    return np.column_stack((np.zeros_like(h2o), ch4, n2, he, h2o, ch4aq, n2aq, heaq))


def create(jx, jz):
    mesh = create_cube(
        x=linspace(0, 300, jx + 1), y=(-0.5, 0.5), z=linspace(-500, 0, jz + 1)
    )
    gas = ch4.create()
    water = h2o.create()
    fluids = [
        FluDef.create(
            defs=[gas.get_copy("N2"), gas.get_copy("He"), gas.get_copy("CH4")],
            name="gas",
        ),
        FluDef.create(
            defs=[
                water.get_copy("H2O"), water.get_copy("N2(aq)"),
                water.get_copy("He(aq)"), water.get_copy("CH4(aq)"),
            ],
            name="aqueous",
        ),
    ]

    def temperature(_, __, z):
        return 300.15 - 0.0443 * z

    def pressure(_, __, z):
        return 15.0e6 - 1.0e4 * z

    def gas_region(x, y, z):
        return get_distance([x, y, z], [150, 0, -500]) < 50

    def saturation(x, y, z):
        return {"CH4": 1} if gas_region(x, y, z) else {"H2O": 1, "He(aq)": 0.001}

    z_min, z_max = mesh.get_pos_range(2)

    def heat_capacity(_, __, z):
        return 1.0e20 if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1 else 1.0e6

    model = tfc.create(
        mesh, porosity=lambda x, y, z: 1.0 if gas_region(x, y, z) else 0.1,
        pore_modulus=100.0e6, denc=heat_capacity, dist=0.1,
        temperature=temperature, p=pressure, s=saturation, perm=1.0e-14,
        heat_cond=2.0, fludefs=fluids, dt_max=3600 * 24 * 30.0,
        gravity=(0, 0, -10),
    )
    model.set_text(key="solve", text={"time_max": 3600 * 24 * 365 * 6})
    step_iteration.add_setting(model, name="balance", step=1, args=["@model"])
    _calls[str(model.handle_str)] = 0
    return model


def balance(model: Seepage):
    key = str(model.handle_str)
    call = _calls.get(key, 0) + 1
    _calls[key] = call
    arrays = as_numpy(model)
    pressure = arrays.cells.pre
    temperature = arrays.fluids("aqueous").get_attr("temperature")
    names = tfc.list_comp(model, keep_structure=False)
    mass = {name: arrays.fluids(name).mass for name in names}
    masses = _mass_matrix(mass)
    # 第 1 次及每隔 ANCHOR_INTERVAL 次调用执行 Reaktoro 锚定；其余时间步优先使用代理模型。
    # 当前 ZMLX 流动时间步 dt 被传入松弛函数，用于自适应调整单步允许变化幅度。
    temperature[:], result = _solve_batch(
        temperature, pressure, masses,
        anchor=call == 1 or call % ANCHOR_INTERVAL == 0,
        dt=float(tfc.get_dt(model)),
    )
    mass["H2O"][:] = result[:, 0] + result[:, 4]
    mass["CH4"][:], mass["N2"][:], mass["He"][:] = result[:, 1:4].T
    mass["CH4(aq)"][:], mass["N2(aq)"][:], mass["He(aq)"][:] = result[:, 5:8].T
    arrays.fluids("aqueous").set_attr("temperature", temperature)
    for name in names:
        arrays.fluids(name).mass = mass[name]


def show(model, jx, jz):
    def draw(figure):
        from zmlx.plt import AutoLayout
        layout = AutoLayout(
            figure, num_plots=6, subplot_aspect_ratio=0.6,
            aspect="equal", xlabel="x/m", ylabel="z/m",
        )
        x = tfc.get_x(model, shape=(jx, jz))
        z = tfc.get_z(model, shape=(jx, jz))
        angles = np.linspace(0, np.pi, 100)
        axis = layout.add_axes2(
            add_contourf, x, z, tfc.get_p(model, shape=(jx, jz)),
            cbar=dict(label="p", shrink=0.6), title="pressure", cmap="coolwarm",
        )
        axis.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), "k--")
        gas_volume = tfc.get_v(model, fid="gas", shape=(jx, jz))
        water_volume = tfc.get_v(model, fid="aqueous", shape=(jx, jz))
        axis = layout.add_axes2(
            add_contourf, x, z, gas_volume / (gas_volume + water_volume),
            cbar=dict(label="s", shrink=0.6), title="gas saturation",
        )
        axis.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), "r--")
        for name in ("CH4", "He"):
            for fluid in (name, f"{name}(aq)"):
                values = tfc.get_m(model, fid=fluid, shape=(jx, jz))
                values = np.log10(1.0 + values / max(values.max() * 1.0e-6, 1.0e-30))
                layout.add_axes2(
                    add_contourf, x, z, values,
                    cbar=dict(label="log mass", shrink=0.6), title=f"{fluid} mass",
                )

    return plot(
        draw, caption=f"Seepage({model.handle_str})",
        suptitle=f"time: {tfc.get_time(model, as_str=True)}",
        tight_layout=True, clear=True, gui_mode=True,
    )


def main():
    jx, jz = 60, 100
    model = create(jx, jz)
    tfc.solve(
        model, close_after_done=False,
        extra_plot=lambda: show(model, jx, jz), slots={"balance": balance},
    )


if __name__ == "__main__":
    gui.execute(main, close_after_done=False)
