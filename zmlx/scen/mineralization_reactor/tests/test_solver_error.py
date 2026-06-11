import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._config import DEFAULT_STATE
from zmlx.scen.mineralization_reactor._mineralization import Co2StorageMineral


# 构造一个故意失败的求解器，用来检查异常分支。
class BrokenSolver:
    def solve(self, chemical, dt):
        raise RuntimeError('test error')


# 测试：求解失败时，不应崩溃，而应返回 reaktoro_succeeded=0。
r = Co2StorageMineral()
r._solver = BrokenSolver()
n = r.calc_next_state(dict(DEFAULT_STATE), 60.0, 298.15, 1.0e7)
assert n['reaktoro_succeeded'] == 0.0
assert 'test error' in n['reaktoro_error']
print('test_solver_error passed')
