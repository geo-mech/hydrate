"""不加载数值内核，检查多井建模、能量统计和碳酸盐岩新网格。"""

import ast
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np

GEO = Path(__file__).resolve().parents[2]


def load_functions(path, names, namespace):
    """只读取指定函数定义，不导入求解内核。

    Args:
        path: 源码路径。
        names: 函数名集合。
        namespace: 替代内核及全局变量的命名空间。
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(tree, str(path), "exec"), namespace)


class Cell:
    """用于检查属性赋值的单元替身，不执行数值求解。"""

    def __init__(self, index, pos):
        """创建单元。

        Args:
            index: 编号。
            pos: 中心坐标。
        """
        self.index, self.pos, self.faces, self.attrs = index, pos, [], {}

    def get_attr(self, key):
        """返回属性。

        Args:
            key: 属性名。

        Returns:
            float: 属性值。
        """
        return self.attrs[key]


class Mesh:
    """5×5二维结构替身，不建立实际地热模型。"""

    def __init__(self, **kwargs):
        """建立结构。

        Args:
            kwargs: 接受原建网参数，结构固定为5×5。
        """
        self.cells = [Cell(i*5+j, [float(i-2), 0., float(j-2)]) for i in range(5) for j in range(5)]
        self.faces = []
        for c in self.cells:
            for delta in (1, 5):
                other = c.index+delta
                if other >= 25 or (delta == 1 and c.index//5 != other//5):
                    continue
                pair = (c, self.cells[other])
                face = SimpleNamespace(area=1., get_cell=lambda i, pair=pair: pair[i])
                self.faces.append(face)
                for cell in pair:
                    cell.faces.append(face)

    def get_nearest_cell(self, pos):
        """映射最近中心。

        Args:
            pos: 目标坐标。

        Returns:
            Cell: 最近单元。
        """
        return min(self.cells, key=lambda c: math.dist(c.pos, pos))


def main():
    """执行结构与参数检查，不运行模型或绘图。"""
    paths = [GEO / "_well_cross_section.py", GEO / "_show.py",
             *Path(__file__).parent.glob("*.py"), * (GEO / "cases/carbonate_extent_05m").glob("*.py")]
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def create_stub(**kwargs):
        """只求值初始化回调，不推进任何物理过程。

        Args:
            kwargs: 原create传递的配置。

        Returns:
            SimpleNamespace: 属性容器。
        """
        mesh = kwargs["mesh"]
        texts = {}
        for cell in mesh.cells:
            cell.attrs = dict(temperature=kwargs["temperature"](*cell.pos), mc=kwargs["denc"](*cell.pos))
        return SimpleNamespace(cells=mesh.cells, faces=mesh.faces, time=0.,
                               get_cell=lambda i: mesh.cells[i], get_cell_key=lambda key: key,
                               get_text=lambda key: texts.get(key, ""),
                               set_text=lambda key, text: texts.update({key: text}))

    fake = SimpleNamespace(create=create_stub, get_z=lambda m: [], set_fa=lambda *a: None,
                           set_face=lambda face, **kw: setattr(face, "perm", kw["perm"]),
                           step_iteration=SimpleNamespace(add_setting=lambda *a, **kw: None),
                           set_dt_max=lambda *a: None, get_time=lambda m: m.time)
    ns = dict(math=math, json=json, tfc=fake, Seepage=object, SeepageMesh=Mesh,
              mesh_xz=Mesh, point_distance=math.dist,
              equivalent_area=lambda a, b: (a+b)/2,
              get_average_area=lambda a, la, b, lb: (la+lb)/(la/a+lb/b),
              create_fludefs=lambda: [])
    load_functions(GEO / "_well_cross_section.py",
                   {"create", "get_well_cells", "update_power", "_clamp_heat_cond", "_wrap_heat_cond"}, ns)
    model = ns["create"](well_positions=[(-1, 0), (1, 0)], sealed_well=True, record_step_power=False)
    wells = ns["get_well_cells"](model)
    assert len(wells) == 2
    assert all(c.attrs["temperature"] == 280 and c.attrs["mc"] == 2650*790*1e6 for c in wells)
    assert all(face.perm == 0 for c in wells for face in c.faces)
    assert sum(c.attrs["temperature"] == 280 for c in model.cells) == 2
    ns["update_power"](model)
    for c, rise in zip(wells, (0.001, 0.002)):
        c.attrs["temperature"] += rise
    model.time = 86400.
    ns["update_power"](model)
    p = json.loads(model.get_text("time2pow"))[0][1]
    assert math.isclose(p, 2650*790*1e6*0.003/86400, rel_tol=1e-8)
    for positions in ([], [(0, 0), (0.1, 0)], [(0, 0), (1, 0)], [(99, 0)]):
        try:
            ns["create"](well_positions=positions)
        except ValueError:
            pass
        else:
            raise AssertionError(f"未拒绝无效井位{positions}")
    single = ns["create"]()
    assert len(ns["get_well_cells"](single)) == 1
    captured = {}
    np_proxy = SimpleNamespace(**vars(np))
    np_proxy.savez_compressed = lambda path, **values: captured.update(values)
    model.cell_number = len(model.cells)
    model.faces = []
    model.get_face_key = lambda key: key
    fake.get_x = lambda m, shape: np.array([c.pos[0] for c in m.cells]).reshape(shape)
    fake.get_z = lambda m, shape=None: np.array([c.pos[2] for c in m.cells]).reshape(shape)
    fake.get_ca = lambda m, key, shape: np.full(shape, 320.)
    fake.get_fa = lambda m, index, key, shape: np.full(shape, 300.)
    fake.get_den = lambda m, index, shape: np.full(shape, 990.)
    field_ns = dict(np=np_proxy, tfc=fake)
    load_functions(GEO / "_show.py", {"save_fields"}, field_ns)
    field_ns["save_fields"](None, model, wells[0], 1., 365, jx=5, jz=5, wells=wells)
    assert len(captured["well_indices"]) == 2
    for name in ("fluid_temperature_c", "fluid_density_kg_m3", "fluid_z0_m"):
        assert np.count_nonzero(np.isnan(captured[name])) == 2
    assert np.all(np.isfinite(captured["rock_temperature_c"]))
    # 原位读取旧/新碳酸盐岩配置，不导入zmlx。
    old_path = GEO / "cases/carbonate_enhancement/settings.py"
    spec = importlib.util.spec_from_file_location("_carbonate_original_settings_check", old_path)
    old = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    text = (GEO / "cases/carbonate_extent_05m/settings.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    tree.body = [n for n in tree.body if not (isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("zmlx"))]
    config = {"__file__": str(GEO / "cases/carbonate_extent_05m/settings.py"), "original": old}
    exec(compile(tree, "new_settings", "exec"), config)
    nodes = np.array(config["grid_nodes"]())
    widths = np.diff(nodes)
    assert len(widths) == 173 and np.all(widths > 0)
    assert np.allclose(nodes, -nodes[::-1])
    assert np.isclose(widths[86], 0.2)
    assert np.allclose(widths[(nodes[:-1] >= 0.1) & (nodes[1:] <= 40.6)], 0.5)
    assert [c.radius_m for c in config["CASES"]] == [0, 5, 15, 25, 40]
    assert old.study_settings() != config["study_settings"]()
    print(f"PASS: {len(paths)} files syntax; multiwell assignment/sealing/energy/masking/invalid positions/singlewell; carbonate grid and extents")


if __name__ == "__main__":
    main()
