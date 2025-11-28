import warnings
from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np

# ---------- 用户输入部分 ----------
user_reactant_pool = ["Ca++", "Mg++", "HCO3-", "H+", "OH-"]  # 多种反应物

# ---------- 原始与加密温度定义 ----------
T_celsius_raw = np.array([0, 25, 60, 100, 150, 200, 250, 300])
T_kelvin_raw = T_celsius_raw + 273.15
T_kelvin_dense = np.linspace(T_kelvin_raw.min(), T_kelvin_raw.max(), 100)


# ---------- 辅助函数 ----------
def extract_reaction_blocks(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    reactions = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == '':
            i += 1
            continue
        title = line
        i += 1
        while i < len(lines) and not lines[i].strip().endswith("species in reaction"):
            i += 1
        if i >= len(lines):
            break
        num_species = int(lines[i].split()[0])
        i += 1
        species = []
        while len(species) < num_species * 2 and i < len(lines):
            parts = lines[i].strip().split()
            for part in parts:
                try:
                    float(part)
                    species.append(part)
                except ValueError:
                    species.append(part)
            i += 1
        species_list = [species[i + 1] for i in range(0, len(species), 2)]

        # Get log10(k)
        logk = []
        count = 0
        while count < 8 and i < len(lines):
            parts = lines[i].strip().split()
            try:
                values = [float(x) for x in parts]
                logk.extend(values)
                count += len(values)
            except ValueError:
                break
            i += 1

        if len(logk) == 8:
            reactions.append({
                'title': title,
                'species': species_list,
                'log10_k': logk
            })
    return reactions


def match_all_reactions(pool: List[str], reactions: List[Dict]) -> List[Dict]:
    pool_set = set([s.replace(" ", "") for s in pool])
    matched = []
    for r in reactions:
        reaction_set = set([s.replace(" ", "") for s in r['species']])
        if reaction_set.issubset(pool_set):
            matched.append(r)
    return matched


def arrhenius_fit(T, log10_k):
    log10_k_arr = np.array(log10_k)
    log10_k_arr = np.clip(log10_k_arr, -100, 100)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        k = np.power(10.0, log10_k_arr)
    ln_k = np.log(k)
    inv_T = 1 / T
    slope, intercept = np.polyfit(inv_T, ln_k, 1)
    R = 8.314
    Ea = -slope * R
    A = np.exp(intercept)
    return A, Ea, k


def compute_reverse_k(k_forward, delta_logK):
    logK = np.clip(np.array(delta_logK), -100, 100)  # 限制防止 overflow
    K_eq = np.power(10.0, logK)
    return k_forward / K_eq


def plot_dense_results(T_dense, kf_dense, kr_dense, A, Ea, title):
    plt.figure(figsize=(9, 6))
    plt.plot(T_dense, kf_dense, '-', label='Forward k(T)')
    plt.plot(T_dense, kr_dense, '--', label='Reverse k_r(T)')
    plt.xlabel('Temperature (K)')
    plt.ylabel('Rate Constant k (mol$^{-1}$·L·s$^{-1}$)')
    plt.yscale('log')
    plt.title(f'Densely Interpolated Reaction: {title}')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    print(f"\n[ {title} - Dense Output ]")
    print("Temperature (K) | k(T) Forward | k_r(T) Reverse")
    print("----------------|----------------|----------------")
    for T_val, k1, k2 in zip(T_dense, kf_dense, kr_dense):
        print(f"{T_val:15.2f} | {k1: .3e}   | {k2: .3e}")


# ---------- 主程序 ----------
file_path = "reaction data/aqueous.txt"
reactions = extract_reaction_blocks(file_path)
matched_list = match_all_reactions(user_reactant_pool, reactions)

if matched_list:
    for match in matched_list:
        A, Ea, k_vals_raw = arrhenius_fit(T_kelvin_raw, match['log10_k'])
        k_rev_raw = compute_reverse_k(k_vals_raw, match['log10_k'])

        # 使用拟合的 A 与 Ea 计算密集温度点上的 kf 和 kr
        kf_dense = A * np.exp(-Ea / (8.314 * T_kelvin_dense))
        logK_clip = np.clip(np.array(match['log10_k']), -100, 100)
        Keq_dense = np.mean(np.power(10.0, logK_clip))
        kr_dense = kf_dense / Keq_dense

        plot_dense_results(T_kelvin_dense, kf_dense, kr_dense, A, Ea, match['title'])
else:
    print("未找到与所提供反应物匹配的反应。请检查拼写和格式。")
