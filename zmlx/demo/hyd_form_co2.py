# ** desc = '测试：纵向二维。浮力作用下气体运移、水合物成藏过程模拟(co2)'

import numpy as np

from zml import get_distance, create_dict
from zmlx.config import hydrate, seepage
from zmlx.seepage_mesh.cube import create_cube


def create():
    mesh = create_cube(x=np.linspace(0, 200, 100),
                       y=(-0.5, 0.5),
                       z=np.linspace(-300, 0, 150))

    def get_initial_t(x, y, z):
        return 275 - 0.0443 * z

    def get_initial_p(x, y, z):
        return 15e6 - 1e4 * z

    def get_initial_s(x, y, z):
        if get_distance((x, z), (100, -350)) < 80:
            return {'co2': 1}
        else:
            return {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_perm(x, y, z):
        if abs(x - 100) < 20:
            return 1.0e-14
        else:
            return 1.0e-15

    kw = hydrate.create_kwargs(has_inh=True,  # 存在抑制剂
                               gravity=[0, 0, -10],
                               has_co2=True,
                               has_co2_in_liq=True,
                               )
    kw.update(create_dict(mesh=mesh, porosity=0.1, pore_modulus=100e6,
                          denc=get_denc, dist=0.1,
                          temperature=get_initial_t,
                          p=get_initial_p,
                          s=get_initial_s,
                          perm=get_perm, heat_cond=2.0,
                          dt_max=3600 * 24 * 5,  # 允许的最大的时间步长
                          dv_relative=0.1,  # 每一步流体流体的距离与网格大小的比值
                          ))
    model = seepage.create(**kw)

    # 设置co2的溶解度
    key = model.get_cell_key('n_co2_sol')
    for cell in model.cells:
        cell.set_attr(key, 0.06)

    model.set_text(key='solve',
                   text={'show_cells': {'dim0': 0, 'dim1': 2},
                         'step_max': 10000,
                         }
                   )
    # 返回创建的模型.
    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)
