import warnings
from typing import List

import matplotlib.pyplot as plt
import numpy as np

# 单一反应检索脚本

# ---------- 用户输入部分 ----------
user_reactants = ["Mg++", "HCO3-", "H+", "Cl-"]  # 示例反应物列表

# ---------- 温度定义 ----------
T_celsius = np.array([0, 25, 60, 100, 150, 200, 250, 300])
T_kelvin = T_celsius + 273.15


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
                    float(part)  # 检查是否为数字
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
                break  # 非数字行跳过
            i += 1

        if len(logk) == 8:
            reactions.append({
                'title': title,
                'species': species_list,
                'log10_k': logk
            })
    return reactions


def match_reaction(user_species: List[str], reactions):
    user_set = set([s.replace(" ", "") for s in user_species])
    for r in reactions:
        reaction_set = set([s.replace(" ", "") for s in r['species']])
        if user_set == reaction_set:
            return r
    return None


def arrhenius_fit(T, log10_k):
    log10_k_arr = np.array(log10_k)
    # 限制极端值，防止 overflow
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


def plot_results(T, k, A, Ea, title):
    T_fit = np.linspace(min(T), max(T), 300)
    k_fit = A * np.exp(-Ea / (8.314 * T_fit))

    plt.figure(figsize=(8, 5))
    plt.plot(T, k, 'o', label='Data')
    plt.plot(T_fit, k_fit, '-', label=f'Arrhenius Fit\nA={A:.2e}, Ea={Ea / 1000:.2f} kJ/mol')
    plt.xlabel('Temperature (K)')
    plt.ylabel('k (mol$^{-1}$·L·s$^{-1}$)')
    plt.yscale('log')
    plt.title(f'Reaction: {title}')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 表格输出
    print("\nTemperature (K) | k (mol⁻¹·L·s⁻¹)")
    print("----------------|----------------------")
    for T_val, k_val in zip(T, k):
        print(f"{T_val:15.2f} | {k_val: .3e}")


# ---------- 主程序 ----------
file_path = "reaction data/aqueous.txt"
reactions = extract_reaction_blocks(file_path)
matched = match_reaction(user_reactants, reactions)

if matched:
    A, Ea, k_vals = arrhenius_fit(T_kelvin, matched['log10_k'])
    plot_results(T_kelvin, k_vals, A, Ea, matched['title'])
else:
    print("未找到匹配的反应。请确认输入的反应物拼写和格式是否正确。")
