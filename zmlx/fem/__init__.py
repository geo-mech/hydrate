"""
基于zmlx.extx.DynSys，实现有限元计算.
"""
from zmlx.exts import SelfPath
from zmlx.fem.dyn import create_dyn  # 创建有限元问题等价的DynSys对象

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
