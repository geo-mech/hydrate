# ** desc = '两相流，水驱替油模拟'
#
# 物理问题描述：
#   本模型模拟水驱替油的经典两相流过程（二次采油）。
#   模型采用二维平面网格（30x30），区域范围0~30m x 0~30m。
#   初始时模型内部充满油（Oil饱和度=1），
#   在左下角以恒定流量1e-5 m3/s注入水（流体ID=1），
#   水逐渐驱替孔隙中的油，最终在右上角（x最大，y最大）流出。
#   这是最基本的水驱油（二次采油）物理模型，用于分析驱替前缘推进、
#   注入压力变化和采出程度等关键参数。
#
# 建模技术要点：
#   1. 使用 create_cube 生成二维平面网格
#   2. 右上角设置大体积单元作为定压出口边界
#   3. 通过 add_injector 在左下角注入水（恒定流量1e-5 m3/s）
#   4. 关闭密度更新、粘度更新、热传导和热交换以简化计算
#   5. 该文件同时被 oil_disp_wat.py 复用（通过修改参数实现油驱水）

from zmlx import *


def create(jx: int, jy: int, s=None, fid_inj=None) -> Seepage:
    """
    创建水驱油（或油驱水）的两相流模型。

    Args:
        jx: x方向的网格单元数量
        jy: y方向的网格单元数量
        s: 初始饱和度。默认值为 (1, 0)，即油饱和度为1，水饱和度为0
        fid_inj: 注入流体的ID。默认值为1（水），若设为0则为注油驱水

    Returns:
        model: 渗流模型对象，包含网格、流体定义、注入井等
    """
    # 生成二维平面网格：0~30m x 0~30m，厚度1m
    mesh: SeepageMesh = create_cube(
        linspace(0, 30, jx + 1),
        linspace(0, 30, jy + 1), (-0.5, 0.5)
    )

    x0, x1 = mesh.get_pos_range(0)  # x方向坐标范围
    y0, y1 = mesh.get_pos_range(1)  # y方向坐标范围

    # 将右上角单元体积设为极大值，模拟定压出口边界
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(y - y1) < 0.1 and abs(x - x1) < 0.1:
            cell.vol = 1.0e8

    # 定义两种流体：oil（密度50 kg/m3，高粘度1e-2 Pa·s）
    # 和 water（密度1000 kg/m3，低粘度1e-3 Pa·s）
    fluid_defs = [
        FluDef(den=50, vis=1.0e-2, name='oil'),
        FluDef(den=1000, vis=1.0e-3, name='water')
    ]

    if s is None:
        s = (1, 0)  # 默认初始为纯油

    # 创建渗流模型：孔隙度0.2，孔隙模量100MPa，压力1MPa，温度280K，渗透率1e-14 m2
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
        fid_inj = 1  # 默认注入水（流体ID=1）

    # 在左下角设置注入井
    cell = model.get_nearest_cell((x0, y0, 0))
    assert cell is not None
    model.add_injector(
        fluid_id=fid_inj,
        flu=cell.get_fluid(1),
        pos=cell.pos,
        radi=0.1,
        opers=[(0, 1.0e-5)]  # 恒定注入流量 1e-5 m3/s
    )
    # 设置最大时间步长为1周
    tfc.set_dt_max(model, 3600 * 24 * 7)
    return model


def show(model: Seepage, jx: int, jy: int):
    """
    在界面上显示模型的状态（压力分布和水饱和度云图）。

    Args:
        model: 渗流模型对象
        jx: x方向的网格单元数量
        jy: y方向的网格单元数量
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
    主函数：创建30x30网格的水驱油模型（初始纯油），模拟100天的驱替过程。
    """
    jx, jy = 30, 30
    model = create(jx, jy, s=(1, 0), fid_inj=1)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=100 * 24 * 3600, plot_gui_only=False)


if __name__ == '__main__':
    gui.execute(wat_disp_oil, close_after_done=False)
