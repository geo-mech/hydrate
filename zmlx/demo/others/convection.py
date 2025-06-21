# ** desc = '单相流，初始有密度的差异，在重力的驱动下自然对流的过程'

from zmlx import *


def create():
    mesh = create_cube(
        x=linspace(-1, 1, 100), y=[-0.5, 0.5], z=linspace(-2, 2, 200)
    )
    model = seepage.create(
        mesh=mesh, dv_relative=0.5,
        fludefs=[Seepage.FluDef(name='h2o')],
        porosity=0.2,
        p=2e6, s=1.0,
        perm=10e-15,
        gravity=[0, 0, -10]
    )
    for cell in model.cells:  # 在z=-1.5的区域设置低密度；在z=1.5的区域设置高密度
        x, _, z = cell.pos
        flu = cell.get_fluid(0)
        if point_distance((x, z), (0, -1.5)) < 0.3:
            flu.mass *= 0.5
            flu.den *= 0.5
        if point_distance((x, z), (0, 1.5)) < 0.3:
            flu.mass *= 1.5
            flu.den *= 1.5
    key = model.reg_flu_key('z0')
    for cell in model.cells:
        cell.get_fluid(0).set_attr(key, cell.z)
    model.add_tag('disable_update_den', 'disable_update_vis', 'disable_ther')
    return model


def show(model):
    title = f'Time = {seepage.get_time(model, as_str=True)}'
    x = as_numpy(model).cells.x
    z = as_numpy(model).cells.z
    density = as_numpy(model).fluids(0).den
    tricontourf(x, z, density, caption='密度', title=title)
    y0 = as_numpy(model).fluids(0).get_attr(model.get_flu_key('z0'))
    tricontourf(x, z, y0, caption='流体Z0', title=title)


def main():
    model = create()
    seepage.solve(model, close_after_done=False, time_max=3600 * 24 * 500,
                  extra_plot=lambda: show(model))


if __name__ == '__main__':
    main()
