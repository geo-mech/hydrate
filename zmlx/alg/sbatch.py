import os
import time


def sbatch(script, *args, sbatchc=1, sbatcht=None, sbatchp='G1Part_sce'):
    """
    在超算上面创建一个任务. 其中:
        script  为脚本文件的名称
        sbatchc 为调用的核心的数量
        sbatcht 为休眠的时间
    """
    text = f"""#!/bin/bash
#SBATCH  -n 1
#SBATCH  -c {sbatchc}
srun     -n 1  -c {sbatchc}  python3 {script} """
    for arg in args:
        text = text + f' {arg}'
    fname = None
    for i in range(100000):
        x = f'jb{i}.sh'
        if not os.path.exists(x):
            fname = x
            break
    assert fname is not None
    with open(fname, 'w') as file:
        file.write(text)
        file.write('\n')
        file.flush()
    print(f'file created: {fname}')
    os.system(f"sbatch -p {sbatchp} {fname}")
    if sbatcht is not None:
        time.sleep(sbatcht)
