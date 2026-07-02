# -*- coding: utf-8 -*-

import os
import csv
import numpy as np
import matplotlib.pyplot as plt

import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.exsolve.fluid import create
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.ui import gui

from zmlx.tfc._base import as_numpy, get_time, get_step
from zmlx.tfc._step import add_setting as add_step_setting


"""
水平一注一采溶解气体被动运移模型：修正版

本代码用于当前阶段：
1. 不考虑脱溶；
2. 不考虑 Reaktoro；
3. 不使用亨利定律；
4. He_sol、n2_sol、ch4_sol 作为水相被动组分；
5. 注入井注入纯水；
6. 真实储层初始含有溶解气体；
7. 生产井虚拟网格不赋予初始气体；
8. 用真实储层质量减少量反算累计产出；
9. 用生产井虚拟网格气体质量增加量等效生产井连接面净产出；
10. 输出 CSV 和产出曲线。

重要说明：
前一版中 faces.get_dv(index=0) 没有正确读到生产井连接面气体通量，
导致 prod_face_adv_cum_kg 近似为 0，质量守恒误差图实际变成了 -recovery_ratio。
本修正版不再依赖该 face_dv 结果，而是采用生产井虚拟网格气体质量变化进行闭合检查。
"""


# ============================================================
# 1. 全局参数
# ============================================================

P_INIT = 20.0e6          # 储层初始压力，Pa
P_PROD = 19.8e6          # 生产井虚拟网格初始压力，Pa

T_RES = 400.0            # 储层初始温度，K
T_INJ = 300.0            # 注入水温度，K

PERM_VALUE = 5.0e-13     # 渗透率，m2
POROSITY = 0.3

Q_IN = 1.3e-4            # 注入流量，m3/s

# 运行时间。当前先给 10 年；如果要跑 25 年，改成 25.0 即可。
TIME_MAX = 10.0 * 365.0 * 24.0 * 3600.0

OUTPUT_DIR = "gas_mass_balance_output_corrected"


# ============================================================
# 2. 溶解气体初始含量
# ============================================================

# 注意：
# 这里只是被动运移测试值，不代表真实地层数据。
HE_INIT = 1.0e-6
N2_INIT = 8.0e-4
CH4_INIT = 1.0e-4

GAS_NAMES = ["he_sol", "n2_sol", "ch4_sol"]

GAS_LABELS = {
    "he_sol": "He(aq)",
    "n2_sol": "N2(aq)",
    "ch4_sol": "CH4(aq)",
}


# ============================================================
# 3. 创建模型
# ============================================================

def create_model():

    mesh = create_xy(
        x_min=0.0, dx=40.0, x_max=1000.0,
        y_min=0.0, dy=40.0, y_max=1000.0,
        z_min=-0.5, z_max=0.5,
    )

    y_min, y_max = get_pos_range(mesh, 1)
    y_mid = (y_min + y_max) / 2.0

    # --------------------------------------------------------
    # 生产井虚拟网格：外置到 z > 2
    # --------------------------------------------------------
    add_cell_face(
        mesh,
        pos=[700.0, y_mid, 0.0],
        offset=[0.0, 0.0, 10.0],
        vol=1.0e8,
        area=2.104,
        length=1.0
    )

    # --------------------------------------------------------
    # 注入井虚拟网格：外置到 z < -2
    # --------------------------------------------------------
    add_cell_face(
        mesh,
        pos=[300.0, y_mid, 0.0],
        offset=[0.0, 0.0, -10.0],
        vol=100.0,
        area=2.104,
        length=1.0
    )

    def get_perm(x, y, z):
        return PERM_VALUE

    def get_s(x, y, z):

        # 注入井虚拟网格：纯水
        if z < -2.0:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0
            )

        # 生产井虚拟网格：纯水，不给初始气体
        if z > 2.0:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0
            )

        # 真实储层：初始含有溶解气体
        return dict(
            h2o=1.0 - HE_INIT - N2_INIT - CH4_INIT,
            he_sol=HE_INIT,
            n2_sol=N2_INIT,
            ch4_sol=CH4_INIT
        )

    def get_denc(x, y, z):
        return 2.0e6

    def get_porosity(x, y, z):
        return POROSITY

    def get_p(x, y, z):
        if z > 2.0:
            return P_PROD
        return P_INIT

    def get_t(x, y, z):
        if z < -2.0:
            return T_INJ
        return T_RES

    my_injectors = [
        {
            "pos": [300.0, y_mid, -10.0],
            "fluid_id": "h2o",
            "value": Q_IN,
        }
    ]

    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100.0e6,
        p=get_p,
        temperature=get_t,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=2.56,
        dist=0.8,
        dt_max=3600.0 * 24.0,
        gravity=[0.0, 0.0, 0.0],
        injectors=my_injectors
    )

    return model


