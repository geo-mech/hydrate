# 1D benchmark field of heat conduction
"""
by 徐涛、张召彬
"""

from scipy.special import erf

from zmlx import *


class CellAttrs:
    temperature = 0
    mc = 1


class FaceAttrs:
    g_heat = 0


def create():
    """
    创建模型
    """
    model = Seepage()
    mesh = create_cube(
        x=np.linspace(0, 100, 501),
        y=(-0.5, 0.5),
        z=(-0.5, 0.5)
    )
    x0, x1 = mesh.get_pos_range(0)

    for c in mesh.cells:
        cell = model.add_cell()
        cell.pos = c.pos
        x = c.pos[0]
        # T0 = 273.15 T1 = 373.15
        cell.set_attr(CellAttrs.temperature,
                      373.15 if abs(x - x0) < 1e-3 else 273.15)
        # 设置比热容 和 密度
        cell.set_attr(CellAttrs.mc, 1.0e20 * c.vol if abs(
            x - x0) < 1e-3 else 2640 * 754.4 * c.vol)

    for f in mesh.faces:
        # 高温高压测试结果 热导率为1.69 W/(K·m)
        face = model.add_face(model.get_cell(f.link[0]),
                              model.get_cell(f.link[1]))
        face.set_attr(FaceAttrs.g_heat, f.area * 1.69 / f.length)

    return model


def get_theory(time):
    """
    返回给定时刻的理论解.
    """
    x = np.linspace(0, 100, 101)
    T0 = 273.15
    T1 = 273.15 + 100
    k = 1.69
    rho = 2640
    c = 754.4
    alpha = k / (rho * c)
    T = T1 + (T0 - T1) * erf(x / (2 * np.sqrt(alpha * time)))
    return x, T


def show(model, time):
    import matplotlib.pyplot as plt
    def on_figure(fig):
        if hasattr(fig, 'my_ax'):
            ax = fig.my_ax
            fig.my_idx += 1
        else:
            ax = add_axes2(fig)
            fig.my_ax = ax
            fig.my_idx = 0
            ax.set_xlabel('x (m)')
            ax.set_ylabel('temperature (K)')

        c = plt.cm.tab20.colors[fig.my_idx]
        x1 = seepage.get_x(model)
        t1 = seepage.get_ca(model, CellAttrs.temperature)
        ax.plot(x1[::20], t1[::20], 'o', c=c)
        x2, t2 = get_theory(time)
        ax.plot(x2, t2, c=c, label=f'{time / 3600 / 24:.0f} d')
        ax.legend(frameon=False)

    plot(on_figure, caption='temperature', clear=False)


def solve(model):
    dt = 200000
    for step in range(5000):
        gui.break_point()
        model.iterate_thermal(
            dt=dt, ca_t=CellAttrs.temperature,
            ca_mc=CellAttrs.mc,
            fa_g=FaceAttrs.g_heat)
        if step % 500 == 0 and step != 0:
            show(model, time=dt * step)
            print(f'step = {step}')


def execute():
    """
    执行建模的求解的全过程
    """
    model = create()
    gui.execute(solve, close_after_done=False, args=[model, ])


if __name__ == '__main__':
    execute()
