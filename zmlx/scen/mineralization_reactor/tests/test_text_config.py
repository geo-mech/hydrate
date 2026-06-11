import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._mineralization import Mineralization, Co2StorageMineral

# 测试：用文本配置创建玄武岩矿化反应器，并检查关键参数是否生效。
r = Mineralization.from_text('scene=basalt;sa=0.002')
assert isinstance(r, Co2StorageMineral)
assert r.scene == 'basalt'

# 反应器应声明自己需要的流体/组分名称，供 Seepage 按名字映射。
assert 'co2_aq' in r.list_fluid_names()
print('test_text_config passed')
