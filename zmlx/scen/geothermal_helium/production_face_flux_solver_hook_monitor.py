# -*- coding: utf-8 -*-

"""
生产井连接面通量监测：solver hook 版本

这版代码不再手动推进时间，也不替代 tfc.solve。
它继续使用 tfc.solve(model=...) 作为正式求解器。

修正重点：
1. 不用两次绘图之间的时间间隔计算产水速率。
2. 不手动推进时间。
3. 尝试挂钩底层 FlowSol.iterate / Seepage.iterate。
4. 在真实渗流迭代完成后，立即读取生产井连接面 face.get_dv()。
5. 用真实迭代传入的 dt 计算 q_prod = abs(dv) / dt。

如果 step CSV 没有数据，说明当前 zmlx.solve 内部没有经过这些 Python 层方法。
"""

import os
import csv
import sys
import math

import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium._create import create
from zmlx.seepage_mesh import create_xz, add_cell_face
from zmlx.ui import gui


# ============================================================
# 1. 参数区
# ============================================================

Q_IN = 1.3e-4         # m3/s
Y_WIDTH = 1.0

X_INJ = 300.0
X_PROD = 700.0

P_PROD = 18.0e6       # Pa

INJ_VOL = 100.0
PROD_VOL = 1.0e6

WELL_AREA = 2.104
WELL_LENGTH = 1.0

CSV_STEP_NAME = "production_face_flux_solver_hook_step.csv"
CSV_PLOT_NAME = "production_face_flux_solver_hook_plot.csv"

PRINT_EVERY_N_RECORDS = 50


# ============================================================
# 2. 基础函数
# ============================================================

def setup_console_encoding():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_model_time_safe(model):
    for name in ["time", "t"]:
        try:
            v = getattr(model, name)
            if callable(v):
                v = v()
            return float(v)
        except Exception:
            pass

    try:
        return float(model.get_attr("time"))
    except Exception:
        pass

    return float("nan")


def get_cell_pos(cell):
    if cell is None:
        return None
    try:
        p = cell.pos
        return float(p[0]), float(p[1]), float(p[2])
    except Exception:
        return None


def get_index_safe(obj):
    if obj is None:
        return None
    for name in ["index", "id", "cell_id", "face_id"]:
        try:
            v = getattr(obj, name)
            if callable(v):
                v = v()
            return int(v)
        except Exception:
            pass
    return None


def classify_cell(cell):
    pos = get_cell_pos(cell)
    if pos is None:
        return "unknown"
    y = pos[1]
    if y < -2.0:
        return "inj_virtual"
    if y > 2.0:
        return "prod_virtual"
    return "reservoir"


def try_call(obj, name, *args):
    try:
        f = getattr(obj, name)
    except Exception:
        return None
    try:
        if callable(f):
            return f(*args)
        if len(args) == 0:
            return f
    except Exception:
        return None
    return None


def iter_model_faces(model):
    try:
        for face in model.faces:
            yield face
        return
    except Exception:
        pass

    for n_name in ["face_number", "face_n"]:
        try:
            n = int(getattr(model, n_name))
            for i in range(n):
                yield model.get_face(i)
            return
        except Exception:
            pass


def get_model_cell_by_id(model, cid):
    if cid is None:
        return None
    try:
        return model.get_cell(int(cid))
    except Exception:
        pass
    try:
        return model.cells[int(cid)]
    except Exception:
        pass
    return None


