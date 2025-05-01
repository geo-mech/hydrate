# ** desc = '砂浓度计算(正在测试，尚未完成)'

from zmlx import *


def create():
    mesh = create_cube(x=np.linspace(0, 50, 100),
                       y=np.linspace(0, 50, 100),
                       z=[0, 1])

    # 所有的流体的定义
    fludefs = [Seepage.FluDef.create(defs=[
        Seepage.FluDef(den=1000, vis=0.001, specific_heat=1000, name='h2o'),
        Seepage.FluDef(den=1000, vis=0.001, specific_heat=1000,
                       name='flu_sand')],
        name='flu'),
        Seepage.FluDef(den=1000, vis=1e30, specific_heat=1000,
                       name='sol_sand')
    ]

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(0)

    def get_fai(x, y, z):
        if abs(x - x_max) < 0.1 or abs(y - y_max) < 0.1:
            return 1e10
        if abs(x - x_min) < 0.1 and abs(y - y_min) < 0.1:
            return 1e10
        else:
            return 0.2

    def get_p(x, y, z):
        if abs(x - x_min) < 0.1 and abs(y - y_min) < 0.1:
            return 3e6
        else:
            return 1e6

    def get_k(x, y, z):
        return 1e-14

    def get_s(x, y, z):
        return {'h2o': 0.9, 'sol_sand': 0.1}

    model = seepage.create(mesh=mesh, dv_relative=0.2,
                           fludefs=fludefs,
                           porosity=get_fai, pore_modulus=200e6,
                           p=get_p, s=get_s, perm=get_k,
                           has_solid=True)

    seepage.set_solve(model,
                      show_cells={'dim0': 0, 'dim1': 1, 'show_t': False},
                      time_max=3600 * 24 * 365 * 30
                      )

    # 添加压力梯度到饱和度的映射.
    x = [0, 0.01e6, 0.03e6, 0.1e6]
    y0 = [0, 0.0, 0.0, 0.1]
    y1 = [0, 0.0001, 0.001, 0.2]

    model.set_curve(index=0, curve=Interp1(x=x, y=y0))
    model.set_curve(index=1, curve=Interp1(x=x, y=y1))

    idx = model.reg_cell_key('i0')
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        x, y, z = cell.pos
        if abs(x - x_min) > 0.1 or abs(y - y_min) > 0.1:
            cell.set_attr(index=idx, value=0)

    idx = model.reg_cell_key('i1')
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        x, y, z = cell.pos
        if abs(x - x_min) > 0.1 or abs(y - y_min) > 0.1:
            cell.set_attr(index=idx, value=1)

    sand_config.add_setting(model,
                            sol_sand='sol_sand', flu_sand='flu_sand',
                            ca_i0='i0', ca_i1='i1')

    return model


def show_gradient(model: Seepage):
    x = as_numpy(model).cells.x
    y = as_numpy(model).cells.y
    v = sand_config.get_gradient(model, fluid=[0])
    tricontourf(x, y, v, caption='gradient')


def update_sand(*args, **kwargs):
    print('my update sand')
    sand_config.iterate(*args, **kwargs)


def test_1():
    model = create()

    def extra_plot():
        show_gradient(model)

    seepage.solve(model, close_after_done=False,
                  extra_plot=extra_plot,
                  slots={'update_sand': update_sand}
                  )


if __name__ == '__main__':
    test_1()
