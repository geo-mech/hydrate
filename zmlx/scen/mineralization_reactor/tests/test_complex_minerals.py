import sys
from pathlib import Path
import timeit

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._mineralization import Co2StorageMineral

# 测试：给一个矿物更复杂的初始状态，包含碳酸盐矿物和硅酸盐矿物。
# 相关的数据，初始化

a = timeit.default_timer()
for step in range(1000):
    r = Co2StorageMineral(scene='basalt')
b = timeit.default_timer()
print(f'init time: {b-a:0.6f} s')

t1 = 0
t2 = 0

for step in range(1000):
    print(f'step {step}')
    a = timeit.default_timer()
    s = dict(r._default_state)
    s.update({
        'Calcite': 2.0e-4,
        'Magnesite': 1.0e-4,
        'Dolomite': 1.5e-4,
        'Albite': 5.0e-4,
        'Anorthite': 8.0e-4,
        'Quartz': 3.0e-4,
        'CO2(aq)': 1.5e-3,
        'Ca+2': 8.0e-5,
        'Mg+2': 1.2e-4,
        'SiO2(aq)': 5.0e-5,
        'Al+3': 1.0e-9,
    })
    b = timeit.default_timer()

    # 针对，必要的操作……
    n = r.calc_next_state(s, 300.0, 308.15, 2.0e7)
    c = timeit.default_timer()

    assert n['reaktoro_succeeded'] == 1.0
    assert 'Albite_delta_kg' in n
    assert 'Anorthite_delta_kg' in n
    assert n['Calcite'] >= 0.0

    t1 += (b-a)
    t2 += (c-b)


print(f't1: {t1} s, t2: {t2} s, avg: {t1/1000:0.6f} s, {t2/1000:0.6f} s')
