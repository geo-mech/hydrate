"""
在北龙超算上创建任务。

其它常用的命令:

    显示用户sce4885的磁盘占用以及剩余的容量.
        lfs quota -uh sce4885 ~

.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn

warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)

import os
import sys

from zmlx.algs.sys import sbatch


def main():
    """命令行入口：将参数传递给 sbatch 提交任务。"""
    is_windows = os.name == 'nt'
    if is_windows:
        print('The current system is Windows (do not support)')
    else:
        sbatch(*sys.argv[1:])


if __name__ == '__main__':  # 尝试提交任务.
    main()
