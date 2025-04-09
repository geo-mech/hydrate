"""
在北龙超算上创建任务。

其它常用的命令:

    显示用户sce4885的磁盘占用以及剩余的容量.
        lfs quota -uh sce4885 ~

"""
import os
import sys

from zmlx.alg.sys import sbatch


def main():
    is_windows = os.name == 'nt'
    if is_windows:
        print('The current system is Windows (do not support)')
    else:
        sbatch(*sys.argv[1:])


if __name__ == '__main__':  # 尝试提交任务.
    main()
