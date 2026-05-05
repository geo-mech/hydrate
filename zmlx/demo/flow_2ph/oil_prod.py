# ** desc = '油水两相的产油产水过程模拟。模拟的是垂直于水平井的一个剖面。'

from zmlx import *


def create_oil(t_min=274, t_max=423, p_min=2.0e6, p_max=99.0e6, name=None):
    """
    创建原油的定义.
    """
    return from_file(
        fname=join_paths(os.path.dirname(__file__), 'oil_data.txt'),
        t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max,
        name=name, specific_heat=2000)


def create(jx=40, jz=20, s=None):
    if s is None:
        s = (0.6, 0.4)

    mesh = create_cube(
        x=np.linspace(0, 20, jx + 1),
        y=[-0.5, 0.5],
        z=np.linspace(-5, 5, jz + 1)
    )

    new_cell = mesh.add_cell(pos=[0, 10, 0], vol=1.0e10)
    cell = mesh.get_nearest_cell(pos=[0, 0, 0])
    mesh.add_face(cell, new_cell, dist=1.0,
                  area=0.1  # 矫正产能
                  )
    x0, x1 = mesh.get_pos_range(0)
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x1) < 0.1:
            cell.vol = 1.0e8  # 右侧恒定压力

    # 定义流体
    fludefs = [
        create_oil(name='oil'),
        Seepage.FluDef(den=1000, vis=1.0e-3, name='water')
    ]

    def get_p(x, y, z):
        if y > 5:
            print("Outlet Pressure:", 2e6)
            return 2e6 - z * 1.0e4
        else:
            return 12e6 - z * 1.0e4

    def get_t(x, y, z):
        if abs(z) < 3 and x < 10:
            return 150 + 273
        else:
            return 60 + 273

    z0, z1 = mesh.get_pos_range(2)

    def denc(x, y, z):
        if abs(z - z0) < 0.01 or abs(z - z1) < 0.01:
            return 50000.0 * 1000.0
        else:
            return 1000.0 * 1000.0

    # 创建模型
    model = seepage.create(
        mesh, porosity=0.2, pore_modulus=100e6,
        p=get_p, temperature=get_t,
        s=s,
        denc=denc,
        perm=Tensor3(xx=2e-14, yy=2e-14, zz=2.0e-15),
        disable_update_den=True,
        fludefs=fludefs,
        gravity=[0, 0, -9.81],
    )
    # 最大时间步长
    seepage.set_dt_max(model, 3600 * 24 * 7)
    return model


def show(model, jx, jz):
    from zmlx.fig import contourf, axes2, plt_show, suptitle, tight_layout, comb, auto_layout

    mask = seepage.get_y(model) < 5

    x = seepage.get_x(model, shape=(jx, jz), mask=mask)
    z = seepage.get_z(model, shape=(jx, jz), mask=mask)
    p = seepage.get_p(model, shape=(jx, jz), mask=mask)
    t = seepage.get_t(model, shape=(jx, jz), mask=mask)
    s = seepage.get_v(model, 0, shape=(jx, jz), mask=mask) / seepage.get_v(model, None, shape=(jx, jz), mask=mask)
    vis = seepage.as_numpy(model).fluids(0).vis[mask].reshape([jx, jz])

    opts = dict(aspect='equal', xlabel='x/m', ylabel='z/m')
    obj = auto_layout(
        axes2(
            contourf(x, z, p, cbar=dict(label='Pressure', shrink=0.7)),
            index=1,
            title='Pressure', **opts
        ),
        axes2(
            contourf(x, z, t, cbar=dict(label='Temperature', shrink=0.7, cmap='coolwarm')),
            index=2,
            title='Temperature', **opts
        ),
        axes2(
            contourf(x, z, s, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm'),
            index=3,
            title='oil saturation', **opts
        ),
        axes2(
            contourf(x, z, np.log10(vis), cbar=dict(label='Viscosity', shrink=0.7), cmap='coolwarm'),
            index=4,
            title='oil viscosity', **opts
        ),
        suptitle(f'时间: {seepage.get_time(model, as_str=True)}'),
        tight_layout(),
        aspect_ratio=1,
    )
    plt_show(obj, caption='模型状态')


def main():
    """
    执行建模并且求解的主函数
    """
    jx, jz = 40 * 2, 20 * 2
    model = create(jx, jz, s=(0.6, 0.4))
    seepage.solve(model, extra_plot=lambda: show(model, jx, jz), time_forward=1000 * 24 * 3600)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
