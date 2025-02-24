import os
import sys

import numpy as np

from icp_xz.well_heating import *
from zmlx.alg.sbatch import sbatch


def run_case(perm):
    folder = os.path.join(os.getcwd(), 'VariPerm', f'{perm}')
    well_heating(folder=folder, perm=perm)


def main(argv):
    if len(argv) == 1:
        for k in np.linspace(-1.0, 2.0, 16):
            perm = 10.0 ** k * 1.0e-15
            print(f'k = {k}, perm = {perm}')
            sbatch(argv[0], perm, c=4, t=1)

    if len(argv) == 2:
        run_case(float(argv[1]))


if __name__ == '__main__':
    main(sys.argv)
