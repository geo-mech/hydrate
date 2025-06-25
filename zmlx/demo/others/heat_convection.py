# ** desc = '单相流，初始有密度的差异，在重力的驱动下自然对流的过程'

from zmlx import *


def is_region1(x, y, z):
    return point_distance([x, z], [-0.1, 0.5]) < 0.2


def is_region2(x, y, z):
    return point_distance([x, z], [0.1, -0.5]) < 0.2


def create():
    mesh = create_cube(
        x=linspace(-0.6, 0.6, 60), y=[-0.5, 0.5], z=linspace(-1, 1, 100)
    )

    def get_denc(x, y, z):
        return 1.0e20 if is_region1(x, y, z) or is_region2(x, y, z) else 1.0e6

    def get_temp(x, y, z):
        if is_region1(x, y, z):
            return 280
        if is_region2(x, y, z):
            return 320
        else:
            return 300

    def dist(x, y, z):
        return 1.0 

    model = seepage.create(
        mesh=mesh, dv_relative=0.5,
        fludefs=[h2o.create(t_min=272.0, t_max=340.0, p_min=1e6, p_max=40e6,
                            name='h2o')],
        porosity=0.2,
        p=5e6, s=1.0,
        perm=1e-12,
        temperature=get_temp, denc=get_denc,
        gravity=[0, 0, -10],
        dist=dist,
    )

    model.add_tag('disable_ther')

    key = model.reg_flu_key('z0')
    for cell in model.cells:
        cell.get_fluid(0).set_attr(key, cell.z)

    return model


def show(model):
    title = f'Time = {seepage.get_time(model, as_str=True)}'
    x = as_numpy(model).cells.x
    z = as_numpy(model).cells.z
    density = as_numpy(model).fluids(0).den
    tricontourf(x, z, density, caption='密度', title=title)

    temperature = as_numpy(model).fluids(0).get_attr(model.get_flu_key('temperature'))
    tricontourf(x, z, temperature, caption='流体温度', title=title)

    y0 = as_numpy(model).fluids(0).get_attr(model.get_flu_key('z0'))
    tricontourf(x, z, y0, caption='流体Z0', title=title)


def main():
    model = create()
    seepage.solve(model, close_after_done=False, time_max=3600 * 24 * 500,
                  extra_plot=lambda: show(model))


if __name__ == '__main__':
    main()
