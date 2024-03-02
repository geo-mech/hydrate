# ** desc = '水平方向二维的水合物开发过程'

from zmlx import *
from zmlx.config import seepage, hydrate
from zmlx.utility.SeepageNumpy import as_numpy


def create():
    mesh = SeepageMesh.create_cube(x=np.linspace(-50, 50, 100),
                                   y=np.linspace(-50, 50, 100), z=(-1, 1))

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)

    def boundary(x, y, z):
        return abs(x - x_min) < 1e-3 or abs(x - x_max) < 1e-3 or abs(y - y_min) < 1e-3 or abs(y - y_max) < 1e-3

    center = mesh.get_nearest_cell(pos=[0, 0, 0]).pos

    def is_prod(x, y, z):
        return get_distance([x, y, z], center) < 0.01

    def get_s(*args):
        if is_prod(*args):
            return [(0,), (1,), (0,)]
        else:
            return [(0,), (0.6,), (0.4,)]

    kw = hydrate.create_kwargs(gravity=[0, 0, -10])
    kw.update(create_dict(mesh=mesh,
                          porosity=lambda *args: 1e6 if boundary(*args) or is_prod(*args) else 0.3,
                          pore_modulus=100e6,
                          denc=lambda *args: 1e20 if boundary(*args) else 5e6,
                          temperature=285.0,
                          p=lambda *args: 3e6 if is_prod(*args) else 10e6,
                          s=get_s,
                          perm=1e-14, heat_cond=1.0, dt_min=1, dt_max=24 * 3600, dv_relative=0.1))

    return seepage.create(**kw)


def show(model):
    if gui.exists():
        kwargs = {'title': f'plot when time={seepage.get_time(model, as_str=True)}'}
        numpy = as_numpy(model)
        x = numpy.cells.x
        y = numpy.cells.y
        tricontourf(x, y, numpy.cells.pre, caption='压力', **kwargs)
        tricontourf(x, y, numpy.cells.get(model.get_cell_key('temperature')), caption='温度', **kwargs)
        fv = numpy.cells.fluid_vol
        tricontourf(x, y, numpy.fluids(0).vol / fv, caption='气饱和度', **kwargs)
        tricontourf(x, y, numpy.fluids(1).vol / fv, caption='水饱和度', **kwargs)
        tricontourf(x, y, numpy.fluids(2).vol / fv, caption='水合物饱和度', **kwargs)


def solve(model):
    iterate = GuiIterator(seepage.iterate, plot=lambda: show(model))
    solver = ConjugateGradientSolver(tolerance=1.0e-20)

    while seepage.get_time(model) < 1 * 365 * 24 * 3600:
        r = iterate(model, solver=solver)
        step = seepage.get_step(model)
        if step % 10 == 0:
            print(f'step = {step}, dt = {seepage.get_dt(model, as_str=True)}, '
                  f'time = {seepage.get_time(model, as_str=True)}, report={r}')


if __name__ == '__main__':
    gui.execute(lambda: solve(create()), close_after_done=False)
