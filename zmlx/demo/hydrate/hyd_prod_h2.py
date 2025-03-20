# ** desc = '水平方向二维的水合物开发过程'

import numpy as np

from zmlx.config import seepage, hydrate
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

    def is_prod(x, y, z):
        return point_distance([x, y, z], center) < 0.1

    def get_s(*args):
        if is_prod(*args):
            return {'h2o': 1}
        else:
            return {'h2o': 1, 'ch4_hydrate': 0.4}

    kw = hydrate.create_kwargs(gravity=[0, 0, -10], mesh=mesh,
                               porosity=lambda *args: 1e6 if boundary(*args) or is_prod(*args) else 0.3,
                               pore_modulus=100e6,
                               denc=lambda *args: 1e20 if boundary(*args) else 5e6,
                               temperature=285.0,
                               p=lambda *args: 3e6 if is_prod(*args) else 10e6,
                               s=get_s,
                               perm=1e-14, heat_cond=1.0,
                               dt_min=1, dt_max=24 * 3600, dv_relative=0.1)

    model = seepage.create(**kw)
    # 用于solve的选项
    model.set_text(key='solve',
                   text={'show_cells': {'dim0': 0, 'dim1': 1}}
                   )
    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)
