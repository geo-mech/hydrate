import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._mineralization import Mineralization, _positive, _value

# 测试：基类和两个小工具函数的基本行为。
base = Mineralization()
assert base.list_fluid_names() == []
assert base.calc_next_state({'Ca+2': 1.0}, 1.0, 300.0, 1.0e5)['Ca+2'] == 1.0
assert _positive(-1.0) == 0.0
assert _positive('bad', 2.0) == 2.0
assert _value(lambda: 3.0) == 3.0
assert _value(lambda: 1.0 / 0.0, 5.0) == 5.0
print('test_helpers passed')
