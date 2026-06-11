import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._config import scene_state
from zmlx.scen.mineralization_reactor._mineralization import Co2StorageMineral

# 测试：咸水层场景迭代一步后，反应组分应发生变化。
r = Co2StorageMineral(scene='saline_aquifer')
s = scene_state('saline_aquifer')
n = r.calc_next_state(s, 600.0, 298.15, 1.0e7)
assert n['reaktoro_succeeded'] == 1.0

# Ca+2 发生变化，并且输出方解石的质量变化量。
assert abs(n['Ca+2'] - s['Ca+2']) > 1.0e-12
assert 'Calcite_delta_kg' in n
print('test_one_step passed')
