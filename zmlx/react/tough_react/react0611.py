from typing import List, Dict

import numpy as np

from zmlx.base.zml import Seepage
from zmlx.react import alg

# ---------- 全局常量 ----------
R = 8.314  # 气体常数 J/mol/K


# ---------- 提取反应条目 ----------
def extract_reaction(filepath: str, target_species: List[str]) -> Dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        title = lines[i].strip()
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
        species_list = [species[j + 1] for j in range(0, len(species), 2)]
        stoichs = [float(species[j]) for j in range(0, len(species), 2)]

        # 获取 log10(k)
        logk = []
        count = 0
        while count < 8 and i < len(lines):
            try:
                values = [float(x) for x in lines[i].strip().split()]
                logk.extend(values)
                count += len(values)
            except ValueError:
                break
            i += 1

        match_set = set(s.replace(" ", "") for s in species_list)
        if match_set == set(s.replace(" ", "") for s in target_species):
            return {
                'title': title,
                'species': species_list,
                'stoichs': stoichs,
                'log10_k': logk
            }
    return {}


# ---------- 拟合 K(T) 与反应速率 ----------
def fit_kinetics(T_dense, log10_k):
    # 原始 8 个温度节点
    T_raw = np.array([273.15, 298.15, 333.15, 373.15, 423.15, 473.15, 523.15, 573.15])
    log10_k = np.clip(np.array(log10_k), -100, 100)
    K_raw = np.power(10.0, log10_k)
    lnK = np.log(K_raw)
    coeff = np.polyfit(1 / T_raw, lnK, 1)
    a, b = coeff
    K_dense = np.exp(a * (1 / T_dense) + b)

    # 任意示例 Arrhenius 参数拟合
    A_f = 1e6
    Ea_f = 5e4
    k_f = A_f * np.exp(-Ea_f / (R * T_dense))
    k_r = k_f / K_dense
    return K_dense, k_f, k_r, A_f, Ea_f


# ---------- 从数据库获取摩尔质量 ----------
def load_mol_weights(filepath="reaction data/thermo_data.tdat") -> Dict[str, float]:
    weights = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == '':
            i += 1
            continue
        name = line.split()[0]
        while i < len(lines) and 'mole wt.=' not in lines[i]:
            i += 1
        if i < len(lines):
            try:
                parts = lines[i].split("mole wt.=")[-1].split()
                weight = float(parts[0])
                weights[name] = weight
            except:
                pass
        i += 1
    return weights


# ---------- 构建组件 ----------
def build_components(species: List[str], stoichs: List[float]) -> List[Dict]:
    mol_weights = load_mol_weights("reaction data/thermo_data.tdat")
    weights = [abs(n) * mol_weights.get(sp, 18.0) for sp, n in zip(species, stoichs)]
    total_react = sum(w for w, n in zip(weights, stoichs) if n < 0)
    total_prod = sum(w for w, n in zip(weights, stoichs) if n > 0)
    components = []
    for sp, n, w in zip(species, stoichs, weights):
        entry = {
            'kind': sp,
            'weight': -w / total_react if n < 0 else w / total_prod,
            'fa_t': 0,
            'fa_c': 0
        }
        components.append(entry)
    return components


# ---------- 构建反应 ----------
def build_reaction():
    T_dense = np.linspace(273.15, 523.15, 100)
    rxn = extract_reaction("reaction data/aqueous.txt", ["Ca++", "HCO3-", "H+"])
    if not rxn:
        raise ValueError("未找到指定反应")

    K, kf, kr, A, Ea = fit_kinetics(T_dense, rxn['log10_k'])
    components = build_components(rxn['species'], rxn['stoichs'])

    model = Seepage()
    reaction = alg.create_reaction(
        model,
        name="CaCO3_dissolution",
        temp=298.15,
        heat=2.73e5,
        p2t=([0, 100e6], [0, 0]),
        t2q=(T_dense.tolist(), kf.tolist()),
        t2qr=(T_dense.tolist(), kr.tolist()),
        components=components
    )
    model.add_reaction(reaction)
    print(f"反应 {reaction.name} 已加入模型")


# ---------- 执行 ----------
if __name__ == '__main__':
    build_reaction()
