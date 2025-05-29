# ** desc = '显示1维的，根据达西定量所计算出来的压力场'

from zmlx import *


def create():
    mesh = create_cube(
        x=np.linspace(-25, 25, 50),
        y=[-0.5, 0.5],
        z=[-0.5, 0.5])
    x_min, x_max = mesh.get_pos_range(0)

    def get_fai(x, y, z):
        return 1.0e10 if abs(x - x_max) < 0.1 or abs(x - x_min) < 0.1 else 0.2

    def get_p(x, y, z):
        return 3e6 if x < 0 else 1e6

    model = seepage.create(
        mesh=mesh,
        dv_relative=0.2,
        fludefs=[h2o.create(name='h2o',
                            density=1000.0,
                            viscosity=1.0e-3)],
        porosity=get_fai,
        pore_modulus=200e6,
        p=get_p,
        s=1.0,
        perm=1e-14
    )
    seepage.set_solve(
        model,
        time_max=3600 * 24 * 30
    )
    return model


def show_model(model: Seepage):
    x = as_numpy(model).cells.x
    p = as_numpy(model).cells.pre
    plot_xy(x=x, y=p, xlabel='x', ylabel='p')


def main():
    model = create()
    seepage.solve(model, close_after_done=False,
                  extra_plot=lambda: show_model(model))


if __name__ == '__main__':
    main()
