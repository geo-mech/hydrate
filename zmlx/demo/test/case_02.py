# ** desc = '显示静水压力场'

import numpy as np

from zml import Seepage
from zmlx.config import seepage
from zmlx.fluid import h2o
from zmlx.plt.plotxy import plotxy
from zmlx.seepage_mesh.cube import create_cube
from zmlx.utility.SeepageNumpy import as_numpy


def create():
    mesh = create_cube(x=np.linspace(-25, 25, 50),
                       y=[-0.5, 0.5],
                       z=[-0.5, 0.5])

    model = seepage.create(mesh=mesh,
                           dv_relative=0.2,
                           fludefs=[h2o.create(name='h2o',
                                               density=1000.0,
                                               viscosity=1.0e-3)],
                           porosity=0.2,
                           pore_modulus=200e6,
                           p=2e6,
                           s=1.0,
                           perm=1e-14,
                           gravity=[-10, 0, 0],
                           )
    seepage.set_solve(model,
                      time_max=3600 * 24 * 30
                      )
    return model


def show_model(model: Seepage):
    x = as_numpy(model).cells.x
    p = as_numpy(model).cells.pre
    plotxy(x=x, y=p, xlabel='x', ylabel='p')


def main():
    model = create()
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show_model(model))


if __name__ == '__main__':
    main()