def get_face_cells(face, model):
    c0 = try_call(face, "get_cell", 0)
    c1 = try_call(face, "get_cell", 1)
    if c0 is not None and c1 is not None:
        return c0, c1

    c0 = try_call(face, "cell", 0)
    c1 = try_call(face, "cell", 1)
    if c0 is not None and c1 is not None:
        return c0, c1

    cells = try_call(face, "cells")
    if cells is not None:
        try:
            cells = list(cells)
            if len(cells) >= 2:
                return cells[0], cells[1]
        except Exception:
            pass

    c0 = try_call(face, "cell0")
    c1 = try_call(face, "cell1")
    if c0 is not None and c1 is not None:
        return c0, c1

    c0 = try_call(face, "c0")
    c1 = try_call(face, "c1")
    if c0 is not None and c1 is not None:
        return c0, c1

    for a, b in [
        ("cell_id0", "cell_id1"),
        ("cell0_id", "cell1_id"),
        ("c0_id", "c1_id"),
    ]:
        id0 = try_call(face, a)
        id1 = try_call(face, b)
        if id0 is not None and id1 is not None:
            c0 = get_model_cell_by_id(model, id0)
            c1 = get_model_cell_by_id(model, id1)
            if c0 is not None and c1 is not None:
                return c0, c1

    id0 = try_call(face, "get_cell_id", 0)
    id1 = try_call(face, "get_cell_id", 1)
    if id0 is not None and id1 is not None:
        c0 = get_model_cell_by_id(model, id0)
        c1 = get_model_cell_by_id(model, id1)
        if c0 is not None and c1 is not None:
            return c0, c1

    return None, None


def get_cell_pressure_safe(cell, model=None):
    if cell is None:
        return float("nan")

    for name in ["pre", "pressure", "p"]:
        try:
            v = getattr(cell, name)
            if callable(v):
                v = v()
            return float(v)
        except Exception:
            pass

    if model is not None:
        # 注意：这里不优先使用 reg_cell_key，避免新建无关 key
        for key_name in ["pre", "pressure", "p"]:
            for func_name in ["get_cell_key", "get_key"]:
                try:
                    key = getattr(model, func_name)(key_name)
                    return float(cell.get_attr(key))
                except Exception:
                    pass

    return float("nan")


def get_cell_temperature_safe(cell, model=None):
    if cell is None:
        return float("nan")

    for name in ["temperature", "temp", "T"]:
        try:
            v = getattr(cell, name)
            if callable(v):
                v = v()
            return float(v)
        except Exception:
            pass

    if model is not None:
        for key_name in ["temperature", "temp", "T"]:
            for func_name in ["get_cell_key", "get_key"]:
                try:
                    key = getattr(model, func_name)(key_name)
                    return float(cell.get_attr(key))
                except Exception:
                    pass

    return float("nan")


def find_h2o_ids(model):
    try:
        fid = model.find_fludef(name="h2o")
    except Exception:
        fid = None

    if fid is None:
        return 0, 0

    if isinstance(fid, (list, tuple)):
        return list(fid), int(fid[0])

    return int(fid), int(fid)


def read_face_dv_safe(face, phase_id):
    try:
        return float(face.get_dv(int(phase_id)))
    except Exception:
        pass

    for name in ["dv", "flow", "flux"]:
        try:
            v = getattr(face, name)
            if callable(v):
                v = v(int(phase_id))
            return float(v)
        except Exception:
            pass

    return float("nan")


# ============================================================
# 3. 创建模型
# ============================================================

