import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._mineralization import Mineralization, Co2StorageMineral

# 测试：反应器配置可以 to_text 再 from_text，还原为同类场景。
r0 = Co2StorageMineral(scene='saline_aquifer', surface_area=0.003)
r1 = Mineralization.from_text(r0.to_text())
assert isinstance(r1, Co2StorageMineral)
assert r1.scene == r0.scene
assert abs(r1.surface_area - r0.surface_area) < 1.0e-12
print('test_roundtrip_text passed')
