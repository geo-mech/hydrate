"""
无头模式（headless）工具：检查命令行参数或配置，确定是否在无 GUI 环境中运行。

典型用法：
    from zmlx.system import is_headless
    gui.execute(main, disable_gui=is_headless(), close_after_done=False)

注意：gui.execute() 内部会自动调用 is_headless()，通常不需要手动传递。
"""
import sys

from zmlx.system._app_data import app_data


def is_headless() -> bool:
    """检查是否处于无头模式，检测顺序：命令行参数 → app_data → 环境变量。"""
    # 1. 命令行参数 --no-gui 或 --headless
    if '--no-gui' in sys.argv or '--headless' in sys.argv:
        return True
    # 2. app_data 中的 headless 键
    v = app_data.get('headless', None)
    if v is not None:
        return bool(v)
    # 3. 环境变量 headless
    v = app_data.getenv(key='headless', default='', ignore_empty=True)
    if v == 'Yes':
        return True
    if v == 'No':
        return False
    # 4. 默认：非无头模式
    return False