def create_model():
    mesh = create_xz(
        x_min=0,
        dx=10,
        x_max=1000,
        y_min=-0.5,
        y_max=0.5,
        z_min=-2200.0,
        dz=10,
        z_max=-1800
    )

    z_min, z_max = get_pos_range(mesh, 2)
    z_mid = (z_min + z_max) / 2.0

    add_cell_face(
        mesh,
        pos=[X_PROD, 0.0, z_mid],
        offset=[0, 10, 0],
        vol=PROD_VOL,
        area=WELL_AREA,
        length=WELL_LENGTH
    )

    add_cell_face(
        mesh,
        pos=[X_INJ, 0.0, z_mid],
        offset=[0, -10, 0],
        vol=INJ_VOL,
        area=WELL_AREA,
        length=WELL_LENGTH
    )

    def is_upper(x, y, z):
        return abs(z - z_max) < 100.0

    def is_lower(x, y, z):
        return abs(z - z_min) < 100.0

    def get_perm(x, y, z):
        if is_upper(x, y, z) or is_lower(x, y, z):
            return 1.0e-18
        return 1.0e-12

    def get_porosity(x, y, z):
        return 0.3

    def get_denc(x, y, z):
        if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1:
            return 1.0e20
        return 2.0e6

    def get_s(x, y, z):
        if y < -2.0:
            return dict(h2o=1.0, he_sol=0.0, n2_sol=0.0)
        return dict(h2o=0.999, n2_sol=0.0008, he_sol=0.000001)

    def get_p(x, y, z):
        if y > 2.0:
            return P_PROD
        return -1.0e4 * z

    def get_t(x, y, z):
        if y < -2.0:
            return 313.15
        return 293.15 - 0.035 * z

    my_injectors = [
        {
            "pos": [X_INJ, -10.0, z_mid],
            "fluid_id": "h2o",
            "value": Q_IN,
        }
    ]

    print("")
    print("========== 模型设置 ==========")
    print(f"注入井位置 = [{X_INJ}, -10.0, {z_mid}]")
    print(f"生产井虚拟网格位置 = [{X_PROD}, 10.0, {z_mid}]")
    print(f"注入流量 value = {Q_IN:.6e} m3/s")
    print(f"注入流量 value = {Q_IN * 86400.0:.6e} m3/day")
    print(f"二维单位厚度注入流量 = {Q_IN / Y_WIDTH:.6e} m3/s/m")
    print(f"生产井虚拟网格体积 = {PROD_VOL:.6e} m3")
    print(f"生产井虚拟网格初始压力 = {P_PROD / 1.0e6:.6f} MPa")
    print("==============================")
    print("")

    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100e6,
        p=get_p,
        temperature=get_t,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=2.56,
        dist=0.8,
        dt_max=3600.0 * 24.0 * 100.0,
        gravity=[0, 0, -10],
        injectors=my_injectors
    )

    return model, z_mid


# ============================================================
# 4. 监测器
# ============================================================

