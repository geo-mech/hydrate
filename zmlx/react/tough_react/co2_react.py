# co2_react.py  ───────────────────────────────────────────
# --------------------------------------------------------

import numpy as np
import warnings
from typing import List, Dict

from zmlx import *                     # 网格/水合物建模
from zmlx.react import alg             # 反应模块


def create_xz_half(x_max=300.0, depth=300.0, height=100.0,
                   dx=2.0, dz=2.0,
                   hc=150, rc=100,
                   ratio=1.05,
                   dx_max=None, dz_max=None):

    if dx_max is None:
        dx_max = dx * 4.0
    vx = [0, dx]
    while vx[-1] < x_max:
        if vx[-1] > rc:
            dx *= ratio
            dx = min(dx, dx_max)
        vx.append(vx[-1] + dx)

    vy = [-0.5, 0.5]
    vz = [0]

    if height > 0:
        dz_bak = dz
        while vz[-1] < height:
            vz.append(vz[-1] + dz)
            dz *= 1.5
        dz = dz_bak
        vz.reverse()
        vz = [-z for z in vz]

    if dz_max is None:
        dz_max = dz * 4.0
    while vz[-1] < depth:
        if vz[-1] > hc:
            dz *= ratio
            dz = min(dz, dz_max)
        vz.append(vz[-1] + dz)

    vz = [-z for z in vz]
    vz.reverse()
    return create_cube(x=vx, y=vy, z=vz)


def create(mass_rate=50.0 / (3600 * 24), years_inj=20,
           p_seabed=10e6, t_seabed=275.0,
           depth_inj=200.0, x_inj=0.0, y_inj=0.0,
           perm=1.0e-15, free_h=5.0,
           mesh=None, s_ini=None, save_dt_min=None, save_dt_max=None,
           years_max=1e5, co2_temp=290.0, **extra_kwds):

    if mesh is None:
        mesh = create_xz_half(x_max=300)

    def get_t(x, y, z):
        return t_seabed if z >= 0 else t_seabed - 0.0443 * z

    def get_p(x, y, z):
        return p_seabed - 1e4 * z

    if s_ini is None:
        def s_ini(x, y, z):
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        return 1e20 if abs(z - z0) < 0.1 or z >= -1 else 3e6

    def get_porosity(x, y, z):
        return 1e10 if abs(z - z1) < 1 else 0.3

    kw = hydrate.create_kwargs(has_inh=True, has_co2=True,
                               gravity=[0, 0, -10],
                               has_co2_in_liq=True,
                               sol_dt=-0.3,
                               inh_diff=1e6 / 400)
    kw.update(dict(mesh=mesh,
                   porosity=get_porosity,
                   pore_modulus=200e6,
                   denc=get_denc,
                   temperature=get_t,
                   p=get_p,
                   s=s_ini,
                   perm=perm,
                   heat_cond=2.0,
                   dt_max=3600 * 24 * 365 * 10,
                   dv_relative=0.1,
                   gr=create_krf(0.2, 3, as_interp=True,
                                 k_max=1, s_max=1, count=200)))
    kw.update(extra_kwds)

    solve_opt = {'show_cells': {'dim0': 0, 'dim1': 2,
                                'show_s': ['ch4', 'ch4_hydrate', 'co2',
                                           'co2_in_liq', 'co2_hydrate', 'inh'],
                                'use_mass': True},
                 'time_max': years_max * 365 * 24 * 3600,
                 'save_dt_min': save_dt_min or 365 * 24 * 3600,
                 'save_dt_max': save_dt_max or 365 * 24 * 3600 * 1000}

    model = seepage.create(texts={'solve': solve_opt}, **kw)

    # 固定 CO₂ 溶解度
    key_sol = model.get_cell_key('n_co2_sol')
    for c in model.cells:
        c.set_attr(key_sol, 0.06)

    # 禁止海床上方/近海底区域生成水合物
    ca_rate = model.reg_cell_key('hyd_rate')
    for r in model.reactions:
        r.irate = ca_rate
    for c in model.cells:
        if c.z > -free_h:
            c.set_attr(ca_rate, 0)

    # 多相相渗
    vs, kg, kw_rel = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    i_gas = model.find_fludef('gas')[0]
    i_liq = model.find_fludef('liq')[0]
    model.set_kr(i_gas, vs, kg)
    model.set_kr(i_liq, vs, kw_rel)

    # 注入口
    fid = model.find_fludef('co2')
    cell_inj = model.get_nearest_cell([x_inj, y_inj, -depth_inj])
    flu_in = cell_inj.get_fluid(*fid).get_copy()
    flu_in.set_attr(index=model.reg_flu_key('temperature'),
                    value=co2_temp)

    try:            # 曲线注入
        vt, vq = mass_rate
        opers = [[t, str(q / flu_in.den)]
                 for t, q in zip(vt, vq) if t < years_inj * 365 * 24 * 3600]
        opers.append([years_inj * 365 * 24 * 3600, '0'])
    except Exception:
        vol_q = mass_rate / flu_in.den
        opers = [[0, str(vol_q)], [years_inj * 365 * 24 * 3600, '0']]

    model.add_injector(cell=cell_inj, value=0,
                       fluid_id=fid, flu=flu_in, opers=opers)

    return model