# ============================================================
# 4. 气体质量守恒与产出监测器：修正版
# ============================================================

class GasMassBalanceMonitor:

    def __init__(
            self,
            out_dir=OUTPUT_DIR,
            gas_names=None,
            reservoir_z_range=(-2.0, 2.0),
            write_every_steps=50,
            min_rate_dt_s=3600.0,
            rate_plot_tmin_year=0.02
    ):
        self.out_dir = os.path.abspath(out_dir)
        os.makedirs(self.out_dir, exist_ok=True)

        self.gas_names = list(gas_names if gas_names is not None else GAS_NAMES)
        self.reservoir_z_range = reservoir_z_range
        self.write_every_steps = int(write_every_steps)

        # 小于这个时间步的速率不作为有效产出速率，避免初始极小 dt 造成尖峰
        self.min_rate_dt_s = float(min_rate_dt_s)
        self.rate_plot_tmin_year = float(rate_plot_tmin_year)

        self.initialized = False

        self.prod_faces = []
        self.inj_faces = []

        self.m0_res = {g: 0.0 for g in self.gas_names}
        self.m0_inj = {g: 0.0 for g in self.gas_names}
        self.m0_prod = {g: 0.0 for g in self.gas_names}
        self.m0_total = {g: 0.0 for g in self.gas_names}

        self.prev_inj = {g: 0.0 for g in self.gas_names}
        self.prev_prod = {g: 0.0 for g in self.gas_names}

        # 用虚拟井网格储量变化等效连接面累计净流入
        self.cum_res_to_prod_storage = {g: 0.0 for g in self.gas_names}
        self.cum_prod_to_res_storage = {g: 0.0 for g in self.gas_names}

        self.cum_res_to_inj_storage = {g: 0.0 for g in self.gas_names}
        self.cum_inj_to_res_storage = {g: 0.0 for g in self.gas_names}

        self.last_prod_balance = {g: 0.0 for g in self.gas_names}
        self.last_time = None

        self.rows = []

    # --------------------------------------------------------
    # 区域判断
    # --------------------------------------------------------
    def _region_by_z(self, z):
        z0, z1 = self.reservoir_z_range

        if z < z0:
            return "inj"

        if z > z1:
            return "prod"

        return "res"

    def _get_masks(self, model):
        ca = as_numpy(model).cells
        z = ca.z

        z0, z1 = self.reservoir_z_range

        mask_res = (z >= z0) & (z <= z1)
        mask_inj = z < z0
        mask_prod = z > z1

        return mask_res, mask_inj, mask_prod

    # --------------------------------------------------------
    # 气体质量读取
    # --------------------------------------------------------
    def _gas_mass_array(self, model, gas_name):
        return as_numpy(model).fluids(gas_name).mass

    def _region_gas_mass(self, model, gas_name, mask):
        m = self._gas_mass_array(model, gas_name)
        return float(np.sum(m[mask]))

    def _all_region_masses(self, model):
        mask_res, mask_inj, mask_prod = self._get_masks(model)

        data = {}

        for g in self.gas_names:
            data[g] = dict(
                res=self._region_gas_mass(model, g, mask_res),
                inj=self._region_gas_mass(model, g, mask_inj),
                prod=self._region_gas_mass(model, g, mask_prod)
            )

        return data

    # --------------------------------------------------------
    # 识别生产井和注入井连接面，仅用于检查模型拓扑
    # --------------------------------------------------------
    def _find_special_faces(self, model):
        prod_faces = []
        inj_faces = []

        for face in model.faces:
            c0 = face.get_cell(0)
            c1 = face.get_cell(1)

            r0 = self._region_by_z(c0.pos[2])
            r1 = self._region_by_z(c1.pos[2])

            pair = {r0, r1}

            if pair == {"res", "prod"}:
                prod_faces.append(face.index)

            if pair == {"res", "inj"}:
                inj_faces.append(face.index)

        self.prod_faces = prod_faces
        self.inj_faces = inj_faces

        print("\n========== 气体质量守恒监测初始化 ==========")
        print(f"生产井连接面数量 = {len(self.prod_faces)}")
        print(f"注入井连接面数量 = {len(self.inj_faces)}")
        print(f"输出文件夹 = {self.out_dir}")
        print("说明：真实储层为 -2 <= z <= 2；生产井虚拟网格为 z > 2；注入井虚拟网格为 z < -2。")
        print("修正：不再用 faces.get_dv(index=0) 作为主守恒依据。")
        print("修正：用生产井虚拟网格气体质量增加量等效生产井连接面净产出。")
        print("==========================================\n")

    # --------------------------------------------------------
    # 初始化
    # --------------------------------------------------------
    def initialize(self, model):
        if self.initialized:
            return

        self._find_special_faces(model)

        masses = self._all_region_masses(model)

        for g in self.gas_names:
            self.m0_res[g] = masses[g]["res"]
            self.m0_inj[g] = masses[g]["inj"]
            self.m0_prod[g] = masses[g]["prod"]
            self.m0_total[g] = masses[g]["res"] + masses[g]["inj"] + masses[g]["prod"]

            self.prev_inj[g] = masses[g]["inj"]
            self.prev_prod[g] = masses[g]["prod"]

        self.initialized = True
        self.last_time = None

        self._record_row(model, masses)
        self.write_csv()

    # --------------------------------------------------------
    # 用虚拟井网格质量变化等效连接面累计产出
    # --------------------------------------------------------
    def _accumulate_virtual_storage_flux(self, masses):
        """
        对当前模型来说：
        生产井虚拟网格初始无气体，且无其他气体源汇。
        因此，生产井虚拟网格中气体质量的增加量，
        就等效于从储层进入生产井连接面的气体净产出量。

        这比直接读取 faces.get_dv(index=0) 更稳定。
        """

        for g in self.gas_names:

            # 生产井虚拟网格气体质量变化
            m_prod = masses[g]["prod"]
            dm_prod = m_prod - self.prev_prod[g]

            if dm_prod >= 0.0:
                self.cum_res_to_prod_storage[g] += dm_prod
            else:
                self.cum_prod_to_res_storage[g] += -dm_prod

            self.prev_prod[g] = m_prod

            # 注入井虚拟网格气体质量变化
            # 正常情况下应该始终接近 0
            m_inj = masses[g]["inj"]
            dm_inj = m_inj - self.prev_inj[g]

            if dm_inj >= 0.0:
                self.cum_res_to_inj_storage[g] += dm_inj
            else:
                self.cum_inj_to_res_storage[g] += -dm_inj

            self.prev_inj[g] = m_inj

    # --------------------------------------------------------
    # 每一步调用
    # --------------------------------------------------------
    def step(self, model):
        if not self.initialized:
            self.initialize(model)

        masses = self._all_region_masses(model)

        self._accumulate_virtual_storage_flux(masses)

        self._record_row(model, masses)

        step = int(get_step(model))

        if step % self.write_every_steps == 0:
            self.write_csv()

    # --------------------------------------------------------
    # 记录一行
    # --------------------------------------------------------
    def _record_row(self, model, masses):
        t = float(get_time(model))
        step = int(get_step(model))

        row = {
            "step": step,
            "time_s": t,
            "time_day": t / 86400.0,
            "time_year": t / (365.0 * 86400.0),
        }

        if self.last_time is None:
            dt = None
        else:
            dt = max(t - self.last_time, 0.0)

        row["dt_s"] = 0.0 if dt is None else dt

        for g in self.gas_names:
            prefix = g.replace("_sol", "")

            m_res = masses[g]["res"]
            m_inj = masses[g]["inj"]
            m_prod = masses[g]["prod"]

            m0_res = self.m0_res[g]
            m0_inj = self.m0_inj[g]
            m0_prod = self.m0_prod[g]
            m0_total = self.m0_total[g]

            total_mass = m_res + m_inj + m_prod

            # 真实储层损失量
            res_loss = m0_res - m_res

            # 注入井侧气体净增加量
            # 正常应接近 0。
            inj_storage_net = m_inj - m0_inj

            # 生产井虚拟网格气体净增加量
            prod_storage_net = m_prod - m0_prod

            # 推荐的累计产出量：
            # 从真实储层减少量中扣除进入注入井侧的异常气体量。
            prod_balance = res_loss - inj_storage_net

            # 全模型质量守恒误差
            total_balance_error = total_mass - m0_total

            if abs(m0_total) > 0.0:
                total_balance_error_rel = total_balance_error / m0_total
            else:
                total_balance_error_rel = 0.0

            # 产出闭合误差：
            # 储层反算产出量 与 生产井虚拟网格累计量 是否一致。
            prod_closure_error = prod_balance - prod_storage_net

            if abs(m0_res) > 0.0:
                prod_closure_error_rel = prod_closure_error / m0_res
                recovery_ratio = prod_balance / m0_res
                prod_storage_recovery_ratio = prod_storage_net / m0_res
            else:
                prod_closure_error_rel = 0.0
                recovery_ratio = 0.0
                prod_storage_recovery_ratio = 0.0

            # 产出速率
            if dt is not None and dt >= self.min_rate_dt_s:
                prod_rate = (prod_balance - self.last_prod_balance[g]) / dt
            else:
                prod_rate = 0.0

            row[f"{prefix}_m0_res_kg"] = m0_res
            row[f"{prefix}_m0_inj_kg"] = m0_inj
            row[f"{prefix}_m0_prod_kg"] = m0_prod
            row[f"{prefix}_m0_total_kg"] = m0_total

            row[f"{prefix}_res_remaining_kg"] = m_res
            row[f"{prefix}_inj_virtual_kg"] = m_inj
            row[f"{prefix}_prod_virtual_kg"] = m_prod
            row[f"{prefix}_total_mass_kg"] = total_mass

            row[f"{prefix}_res_loss_cum_kg"] = res_loss

            # 生产井虚拟网格质量变化等效连接面累计产出
            row[f"{prefix}_prod_storage_net_cum_kg"] = prod_storage_net
            row[f"{prefix}_prod_storage_pos_cum_kg"] = self.cum_res_to_prod_storage[g]
            row[f"{prefix}_prod_storage_reverse_cum_kg"] = self.cum_prod_to_res_storage[g]

            # 注入井侧异常监测
            row[f"{prefix}_inj_storage_net_cum_kg"] = inj_storage_net
            row[f"{prefix}_inj_storage_pos_cum_kg"] = self.cum_res_to_inj_storage[g]
            row[f"{prefix}_inj_storage_reverse_cum_kg"] = self.cum_inj_to_res_storage[g]

            # 储层质量减少量反算的累计产出
            row[f"{prefix}_prod_balance_cum_kg"] = prod_balance
            row[f"{prefix}_prod_balance_rate_kg_s"] = prod_rate

            row[f"{prefix}_recovery_ratio"] = recovery_ratio
            row[f"{prefix}_prod_storage_recovery_ratio"] = prod_storage_recovery_ratio

            # 两类误差
            row[f"{prefix}_total_mass_balance_error_kg"] = total_balance_error
            row[f"{prefix}_total_mass_balance_error_rel"] = total_balance_error_rel

            row[f"{prefix}_prod_closure_error_kg"] = prod_closure_error
            row[f"{prefix}_prod_closure_error_rel"] = prod_closure_error_rel

            self.last_prod_balance[g] = prod_balance

        self.last_time = t

        if len(self.rows) == 0:
            self.rows.append(row)
        else:
            if self.rows[-1]["step"] != row["step"]:
                self.rows.append(row)
            else:
                self.rows[-1] = row

    # --------------------------------------------------------
    # 输出 CSV
    # --------------------------------------------------------
    def write_csv(self):
        if len(self.rows) == 0:
            return

        path = os.path.join(self.out_dir, "gas_mass_balance_and_production_corrected.csv")

        fieldnames = list(self.rows[0].keys())

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in self.rows:
                writer.writerow(row)

    # --------------------------------------------------------
    # 绘图工具
    # --------------------------------------------------------
    def _get_col(self, name):
        return np.array([float(r.get(name, 0.0)) for r in self.rows], dtype=float)

    def plot_all(self):
        if len(self.rows) < 2:
            return

        self._plot_cumulative_production()
        self._plot_cumulative_production_storage()
        self._plot_production_rate()
        self._plot_recovery_ratio()
        self._plot_total_mass_balance_error()
        self._plot_production_closure_error()

    # --------------------------------------------------------
    # 累计产出：储层质量减少量反算
    # --------------------------------------------------------
    def _plot_cumulative_production(self):
        t_year = self._get_col("time_year")

        plt.figure(figsize=(8, 5))

        for g in self.gas_names:
            prefix = g.replace("_sol", "")
            y = self._get_col(f"{prefix}_prod_balance_cum_kg")
            plt.plot(t_year, y, label=f"{GAS_LABELS[g]} balance")

        plt.xlabel("Time / year")
        plt.ylabel("Cumulative produced gas mass / kg")
        plt.title("Cumulative produced dissolved gas based on reservoir balance")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        path = os.path.join(self.out_dir, "gas_cumulative_production_balance_corrected.png")
        plt.savefig(path, dpi=300)
        plt.close()

    # --------------------------------------------------------
    # 累计产出：生产井虚拟网格质量增加量
    # --------------------------------------------------------
    def _plot_cumulative_production_storage(self):
        t_year = self._get_col("time_year")

        plt.figure(figsize=(8, 5))

        for g in self.gas_names:
            prefix = g.replace("_sol", "")
            y = self._get_col(f"{prefix}_prod_storage_net_cum_kg")
            plt.plot(t_year, y, label=f"{GAS_LABELS[g]} prod virtual")

        plt.xlabel("Time / year")
        plt.ylabel("Gas mass in production virtual cell / kg")
        plt.title("Cumulative produced gas based on production virtual storage")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        path = os.path.join(self.out_dir, "gas_cumulative_production_storage_corrected.png")
        plt.savefig(path, dpi=300)
        plt.close()

    # --------------------------------------------------------
    # 产出速率
    # --------------------------------------------------------
    def _plot_production_rate(self):
        t_year = self._get_col("time_year")
        mask = t_year >= self.rate_plot_tmin_year

        if not np.any(mask):
            mask = np.ones_like(t_year, dtype=bool)

        plt.figure(figsize=(8, 5))

        for g in self.gas_names:
            prefix = g.replace("_sol", "")
            y = self._get_col(f"{prefix}_prod_balance_rate_kg_s")
            plt.plot(t_year[mask], y[mask], label=GAS_LABELS[g])

        plt.xlabel("Time / year")
        plt.ylabel("Production rate / kg/s")
        plt.title("Gas production rate after initial transient")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        path = os.path.join(self.out_dir, "gas_production_rate_corrected.png")
        plt.savefig(path, dpi=300)
        plt.close()

    # --------------------------------------------------------
    # 采收率
    # --------------------------------------------------------
    def _plot_recovery_ratio(self):
        t_year = self._get_col("time_year")

        plt.figure(figsize=(8, 5))

        for g in self.gas_names:
            prefix = g.replace("_sol", "")
            y = self._get_col(f"{prefix}_recovery_ratio")
            plt.plot(t_year, y, label=GAS_LABELS[g])

        plt.xlabel("Time / year")
        plt.ylabel("Recovery ratio")
        plt.title("Gas recovery ratio")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        path = os.path.join(self.out_dir, "gas_recovery_ratio_corrected.png")
        plt.savefig(path, dpi=300)
        plt.close()

    # --------------------------------------------------------
    # 全模型质量守恒误差
    # --------------------------------------------------------
    def _plot_total_mass_balance_error(self):
        t_year = self._get_col("time_year")

        plt.figure(figsize=(8, 5))

        for g in self.gas_names:
            prefix = g.replace("_sol", "")
            y = self._get_col(f"{prefix}_total_mass_balance_error_rel")
            plt.plot(t_year, y, label=GAS_LABELS[g])

        plt.xlabel("Time / year")
        plt.ylabel("Relative total mass balance error")
        plt.title("Total gas mass balance error")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        path = os.path.join(self.out_dir, "gas_total_mass_balance_error_rel_corrected.png")
        plt.savefig(path, dpi=300)
        plt.close()

    # --------------------------------------------------------
    # 产出闭合误差：
    # 储层反算产出量 vs 生产井虚拟网格累计量
    # --------------------------------------------------------
    def _plot_production_closure_error(self):
        t_year = self._get_col("time_year")

        plt.figure(figsize=(8, 5))

        for g in self.gas_names:
            prefix = g.replace("_sol", "")
            y = self._get_col(f"{prefix}_prod_closure_error_rel")
            plt.plot(t_year, y, label=GAS_LABELS[g])

        plt.xlabel("Time / year")
        plt.ylabel("Relative production closure error")
        plt.title("Production closure error: balance vs production virtual storage")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        path = os.path.join(self.out_dir, "gas_production_closure_error_rel_corrected.png")
        plt.savefig(path, dpi=300)
        plt.close()

    # --------------------------------------------------------
    # 结束输出
    # --------------------------------------------------------
    def finalize(self):
        self.write_csv()
        self.plot_all()

        print("\n========== 修正后的气体质量守恒与产出曲线输出完成 ==========")
        print(f"CSV 文件：{os.path.join(self.out_dir, 'gas_mass_balance_and_production_corrected.csv')}")
        print(f"累计产出曲线：{os.path.join(self.out_dir, 'gas_cumulative_production_balance_corrected.png')}")
        print(f"生产井虚拟网格累计量曲线：{os.path.join(self.out_dir, 'gas_cumulative_production_storage_corrected.png')}")
        print(f"产出速率曲线：{os.path.join(self.out_dir, 'gas_production_rate_corrected.png')}")
        print(f"采收率曲线：{os.path.join(self.out_dir, 'gas_recovery_ratio_corrected.png')}")
        print(f"全模型质量守恒误差曲线：{os.path.join(self.out_dir, 'gas_total_mass_balance_error_rel_corrected.png')}")
        print(f"产出闭合误差曲线：{os.path.join(self.out_dir, 'gas_production_closure_error_rel_corrected.png')}")
        print("============================================================\n")


# ============================================================
# 5. 主程序
# ============================================================

def main():
    from zmlx.scen.geothermal_helium.exsolve.show3 import show_xy

    model = create_model()

    gas_monitor = GasMassBalanceMonitor(
        out_dir=OUTPUT_DIR,
        gas_names=GAS_NAMES,
        reservoir_z_range=(-2.0, 2.0),
        write_every_steps=50,
        min_rate_dt_s=3600.0,
        rate_plot_tmin_year=0.02
    )

    gas_monitor.initialize(model)

    add_step_setting(
        model,
        start=1,
        step=1,
        stop=999999999,
        name="gas_monitor_step",
        args=["@model"]
    )

    def extra_plot():
        show_xy(model)

    tfc.solve(
        model=model,
        extra_plot=extra_plot,
        slots={
            "gas_monitor_step": gas_monitor.step
        },
        time_max=TIME_MAX,
        state_hint="He-N2-CH4 passive transport with corrected mass balance"
    )

    gas_monitor.finalize()


if __name__ == "__main__":
    gui.execute(main)