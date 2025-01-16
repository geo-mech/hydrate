# ** desc = '两相流，水驱替气体'

import numpy as np

from zml import Seepage
from zmlx.config import seepage
from zmlx.seepage_mesh.cube import create_cube
from zmlx.ui import gui


def create():
    mesh = create_cube(np.linspace(0, 50, 51),
                       np.linspace(0, 50, 51), (-0.5, 0.5))

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x1) < 0.1 or abs(y - y1) < 0.1:
            cell.vol = 1.0e8

    model = seepage.create(mesh, porosity=0.2, pore_modulus=100e6,
                           p=1e6,
                           temperature=280,
                           s=(1, 0),
                           perm=1e-14,
                           disable_update_den=True,
                           disable_update_vis=True,
                           disable_ther=True,
                           disable_heat_exchange=True,
                           fludefs=[Seepage.FluDef(den=50, vis=1.0e-3, name='flu0'),
                                    Seepage.FluDef(den=1000, vis=1.0e-5, name='flu1')]
                           )

    cell = model.get_nearest_cell((x0, y0, 0))
    model.add_injector(fluid_id=1,
                       flu=cell.get_fluid(1),
                       pos=cell.pos,
                       radi=0.1,
                       opers=[(0, 1.0e-5)])

    seepage.set_dt_max(model, 3600 * 24 * 7)

    # 用于求解的选项
    model.set_text(key='solve',
                   text={'show_cells': {'dim0': 0, 'dim1': 1},
                         'time_max': 100 * 24 * 3600,
                         }
                   )

    return model


if __name__ == '__main__':
    gui.execute(lambda: seepage.solve(create()), close_after_done=False)
