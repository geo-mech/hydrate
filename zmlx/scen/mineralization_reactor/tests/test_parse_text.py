import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能找到 hydrate 根目录下的 zmlx 包。
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from zmlx.scen.mineralization_reactor._mineralization import parse_text

# 测试：_mineralization.py 中的文本配置解析函数。
assert parse_text('basalt')['scene'] == 'basalt'
assert parse_text('scene=seabed;sa=0.001')['sa'] == '0.001'
assert parse_text('{"model":"co2_storage_mineral","preset":"permafrost"}')['scene'] == 'permafrost'
print('test_parse_text passed')
