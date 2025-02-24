import os
import sys

import numpy as np

from icp_xz.well_heating import *
from zmlx.alg.sbatch import sbatch


def run_case(power):
    folder = os.path.join(os.getcwd(), 'VariPower', f'{power}')
    well_heating(folder=folder, power=power)


def main(argv):
    if len(argv) == 1:
        for power in np.linspace(0.0, 2e3, 11):
            print(f'power = {power}')
            sbatch(argv[0], power, c=4, t=1)

    if len(argv) == 2:
        run_case(float(argv[1]))


if __name__ == '__main__':
    main(sys.argv)
