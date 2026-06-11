import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._config import DEFAULT_STATE
from zmlx.scen.mineralization_reactor._mineralization import Co2StorageMineral

# 测试：手动设置水、CO2(aq)、Ca+2 的质量，单位均为 kg。
r = Co2StorageMineral()
s = dict(DEFAULT_STATE, H2O=2.0, **{'CO2(aq)': 2.0e-3, 'Ca+2': 2.5e-4})

# 计算一个很短时间步，确认 Reaktoro 能接受这些 kg 状态并返回新状态。
n = r.calc_next_state(s, 60.0, 298.15, 1.0e7)
assert n['reaktoro_succeeded'] == 1.0
assert n['H2O'] == 2.0
assert n['Ca+2'] >= 0.0
print('test_set_composition passed')
