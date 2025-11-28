# ** desc = '两相流，流体注入驱替'


from zmlx import *


def create():
    """
    创建一个模型，并且这里具有一定的随机性；
    """
    import random
    mesh = create_cube(
        np.linspace(0, 100 * random.uniform(0.8, 1.2), 50),
        np.linspace(0, 100 * random.uniform(0.8, 1.2), 50), (-0.5, 0.5))

    # 获得Mesh的坐标范围
    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    # 固定边界位置的压力
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x0) < 0.1 or abs(x - x1) < 0.1 or abs(y - y0) < 0.1 or abs(
                y - y1) < 0.1:
            cell.vol = 1.0e8

    model = seepage.create(
        mesh, porosity=0.2, pore_modulus=100e6,
        p=1e6, temperature=280,
        s=(1, 0), perm=1e-14,
        disable_update_den=True,
        disable_update_vis=True,
        disable_ther=True,
        disable_heat_exchange=True,
        fludefs=[
            Seepage.FluDef(den=50, vis=1.0e-4 * random.uniform(0.5, 1.5),
                           name='flu0'),
            Seepage.FluDef(den=1000, vis=1.0e-3 * random.uniform(0.5, 1.5),
                           name='flu1')]  # 粘性有一定随机性
    )

    cell = model.get_nearest_cell(
        (40 * random.uniform(0.8, 1.2), 40 * random.uniform(0.8, 1.2), 0))
    model.add_injector(fluid_id=1, flu=cell.get_fluid(1),
                       pos=cell.pos,
                       radi=0.1, opers=[(0, 1.0e-5)])
    seepage.set_dt_max(model, 3600 * 24)

    # 返回最终的模型
    return model


def show_model(model: Seepage):
    from zmlx.plt.on_axes import add_axes2, tricontourf
    if not gui:
        return

    x = seepage.get_cell_pos(model, dim=0)
    y = seepage.get_cell_pos(model, dim=1)
    p = seepage.get_cell_pre(model)
    s = seepage.get_cell_fv(model, fid=1) / seepage.get_cell_fv(model)

    def on_figure(figure):
        figure.suptitle(
            f'Model when time = {seepage.get_time(model, as_str=True)}')
        opts = dict(
            ncols=2, nrows=1, xlabel='x', ylabel='y', aspect='equal'
        )
        add_axes2(figure, tricontourf, x, y, p, title='Pressure',
                  cbar=dict(label='Pressure'),
                  index=1, **opts
                  )
        add_axes2(figure, tricontourf, x, y, s, title='Saturation',
                  cbar=dict(label='Saturation'),
                  index=2, **opts
                  )

    plot(on_figure, caption=f'Seepage({model.handle})', clear=True)


def main():
    from zmlx.demo.opath import opath
    model = create()
    seepage.solve(
        model, folder=opath('liq_inj'),
        close_after_done=False,
        time_max=3600 * 24 * 365,  # 求解终止时的时间
        extra_plot=lambda: show_model(model),
    )


if __name__ == '__main__':
    main()
