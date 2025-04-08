# ** desc = '实验室尺度的ch4水合物合成过程模拟 (仅供参考) '

from numpy import linspace

from zmlx.config import seepage, hydrate
from zmlx.seepage_mesh.cylinder import create_cylinder
from zmlx.seepage_mesh.swap import swap_yz


def create():
    """
    创建模型
    """
    mesh = create_cylinder(x=linspace(0, 0.5, 50),
                           r=linspace(0, 0.1, 10))
    swap_yz(mesh)
    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        return abs(z - z_max) < 0.0001

    def get_s(x, y, z):
        return {'h2o': 0.6, 'ch4': 0.4}

    def denc(*pos):
        return 1e20 if is_upper(*pos) else 5e6

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        return 1.0 if abs(y) < 2 else 0.0

    # 关键词
    kw = hydrate.create_kwargs(gravity=[0, 0, 0],
                               dt_min=1.0e-4,
                               dt_max=10,
                               dv_relative=1,
                               mesh=mesh,
                               porosity=0.3,
                               pore_modulus=100e6,
                               denc=denc,
                               temperature=273.15 + 3.0,
                               p=1e6,
                               s=get_s,
                               perm=1.0e-14,
                               dist=0.001,
                               heat_cond=heat_cond,
                               )
    model = seepage.create(**kw,
                           warnings_ignored={'gravity'})

    seepage.add_injector(
        model, data=dict(
            flu='insitu',
            fluid_id='ch4',
            value=1.0e-6,  # m^3/s
            pos=[0, 0, 0],
        ))

    # 用于solve的选项
    model.set_text(key='solve',
                   text={'show_cells': {'dim0': 0,
                                        'dim1': 2
                                        },
                         'time_max': 10 * 3600,
                         }
                   )
    # 返回模型
    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)
