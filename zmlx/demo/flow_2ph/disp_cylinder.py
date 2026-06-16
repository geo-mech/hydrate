# ** desc = '圆柱中的驱替过程(两相流)'

from zmlx import *


def create(jx: int, jy: int, s=None) -> Seepage:
    """
    创建模型.
    Args:
        jx: 模型的x方向的单元格数量
        jy: 模型的y方向的单元格数量
        s: 初始饱和度. 默认值为(1, 0)

    Returns:
        model: 模型对象
    """
    mesh: SeepageMesh = create_cylinder(
        x=linspace(0, 1.0, jx + 1),
        r=linspace(0, 0.25, jy + 1)
    )

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x1) < 0.0001:
            cell.vol = 1.0e8

    # 定义流体
    fluid_defs = [
        FluDef(den=50, vis=1.0e-2, name='oil'),
        FluDef(den=1000, vis=1.0e-3, name='water')
    ]

    if s is None:
        s = {'water': 0.5, 'oil': 0.5}

    # 创建模型
    model: Seepage = tfc.create(
        mesh, porosity=0.2, pore_modulus=100e6,
        p=1e6, temperature=280,
        s=s,
        perm=1e-14,
        disable_update_den=True,
        disable_update_vis=True,
        disable_ther=True,
        disable_heat_exchange=True,
        fludefs=fluid_defs
    )

    # 找到需要注入的单元
    ca_vol = model.get_cell_key('vol')
    all_vol = 0
    cells_inj = []
    for c in model.cells:
        if abs(c.x - x0) < 0.001 and c.y < y1 * 0.5:
            cells_inj.append(c)
            all_vol += c.get_attr(ca_vol)

    q_inj = 1.0e-6
    for cell in cells_inj:
        model.add_injector(
            fluid_id=1,
            flu=cell.get_fluid(1),
            pos=cell.pos,
            radi=0.1,
            opers=[(0, q_inj * cell.get_attr(ca_vol) / all_vol)]
        )


    # 最大时间步长
    tfc.set_dt_max(model, 3600 * 24)
    return model


def show(model: Seepage, jx: int, jy: int):
    """
    在界面上显示模型的状态.
    Args:
        model: 模型对象
        jx: 模型的x方向的单元格数量
        jy: 模型的y方向的单元格数量
    """
    x = tfc.get_x(model, shape=(jx, jy))
    y = tfc.get_y(model, shape=(jx, jy))
    p = tfc.get_p(model, shape=(jx, jy))
    s = tfc.get_v(model, 1, shape=(jx, jy)) / tfc.get_v(model, None, shape=(jx, jy))

    def on_figure(figure):
        layout = AutoFigLayout(figure, 2, subplot_aspect_ratio=4.0, xlabel='x/m', ylabel='r/m', aspect='equal')
        layout.add_axes2(
            add_contourf, x, y, p, cbar=dict(label='Pressure', shrink=0.7), title='Pressure'
        )
        layout.add_axes2(
            add_contourf, x, y, s, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm', title='Saturation'
        )

    plot(on_figure, caption=f'Seepage({model.handle_str})', tight_layout=True)


def main():
    """
    执行建模并且求解的主函数
    """
    jx, jy = 50, 20
    model = create(jx, jy, s={'water': 0, 'oil': 1})
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=5 * 3600)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
