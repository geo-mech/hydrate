# ** desc = '重力驱动下的气水分层'


import numpy as np

from zmlx.config import seepage
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.fluid.h2o import create as create_h2o
from zmlx.seepage_mesh.cube import create_cube


def create():
    mesh = create_cube(x=np.linspace(0, 200, 5),
                       y=(-0.5, 0.5),
                       z=np.linspace(-500, 0, 100)
                       )

    model = seepage.create(mesh, porosity=0.1, pore_modulus=100e6,
                           denc=1.0e6,
                           temperature=280,
                           p=10e6,
                           s={'ch4': 0.5, 'h2o': 0.5},
                           perm=1.0e-15,
                           heat_cond=2.0,
                           fludefs=[create_ch4(name='ch4'),
                                    create_h2o(name='h2o')],
                           dt_max=3600 * 24 * 365,
                           gravity=(0, 0, -10))

    # 用于求解的选项
    model.set_text(key='solve',
                   text={'show_cells': {'dim0': 0, 'dim1': 2},
                         'time_max': 3600 * 24 * 365 * 100,
                         }
                   )

    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)