class SolverHookFluxMonitor:
    def __init__(self, model, z_mid, h2o_phase_id, csv_step_path, csv_plot_path):
        self.model = model
        self.z_mid = z_mid
        self.h2o_phase_id = h2o_phase_id
        self.csv_step_path = csv_step_path
        self.csv_plot_path = csv_plot_path

        self.record_id = 0
        self.plot_id = 0
        self.last_record_time = None

        self.prod_faces = self.find_production_faces()

        self.init_csv()

        print("")
        print("========== solver hook 生产井通量监测初始化 ==========")
        print(f"h2o phase_id for face.get_dv = {self.h2o_phase_id}")
        print(f"生产井连接面数量 = {len(self.prod_faces)}")
        for item in self.prod_faces:
            print("----------------------------------------")
            print(f"face index = {item['face_index']}")
            print(f"储层侧 cell = {get_index_safe(item['res_cell'])}, pos = {get_cell_pos(item['res_cell'])}")
            print(f"生产井虚拟 cell = {get_index_safe(item['prod_cell'])}, pos = {get_cell_pos(item['prod_cell'])}")
        print(f"逐步 CSV = {self.csv_step_path}")
        print(f"绘图 CSV = {self.csv_plot_path}")
        print("===================================================")
        print("")

    def find_production_faces(self):
        out = []
        for face in iter_model_faces(self.model):
            c0, c1 = get_face_cells(face, self.model)
            if c0 is None or c1 is None:
                continue

            g0 = classify_cell(c0)
            g1 = classify_cell(c1)

            ok = (
                (g0 == "reservoir" and g1 == "prod_virtual")
                or
                (g1 == "reservoir" and g0 == "prod_virtual")
            )
            if not ok:
                continue

            if g0 == "reservoir":
                res_cell = c0
                prod_cell = c1
            else:
                res_cell = c1
                prod_cell = c0

            res_pos = get_cell_pos(res_cell)
            if res_pos is None:
                continue

            score = (res_pos[0] - X_PROD) ** 2 + (res_pos[2] - self.z_mid) ** 2

            out.append({
                "face": face,
                "face_index": get_index_safe(face),
                "res_cell": res_cell,
                "prod_cell": prod_cell,
                "score": score,
            })

        out.sort(key=lambda x: x["score"])
        return out

    def init_csv(self):
        for path in [self.csv_step_path, self.csv_plot_path]:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)

        with open(self.csv_step_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([
                "record_id",
                "source",
                "time_s",
                "time_day",
                "dt_s",

                "sum_raw_dv_m3_per_step",
                "sum_abs_dv_m3_per_step",
                "raw_flux_m3_s",
                "abs_flux_m3_s",

                "q_into_prod_m3_s",
                "q_into_prod_m3_day",
                "q_in_m3_s",
                "q_in_m3_day",
                "prod_to_in_ratio",

                "p_res_MPa",
                "p_prod_MPa",
                "dp_res_minus_prod_MPa",

                "t_res_C",
                "t_prod_C",

                "diagnosis"
            ])

        with open(self.csv_plot_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([
                "plot_id",
                "time_s",
                "time_day",
                "p_res_MPa",
                "p_prod_MPa",
                "dp_res_minus_prod_MPa",
                "t_res_C",
                "t_prod_C",
                "note"
            ])

    def read_snapshot(self):
        raw_dv = 0.0
        abs_dv = 0.0

        p_res = float("nan")
        p_prod = float("nan")
        t_res = float("nan")
        t_prod = float("nan")

        for item in self.prod_faces:
            face = item["face"]
            res_cell = item["res_cell"]
            prod_cell = item["prod_cell"]

            dv = read_face_dv_safe(face, self.h2o_phase_id)
            if not math.isnan(dv):
                raw_dv += dv
                abs_dv += abs(dv)

            p_res_i = get_cell_pressure_safe(res_cell, self.model)
            p_prod_i = get_cell_pressure_safe(prod_cell, self.model)
            t_res_i = get_cell_temperature_safe(res_cell, self.model)
            t_prod_i = get_cell_temperature_safe(prod_cell, self.model)

            if math.isnan(p_res) and not math.isnan(p_res_i):
                p_res = p_res_i
            if math.isnan(p_prod) and not math.isnan(p_prod_i):
                p_prod = p_prod_i
            if math.isnan(t_res) and not math.isnan(t_res_i):
                t_res = t_res_i
            if math.isnan(t_prod) and not math.isnan(t_prod_i):
                t_prod = t_prod_i

        dp = p_res - p_prod if not math.isnan(p_res) and not math.isnan(p_prod) else float("nan")

        return raw_dv, abs_dv, p_res, p_prod, dp, t_res, t_prod

    def record_after_real_iteration(self, dt_s, source):
        if dt_s is None or math.isnan(dt_s) or dt_s <= 0.0:
            return

        t_now = get_model_time_safe(self.model)

        # 避免同一时间重复记录
        if self.last_record_time is not None:
            if not math.isnan(t_now) and abs(t_now - self.last_record_time) < 1.0e-9:
                return

        raw_dv, abs_dv, p_res, p_prod, dp, t_res, t_prod = self.read_snapshot()

        raw_flux = raw_dv / dt_s
        abs_flux = abs_dv / dt_s

        if math.isnan(dp):
            q_into_prod = float("nan")
        elif dp > 0.0:
            q_into_prod = abs_flux
        elif dp < 0.0:
            q_into_prod = -abs_flux
        else:
            q_into_prod = 0.0

        q_day = q_into_prod * 86400.0 if not math.isnan(q_into_prod) else float("nan")
        ratio = q_into_prod / Q_IN if Q_IN > 0 and not math.isnan(q_into_prod) else float("nan")

        p_res_mpa = p_res / 1.0e6 if not math.isnan(p_res) else float("nan")
        p_prod_mpa = p_prod / 1.0e6 if not math.isnan(p_prod) else float("nan")
        dp_mpa = dp / 1.0e6 if not math.isnan(dp) else float("nan")

        t_res_c = t_res - 273.15 if not math.isnan(t_res) else float("nan")
        t_prod_c = t_prod - 273.15 if not math.isnan(t_prod) else float("nan")

        if len(self.prod_faces) == 0:
            diagnosis = "未找到生产井连接面。"
        elif math.isnan(q_into_prod):
            diagnosis = "无法计算生产井通量。"
        elif q_into_prod > 1.0e-20:
            diagnosis = "生产井正在抽水：真实储层流入生产井虚拟网格。"
        elif q_into_prod < -1.0e-20:
            diagnosis = "方向相反：生产井虚拟网格流向真实储层。"
        else:
            diagnosis = "生产井连接面通量接近 0。"

        self.record_id += 1
        self.last_record_time = t_now

        with open(self.csv_step_path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([
                self.record_id,
                source,
                t_now,
                t_now / 86400.0 if not math.isnan(t_now) else float("nan"),
                dt_s,

                raw_dv,
                abs_dv,
                raw_flux,
                abs_flux,

                q_into_prod,
                q_day,
                Q_IN,
                Q_IN * 86400.0,
                ratio,

                p_res_mpa,
                p_prod_mpa,
                dp_mpa,

                t_res_c,
                t_prod_c,

                diagnosis
            ])

        if self.record_id % PRINT_EVERY_N_RECORDS == 0:
            print("")
            print("========== solver hook 生产井通量监测 ==========")
            print(f"record_id = {self.record_id}")
            print(f"source = {source}")
            print(f"time = {t_now:.6e} s = {t_now / 86400.0:.6f} day")
            print(f"dt = {dt_s:.6e} s")
            print("---------------------------------------------")
            print(f"raw dv = {raw_dv:.6e} m3")
            print(f"abs dv = {abs_dv:.6e} m3")
            print(f"q_into_prod = {q_into_prod:.6e} m3/s")
            print(f"q_into_prod = {q_day:.6e} m3/day")
            print(f"Q_IN = {Q_IN:.6e} m3/s")
            print(f"prod_to_in_ratio = {ratio:.6e}")
            print("---------------------------------------------")
            print(f"p_res = {p_res_mpa:.6f} MPa")
            print(f"p_prod = {p_prod_mpa:.6f} MPa")
            print(f"dp = {dp_mpa:.6f} MPa")
            print("---------------------------------------------")
            print(f"t_res = {t_res_c:.6f} C")
            print(f"t_prod = {t_prod_c:.6f} C")
            print("---------------------------------------------")
            print(f"判断：{diagnosis}")
            print("=============================================")
            print("")

    def record_plot_snapshot(self):
        self.plot_id += 1
        t_now = get_model_time_safe(self.model)
        raw_dv, abs_dv, p_res, p_prod, dp, t_res, t_prod = self.read_snapshot()

        p_res_mpa = p_res / 1.0e6 if not math.isnan(p_res) else float("nan")
        p_prod_mpa = p_prod / 1.0e6 if not math.isnan(p_prod) else float("nan")
        dp_mpa = dp / 1.0e6 if not math.isnan(dp) else float("nan")

        t_res_c = t_res - 273.15 if not math.isnan(t_res) else float("nan")
        t_prod_c = t_prod - 273.15 if not math.isnan(t_prod) else float("nan")

        note = "绘图快照，只看压力温度；严格流量请看 solver_hook_step CSV。"

        with open(self.csv_plot_path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([
                self.plot_id,
                t_now,
                t_now / 86400.0 if not math.isnan(t_now) else float("nan"),
                p_res_mpa,
                p_prod_mpa,
                dp_mpa,
                t_res_c,
                t_prod_c,
                note
            ])

        print("")
        print("========== 绘图快照 ==========")
        print(note)
        print(f"plot_id = {self.plot_id}")
        if math.isnan(t_now):
            print("time = nan")
        else:
            print(f"time = {t_now:.6e} s = {t_now / 86400.0:.6f} day")
        print(f"p_res = {p_res_mpa:.6f} MPa")
        print(f"p_prod = {p_prod_mpa:.6f} MPa")
        print(f"dp = {dp_mpa:.6f} MPa")
        print(f"t_res = {t_res_c:.6f} C")
        print(f"t_prod = {t_prod_c:.6f} C")
        print("==============================")
        print("")


# ============================================================
# 5. 安装 hook
# ============================================================

def parse_dt_from_args_kwargs(args, kwargs, dt_position=None):
    if "dt" in kwargs:
        try:
            return float(kwargs["dt"])
        except Exception:
            return None

    if dt_position is not None and len(args) > dt_position:
        try:
            return float(args[dt_position])
        except Exception:
            return None

    return None


def install_hooks(model, monitor):
    installed = []

    # hook 1: FlowSol.iterate(self, model, dt, ...)
    try:
        flow_sol = model.get_flow_sol()
        flow_cls = type(flow_sol)
        original_flow_iterate = flow_cls.iterate

        def hooked_flow_iterate(self, *args, **kwargs):
            dt_s = parse_dt_from_args_kwargs(args, kwargs, dt_position=1)
            result = original_flow_iterate(self, *args, **kwargs)

            target_model = None
            if len(args) >= 1:
                target_model = args[0]
            if target_model is model:
                monitor.record_after_real_iteration(dt_s=dt_s, source="FlowSol.iterate")

            return result

        flow_cls.iterate = hooked_flow_iterate
        installed.append("FlowSol.iterate")
    except Exception as e:
        print("无法安装 FlowSol.iterate hook。")
        print(e)

    # hook 2: Seepage.iterate(self, dt, ...)
    try:
        model_cls = type(model)
        original_model_iterate = model_cls.iterate

        def hooked_model_iterate(self, *args, **kwargs):
            dt_s = parse_dt_from_args_kwargs(args, kwargs, dt_position=0)
            result = original_model_iterate(self, *args, **kwargs)

            if self is model:
                monitor.record_after_real_iteration(dt_s=dt_s, source="Seepage.iterate")

            return result

        model_cls.iterate = hooked_model_iterate
        installed.append("Seepage.iterate")
    except Exception as e:
        print("无法安装 Seepage.iterate hook。")
        print(e)

    print("")
    print("========== hook 安装结果 ==========")
    if installed:
        for name in installed:
            print(f"已安装：{name}")
    else:
        print("没有成功安装任何 hook。")
    print("如果逐步 CSV 没有数据，说明 tfc.solve 没有经过这些 Python 层迭代函数。")
    print("=================================")
    print("")


# ============================================================
# 6. 主程序
# ============================================================

def main():
    setup_console_encoding()

    from zmlx.scen.geothermal_helium._show import show_xz

    model, z_mid = create_model()

    h2o_full_id, h2o_phase_id = find_h2o_ids(model)

    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    csv_step_path = os.path.join(downloads, CSV_STEP_NAME)
    csv_plot_path = os.path.join(downloads, CSV_PLOT_NAME)

    monitor = SolverHookFluxMonitor(
        model=model,
        z_mid=z_mid,
        h2o_phase_id=h2o_phase_id,
        csv_step_path=csv_step_path,
        csv_plot_path=csv_plot_path
    )

    install_hooks(model, monitor)

    monitor.record_plot_snapshot()

    def extra_plot():
        monitor.record_plot_snapshot()
        show_xz(model)

    tfc.solve(
        model=model,
        extra_plot=extra_plot
    )


if __name__ == "__main__":
    gui.execute(main)
