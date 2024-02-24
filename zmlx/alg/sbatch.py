import os
import time


def sbatch(*args, c=1, t=None, p='G1Part_sce'):
    """
    在超算上面创建一个任务. 其中:
        args: 跟在python后面的参数.
        c: 调用的核心的数量
        t: 休眠时间(当启动多个的时候，加上休眠，确保多个任务不要同时启动)
    """
    if len(args) == 0:
        return
    text = f"""#!/bin/bash
#SBATCH  -n 1
#SBATCH  -c {c}
srun     -n 1  -c {c}  python3 """
    for arg in args:
        text = text + f' {arg}'
    name = None
    for i in range(100000):
        x = f'jb{i}.sh'
        if not os.path.exists(x):
            name = x
            break
    assert name is not None
    with open(name, 'w') as file:
        file.write(text)
        file.write('\n')
        file.flush()
    os.system(f"sbatch -p {p} {name}")
    print(f'task submitted: {args}')
    if t is not None:
        time.sleep(t)


def main():
    from zml import is_windows
    import sys

    if is_windows:
        print('The current system is Windows (do not support)')
    else:
        sbatch(*sys.argv[1:])


if __name__ == '__main__':  # 尝试提交任务.
    main()
