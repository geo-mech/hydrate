import numpy as np

from zml import Seepage, Tensor3
from zmlx.alg.clamp import clamp
from zmlx.config import seepage
from zmlx.demo.opath import opath
from zmlx.seepage_mesh.cube import create_cube


def create():
    # 创建规则的Mesh
    mesh = create_cube(x=np.linspace(0, 100, 200),
                       y=(-0.5, 0.5),
                       z=np.linspace(-20, 30, 100))

    # 实际的cell的中心点的坐标的范围
    x0, x1 = mesh.get_pos_range(0)

    # 设置右侧的cell的体积无限大，从而固定流体的压力.
    for cell in mesh.cells:
        if abs(cell.pos[0] - x1) < 0.1:
            cell.vol = 1.0e8  # 固定压力.

    def get_s(x, y, z):  # 初始的饱和度.
        dz = z - max(13 - 0.5 * x, 0.0)
        s1 = clamp(0.5 + dz * 0.05, 0.1, 0.9)
        return {'oil': s1, 'water': 1 - s1}

    # 设置3种流体，均为不可压缩的流体
    fludefs = [Seepage.FluDef(den=1000, vis=1.0, name='oil'),
               Seepage.FluDef(den=1000, vis=1.0e-3, name='water'),
               Seepage.FluDef(den=1000, vis=1.0e-2, name='foam')]

    # 创建模型.
    model = seepage.create(mesh, porosity=0.1, pore_modulus=100e6,
                           p=1e6,
                           temperature=280,
                           s=get_s,
                           perm=Tensor3(xx=5.0e-14,
                                        yy=5.0e-14,
                                        zz=1.0e-14),
                           disable_update_den=True,
                           disable_update_vis=True,
                           disable_ther=True,
                           disable_heat_exchange=True,
                           fludefs=fludefs,
                           gravity=[0, 0, -10],
                           dt_max=3600 * 24,
                           )

    # 添加注入点.
    cell = model.get_nearest_cell([0, 0, 12.5])
    model.add_injector(fluid_id=2, cell=cell, value=1.0e-5,
                       flu=cell.get_fluid(2))

    # 用于求解的选项
    model.set_text(key='solve',
                   text={'show_cells': {'dim0': 0, 'dim1': 2},
                         'time_max': 50 * 24 * 3600,  # 计算的时间长度.
                         }
                   )

    # 返回模型.
    return model


if __name__ == '__main__':
    seepage.solve(create(), folder=opath('foam_inj'), close_after_done=True)
