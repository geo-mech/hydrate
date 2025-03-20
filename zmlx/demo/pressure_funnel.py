# ** desc = '天然气储层降压开发的时候的压力降低漏斗'

import numpy as np

from zmlx.config import seepage
from zmlx.demo.opath import opath
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.geometry.point_distance import point_distance
from zmlx.seepage_mesh.cube import create_cube


def create():
    mesh = create_cube(x=np.linspace(-50, 50, 100),
                       y=np.linspace(-50, 50, 100), z=(-1, 1))

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)

    def boundary(x, y, z):
        return abs(x - x_min) < 1e-3 or abs(x - x_max) < 1e-3 or abs(y - y_min) < 1e-3 or abs(y - y_max) < 1e-3

    center = mesh.get_nearest_cell(pos=[0, 0, 0]).pos

    def is_prod(*args):
        assert len(args) == 3
        return point_distance(args, center) < 0.1

    def porosity(*args):
        return 1e6 if boundary(*args) or is_prod(*args) else 0.3

    def denc(*args):
        return 1e20 if boundary(*args) else 5e6

    def pressure(*args):
        return 3e6 if is_prod(*args) else 10e6

    # 创建模型
    model = seepage.create(mesh=mesh,
                           fludefs=[create_ch4(name='ch4')],
                           porosity=porosity,
                           pore_modulus=100e6,
                           denc=denc,
                           temperature=285.0,
                           p=pressure,
                           s={'ch4': 1},
                           perm=1e-15,
                           dt_min=1, dt_max=24 * 3600, dv_relative=0.1,
                           )
    # 用于solve的选项
    seepage.set_text(
        model,
        solve=dict(
            show_cells=dict(
                dim0=0, dim1=1, show_t=False, show_s=False
            ),
            time_max=3600 * 24 * 10,
        )
    )
    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False, folder=opath('pressure_funnel'),
                  save_dt=3600, time_unit='d')
