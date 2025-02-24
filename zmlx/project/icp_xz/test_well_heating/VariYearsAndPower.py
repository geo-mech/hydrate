import os
import sys

import numpy as np

from icp_xz.well_heating import *
from zmlx.alg.sbatch import sbatch


def run_case(years_heating):
    if years_heating > 0:
        folder = os.path.join(os.getcwd(), 'VariYearsAndPower', f'{years_heating}')
        well_heating(folder=folder, years_heating=years_heating, power=1.0e4 / years_heating)


def main(argv):
    if len(argv) == 1:
        for years_heating in np.linspace(1.0, 15.0, 15):
            print(f'years_heating = {years_heating}')
            sbatch(argv[0], years_heating, c=4, t=1)

    if len(argv) == 2:
        run_case(float(argv[1]))


if __name__ == '__main__':
    main(sys.argv)