R_GAS = 8.314  # J/mol/K


def extract_reaction(filepath: str, target_species: List[str]) -> Dict:
    """从 aqueous.txt 中提取完全匹配 target_species 的反应条目"""
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

        num = int(lines[i].split()[0]); i += 1
        sp, st = [], []
        while len(sp) < num and i < len(lines):
            parts = lines[i].split()
            st.extend([float(parts[k]) for k in range(0, len(parts), 2)])
            sp.extend([parts[k + 1] for k in range(0, len(parts), 2)])
            i += 1

        # log₁₀K 行
        logk = []
        while len(logk) < 8 and i < len(lines):
            try:
                logk.extend([float(x) for x in lines[i].split()])
            except ValueError:
                break
            i += 1

        if set(map(str.strip, sp)) == set(map(str.strip, target_species)):
            return dict(title=title, species=sp, stoichs=st, log10_k=logk)
    return {}


def fit_kinetics(T: np.ndarray, log10_k: List[float]):
    """由 8 个温度节点 log₁₀K 拟合 K(T)，并假设同阶 Arrhenius 给出 k_f"""
    T_raw = np.array([273.15, 298.15, 333.15, 373.15,
                      423.15, 473.15, 523.15, 573.15])
    log10_k = np.clip(np.array(log10_k), -100, 100)
    K_raw = 10 ** log10_k
    a, b = np.polyfit(1 / T_raw, np.log(K_raw), 1)
    K_T = np.exp(a / T + b)             # K(T)

    # 任选常数级前向速率系数 (示例)
    A_f, Ea_f = 1e6, 5e4                # 单位对后续无影响，只用于示范
    k_f = A_f * np.exp(-Ea_f / (R_GAS * T))
    k_r = k_f / K_T
    return K_T, k_f, k_r


def load_mol_weights(path="reaction data/thermo_data.tdat") -> Dict[str, float]:
    wt = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        name = lines[i].split()[0]
        while i < len(lines) and 'mole wt.=' not in lines[i]:
            i += 1
        if i < len(lines):
            try:
                wt[name] = float(lines[i].split('mole wt.=')[-1].split()[0])
            except Exception:
                pass
        i += 1
    return wt


def build_components(species: List[str], stoichs: List[float],
                     thermo_path="reaction data/thermo_data.tdat"):
    wts = load_mol_weights(thermo_path)
    abs_w = [abs(n) * wts.get(sp, 18.0)
             for sp, n in zip(species, stoichs)]
    tot_r = sum(w for w, n in zip(abs_w, stoichs) if n < 0)
    tot_p = sum(w for w, n in zip(abs_w, stoichs) if n > 0)
    comp = []
    for sp, n, w in zip(species, stoichs, abs_w):
        comp.append(dict(kind=sp,
                         weight=(-w / tot_r) if n < 0 else (w / tot_p),
                         fa_t=0, fa_c=0))
    return comp


def add_caco3_reaction(model: seepage.Seepage,
                       aqueous_path="reaction data/aqueous.txt",
                       thermo_path="reaction data/thermo_data.tdat",
                       target_species=("Ca++", "HCO3-", "H+")):
    """在已建模型中嵌入 CaCO₃ 溶解/沉淀反应"""
    rxn = extract_reaction(aqueous_path, list(target_species))
    if not rxn:
        raise RuntimeError("未在数据库中找到指定反应！")

    T_dense = np.linspace(273.15, 523.15, 100)
    _, kf, kr = fit_kinetics(T_dense, rxn['log10_k'])
    comps = build_components(rxn['species'], rxn['stoichs'], thermo_path)

    reaction = alg.create_reaction(
        model,
        name="CaCO3_dissolution_precip",
        temp=298.15,
        heat=2.73e5,          # 示意焓变，可按需修改
        p2t=([0, 100e6], [0, 0]),
        t2q=(T_dense.tolist(), kf.tolist()),
        t2qr=(T_dense.tolist(), kr.tolist()),
        components=comps
    )
    model.add_reaction(reaction)
    print(f"✓ 反应 {reaction.name} 已成功注入模型")
    return reaction



def create_with_reaction(**kwds):
    """外部主接口：返回含 CO₂ 注入+CaCO₃ 反应的模型"""
    mdl = create(**kwds)            # 先建 CO₂-hydrate 模型
    try:
        add_caco3_reaction(mdl)
    except Exception as e:
        warnings.warn(f"CaCO₃ 反应未加入: {e}")
    return mdl




if __name__ == "__main__":
    # ------ 可在此处集中修改模型/反应参数 ------
    model = create_with_reaction(
        mass_rate=50.0 / (3600 * 24),   # kg/s
        years_inj=20,
        depth_inj=200.0,
        perm=1e-15,
    )

    # ------ 开始计算 ------
    seepage.solve(model, close_after_done=False, folder=None)
