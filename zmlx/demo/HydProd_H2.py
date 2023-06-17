from zmlx import *


config = create_hydconfig()
config.dt_min = 1
config.dt_max = 24 * 3600
config.dv_relative = 0.1


def create():
    mesh = SeepageMesh.create_cube(np.linspace(-50, 50, 100),
                                   np.linspace(-50, 50, 100), (-1, 1))

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)

    def boundary(x, y, z):
        return abs(x - x_min) < 1e-3 or abs(x - x_max) < 1e-3 or abs(y - y_min) < 1e-3 or abs(y - y_max) < 1e-3

    center = mesh.get_nearest_cell(pos=[0, 0, 0]).pos

    def is_prod(x, y, z):
        return get_distance([x, y, z], center) < 0.01

    def get_s(*args):
        if is_prod(*args):
            return [(0, ), (1, ), (0, )]
        else:
            return [(0, ), (0.6, ), (0.4, )]

    model = config.create(mesh=mesh,
                          porosity=lambda *args: 1e6 if boundary(*args) or is_prod(*args) else 0.3,
                          pore_modulus=100e6,
                          denc=lambda *args: 1e20 if boundary(*args) else 5e6,
                          temperature=285.0,
                          p=lambda *args: 3e6 if is_prod(*args) else 10e6,
                          s=get_s,
                          perm=1e-14, heat_cond=1.0
                          )
    return model


def show(model):
    kwargs = {'gui_only': True, 'title': f'plot when model.time={time2str(config.get_time(model))}'}
    x = model.numpy.cells.x
    y = model.numpy.cells.y
    tricontourf(x, y, model.numpy.cells.get(-12), caption='压力', **kwargs)
    tricontourf(x, y, model.numpy.cells.get(config.cell_keys['temperature']), caption='温度', **kwargs)
    fv = model.numpy.cells.fluid_vol
    tricontourf(x, y, model.numpy.fluids(0).vol / fv, caption='气饱和度', **kwargs)
    tricontourf(x, y, model.numpy.fluids(1).vol / fv, caption='水饱和度', **kwargs)
    tricontourf(x, y, model.numpy.fluids(2).vol / fv, caption='水合物饱和度', **kwargs)


def solve(model):
    iterate = GuiIterator(config.iterate, plot=lambda: show(model))
    while config.get_time(model) < 1 * 365 * 24 * 3600:
        r = iterate(model)
        step = config.get_step(model)
        if step % 10 == 0:
            dt = time2str(config.get_dt(model))
            t = time2str(config.get_time(model))
            print(f'step = {step}, dt = {dt}, time = {t}, report={r}')


if __name__ == '__main__':
    gui.execute(lambda: solve(create()), close_after_done=False)

