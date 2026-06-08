# ** desc = '两相流，水驱替油模拟'

from zmlx import *


def create(jx: int, jy: int, s=None, fid_inj=None) -> Seepage:
    """
    创建模型.
    Args:
        jx: 模型的x方向的单元格数量
        jy: 模型的y方向的单元格数量
        s: 初始饱和度. 默认值为(1, 0)
        fid_inj: 注入 fluid_id. 默认值为1

    Returns:
        model: 模型对象
    """
    mesh: SeepageMesh = create_cube(
        linspace(0, 30, jx + 1),
        linspace(0, 30, jy + 1), (-0.5, 0.5)
    )

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(y - y1) < 0.1 and abs(x - x1) < 0.1:
            cell.vol = 1.0e8

    # 定义流体
    fluid_defs = [
        FluDef(den=50, vis=1.0e-2, name='oil'),
        FluDef(den=1000, vis=1.0e-3, name='water')
    ]

    if s is None:
        s = (1, 0)

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

    if fid_inj is None:
        fid_inj = 1

    cell = model.get_nearest_cell((x0, y0, 0))
    assert cell is not None
    model.add_injector(
        fluid_id=fid_inj,
        flu=cell.get_fluid(1),
        pos=cell.pos,
        radi=0.1,
        opers=[(0, 1.0e-5)]
    )
    # 最大时间步长
    tfc.set_dt_max(model, 3600 * 24 * 7)
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

    opts = dict(aspect='equal', xlabel='x/m', ylabel='y/m')
    obj = fig.auto_layout(
        fig.axes2(
            fig.contourf(x, y, p, cbar=dict(label='Pressure', shrink=0.7)),
            index=1,
            title='Pressure', **opts
        ),
        fig.axes2(
            fig.contourf(x, y, s, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm'),
            index=2,
            title='water saturation', **opts
        ),
        fig.suptitle(f'时间: {tfc.get_time(model, as_str=True)}'),
        fig.tight_layout(),
        aspect_ratio=1,
    )
    fig.show(obj, caption='模型状态')


def wat_disp_oil():
    """
    执行建模并且求解的主函数
    """
    jx, jy = 30, 30
    model = create(jx, jy, s=(1, 0), fid_inj=1)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=100 * 24 * 3600)


if __name__ == '__main__':
    gui.execute(wat_disp_oil, close_after_done=False)
