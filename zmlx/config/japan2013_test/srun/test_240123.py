# ** desc = '此例子说明：如何在北京超算上同时计算多个算例 （仅供示例，勿直接执行）'

import sys

from zmlx.alg.sbatch import sbatch
from zmlx.config.japan13 import h2o_inj
from zmlx.filesys.opath import opath

# 进行因素分析的时候，可变变量的数量，应该等于函数run的参数的数量
n_vari = 1


def run_case(folder):
    """
    内核函数，用于在给定的参数下计算 （运行一个case）
    """
    h2o_inj(root_folder=opath('japan2013', folder))


def main(argv):
    """
    主函数，用来调用计算内核
    """
    if len(argv) == 1:
        sbatch(argv[0], 'base', sbatchc=2, sbatcht=1)

    if len(argv) == n_vari + 1:
        run_case(argv[1])


if __name__ == '__main__':
    main(sys.argv)
