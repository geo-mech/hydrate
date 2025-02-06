# ** desc = '实验室尺度的水合物分解过程模拟 (仅供参考)'
"""
注意，此case拷贝自hyd_prod_v2.py，并在此基础上修改了mesh，并进行了一些微调。
此demo不针对任何的实验，仅仅用以说明实验室尺度水合物分解建模的方法。
计算结果仅供参考。since 2025-2-6

注：
    在case_11的基础上，修改了温度和压力.
"""

from numpy import linspace

from zmlx.config import seepage, hydrate
from zmlx.seepage_mesh.add_cell_face import add_cell_face
from zmlx.seepage_mesh.cylinder import create_cylinder
from zmlx.seepage_mesh.swap import swap_yz


def create():
    """
    创建模型
    """
    mesh = create_cylinder(x=linspace(0, 0.5, 50),
                           r=linspace(0, 0.1, 10))
    swap_yz(mesh)

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh, pos=[0, 0, 0], offset=[0, 10, 0], vol=1000,
                  area=5, length=1)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        return abs(z - z_max) < 0.0001

    def is_prod(x, y, z):
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        if is_prod(x, y, z):
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    def denc(*pos):
        return 1e20 if is_upper(*pos) else 5e6

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        return 1.0 if abs(y) < 2 else 0.0

    # 关键词
    kw = hydrate.create_kwargs(gravity=[0, 0, 0],
                               dt_min=1.0e-4,
                               dt_max=24 * 3600,
                               dv_relative=0.1,
                               mesh=mesh,
                               porosity=0.3,
                               pore_modulus=100e6,
                               denc=denc,
                               temperature=273.15+3.0,
                               p=4e6,
                               s=get_s,
                               perm=1.0e-14,
                               dist=0.001,
                               heat_cond=heat_cond,
                               prods=[{'index': -1,
                                       't': [0, 1e20],
                                       'p': [0.3e6, 0.3e6]}]
                               )
    model = seepage.create(**kw)

    # 用于solve的选项
    model.set_text(key='solve',
                   text={'monitor': {'cell_ids': [model.cell_number - 1]},
                         'show_cells': {'dim0': 0,
                                        'dim1': 2,
                                        'mask': seepage.get_cell_mask(model=model, yr=[-1, 1])},
                         'time_max': 365 * 24 * 3600,
                         }
                   )
    # 返回模型
    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)
