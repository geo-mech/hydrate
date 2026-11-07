"""统一管理九个碳酸盐岩工况；不导入求解器，绘图也可单独引用。"""

from dataclasses import asdict, dataclass
from pathlib import Path

#: 所有代码、结果和运行临时文件均保留在 geothermal 内。
ROOT = Path(__file__).resolve().parent
GEOTHERMAL = ROOT.parents[1]
#: 与旧圆形改造结果分目录保存，避免混用，也不删除原结果。
RESULTS = ROOT / "results_fractures"
SCHEMA = "carbonate-fractures-v1"
#: 人工设计的裂缝几何，不是现场反演；固定随机种子使各工况可比。
FRACTURE_SEED, FRACTURE_COUNT = 20261106, 12
FRACTURE_VERTICAL_RATIO = 0.45
#: 等效高渗裂缝带宽度，不是力学裂缝开度；改造区内共用0.25m网格。
FRACTURE_BAND_WIDTH_M, GRID_STEP_M, GRID_REFINED_EXTENT_M = 1.0, 1.0, 22.0
#: PPT 的井深、井底温度和地温梯度；z 轴向上。
DEPTH_M, TEMPERATURE_C, GRADIENT_K_M = 4701.7, 155.2, 0.0287
#: 重力与静水压力积分统一为 9.81；大气压为绝对压力起点。
GRAVITY, ATMOSPHERE_PA = 9.81, 101325.0
#: 其余为待现场标定的研究假设，并非苏热1井实测参数。
K0, K_ZONE, LAMBDA0 = 1e-17, 1e-13, 4.0
ROCK_DENSITY, ROCK_CP, POROSITY = 2800.0, 900.0, 0.02
WELL_TEMPERATURE_K, WELL_DIAMETER_M = 280.0, 0.2
DAYS, SAVE_DAYS = 3650, (365, 1825, 3650)
MD_M2 = 9.869233e-16
#: 液态纯水表覆盖局部模型预期的温压范围；不是全水柱积分的范围。
WATER_P_MIN, WATER_P_MAX = 10e6, 80e6
WATER_T_MIN, WATER_T_MAX = 275.0, 450.0


@dataclass(frozen=True)
class Case:
    """裂缝改造参数；radius_m表示裂缝中心线最远延伸距离，而非圆形区。"""

    name: str
    label: str
    radius_m: float
    zone_permeability_m2: float
    zone_conductivity_w_mk: float
    reference: str

    def metadata(self):
        """返回可写入JSON的设计参数字典。

        Returns:
            dict: 当前工况的名称、分区物性及评价参照。
        """
        return asdict(self)


CASES = (
    Case("baseline", "基准", 0.0, K0, LAMBDA0, "baseline"),
    *(Case(f"A{i}", f"A{i}", radius, K_ZONE, LAMBDA0, "baseline")
      for i, radius in enumerate((2.0, 5.0, 10.0, 20.0), 1)),
    *(Case(f"B{i}", f"B{i}", 10.0, K_ZONE, conductivity, "A3")
      for i, conductivity in enumerate((5.0, 6.0, 7.0, 8.0), 1)),
)
BY_NAME = {case.name: case for case in CASES}


def grid_nodes():
    """返回所有工况共用的对称非均匀节点，中央井单元宽0.2m。

    Returns:
        list[float]: [-50,50]m节点，±22m内约0.25m，外部逐步放粗。
    """
    positive = [WELL_DIAMETER_M/2]
    while positive[-1] + GRID_STEP_M < GRID_REFINED_EXTENT_M - 1e-8:
        positive.append(round(positive[-1] + GRID_STEP_M, 8))
    positive += [GRID_REFINED_EXTENT_M, *range(23, 31), *range(32, 51, 2)]
    return [-v for v in reversed(positive)] + positive


def study_settings():
    """返回参与结果一致性检查的公共参数，避免改参数后混用旧结果。

    Returns:
        dict: 公共物性、几何、运行时长和物性表范围。
    """
    names = ("DEPTH_M", "TEMPERATURE_C", "GRADIENT_K_M", "GRAVITY", "ATMOSPHERE_PA",
             "K0", "K_ZONE", "LAMBDA0", "ROCK_DENSITY", "ROCK_CP", "POROSITY",
             "WELL_TEMPERATURE_K", "WELL_DIAMETER_M", "DAYS", "WATER_P_MIN",
             "WATER_P_MAX", "WATER_T_MIN", "WATER_T_MAX", "FRACTURE_SEED", "FRACTURE_COUNT",
             "FRACTURE_VERTICAL_RATIO", "FRACTURE_BAND_WIDTH_M", "GRID_STEP_M", "GRID_REFINED_EXTENT_M")
    return dict({name: globals()[name] for name in names}, grid_nodes_m=grid_nodes(),
                save_days=list(SAVE_DAYS))
