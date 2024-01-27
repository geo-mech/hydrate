import sys

import numpy as np

from zmlx.alg.sbatch import sbatch
from zmlx.config.japan13 import h2o_inj
from zmlx.filesys.opath import opath


def run(qinj, inj_t0):
    h2o_inj(power=0, qinj=qinj,
            rowdist=43.3,  # 43.3 注井间距为50m
            inj_t0=inj_t0,
            guimode=False,
            folder=opath('230411 qinj#_tinj#', '%0.5e %0.5e' % (qinj, inj_t0)),
            )


if __name__ == '__main__':
    if len(sys.argv) == 1:
        for qinj in np.linspace(0, 600, 8):
            for inj_t0 in np.linspace(273.15 + 10, 273.15 + 25, 8):
                print(qinj, inj_t0)
                sbatch(sys.argv[0], qinj, inj_t0, sbatchc=4, sbatcht=None)

    if len(sys.argv) == 3:
        run(float(sys.argv[1]), float(sys.argv[2]))
