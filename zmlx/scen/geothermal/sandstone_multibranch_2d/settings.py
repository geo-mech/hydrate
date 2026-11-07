"""二维平行分支井参数，复用砂岩十年基准的渗透率和热导率。"""

import math
from dataclasses import asdict, dataclass
from pathlib import Path

from zmlx.scen.geothermal.cases.case_sandstone_10years import COND, PERM

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
#: 保存格式标识；二维平行热汇，不代表真实分叉及循环回路。
SCHEMA = "sandstone-parallel-wells-2d-v1"
COUNTS = (1, 2, 3, 4)


@dataclass(frozen=True)
class Parameters:
    """所有分支数共用的砂岩及数值参数，使用SI单位。

    Args:
        days: 完整运行天数，默认3650，按365天折算一年。
        spacing_m: 分支目标中心距，映射网格后的实际位置另存。
        half_width_m: X、Z方向半宽，默认50m。
        grid_count: X、Z网格数，默认101；必须为奇数以包含中心井。
    """

    days: int = 3650
    spacing_m: float = 20.0
    half_width_m: float = 50.0
    grid_count: int = 101
    depth_m: float = 2960.0
    temperature_c: float = 85.8
    gradient_k_m: float = 0.0235
    permeability_m2: float = PERM
    conductivity_w_mk: float = COND
    rock_density_kg_m3: float = 2600.0
    rock_cp_j_kgk: float = 825.0
    porosity: float = 0.22
    well_temperature_k: float = 280.0
    well_diameter_m: float = 0.2
    pressure_center_pa: float = 29e6
    gravity_m_s2: float = 10.0
    dt_max_s: float = 86400.0

    def validate(self):
        """检查物性及离散参数。

        Raises:
            ValueError: 参数非有限、非正、时间不是整数或网格不是奇数。
        """
        for key, value in asdict(self).items():
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"参数{key}必须为有限正数")
        if int(self.days) != self.days or int(self.grid_count) != self.grid_count:
            raise ValueError("days、grid_count必须为整数")
        if self.grid_count < 5 or self.grid_count % 2 != 1 or self.porosity >= 1:
            raise ValueError("网格必须为不少于5的奇数；孔隙度必须小于1")
        # 原砂岩水物性表275～370K；这里不静默拓展其适用范围。
        if not (275 <= self.well_temperature_k <= 370 and
                275 <= 273.15 + self.temperature_c - self.gradient_k_m*self.half_width_m and
                273.15 + self.temperature_c + self.gradient_k_m*self.half_width_m <= 370):
            raise ValueError("地层或井温超出原砂岩水物性表275～370K")

    def positions(self, count):
        """返回同深度、横向居中排列的目标井位。

        Args:
            count: 正整数分支数量。

        Returns:
            list: (x,z)位置，单位m；实际映射网格后的井位在求解前核验。

        Raises:
            ValueError: 井数非法或井位进入最外侧热缓冲列。
        """
        self.validate()
        if isinstance(count, bool) or int(count) != count or count < 1:
            raise ValueError("分支数必须为正整数")
        positions = [((i - (count-1)/2)*self.spacing_m, 0.0) for i in range(count)]
        dx = 2*self.half_width_m/self.grid_count
        if max(abs(x) for x, _ in positions) >= self.half_width_m-dx:
            raise ValueError("井位过近边界，请减小井距或扩大所有对照工况的计算域")
        return positions

    def save_days(self):
        """返回第1、5、10年及终时快照日。

        Returns:
            tuple: 不超过运行时长的完整日数。
        """
        return tuple(sorted({d for d in (365, 1825, 3650, int(self.days)) if d <= self.days}))
