# ** desc = '圆柱中的驱替过程(三相流)'
#
# 物理问题描述：
#   本模型在圆柱坐标系中模拟气-水-油三相流驱替过程。
#   模型为一维径向流（轴向对称），长度1m，半径0.25m。
#   左侧（x=0处）以恒定流量注入水（流体ID=1），
#   右侧（x=1处）设置为定压流出边界。
#   初始时模型内部为气-油各占50%（gas=0.5, oil=0.5），
#   水从左侧注入后驱动气-油混合物向右运动，三种流体在
#   孔隙介质中表现出不同的流动行为。
#   三相流模拟比两相流更复杂，需要考虑各相之间的相互作用。
#
# 建模技术要点：
#   1. 使用 create_cylinder 生成圆柱坐标系网格
#   2. 定义三种流体（gas/water/oil），密度和粘度各不相同
#   3. 右侧大体积单元作为定压边界（体积设为1e8）
#   4. 通过 add_injector 在左侧注入水（恒定流量1e-6 m3/s）
#   5. 关闭密度更新、粘度更新、热传导和热交换以简化计算
#   6. 显示各相饱和度云图（Gas和Oil）以及压力云图

from zmlx import *


def create(jx: int, jy: int, s=None) -> Seepage:
    """
    创建圆柱坐标系下的三相（气-水-油）驱替模型。

    Args:
        jx: x方向（轴向）的网格单元数量
        jy: y方向（径向）的网格单元数量
        s: 初始饱和度分布。若为None，默认气-水-油各占1/3

    Returns:
        model: 渗流模型对象
    """
    # 生成圆柱网格：轴向0~1m，径向0~0.25m
    mesh: SeepageMesh = create_cylinder(
        x=linspace(0, 1.0, jx + 1),
        r=linspace(0, 0.25, jy + 1)
    )

    x0, x1 = mesh.get_pos_range(0)  # 获取x方向坐标范围
    y0, y1 = mesh.get_pos_range(1)  # 获取y方向（径向）坐标范围

    # 将右侧（x最大处）的单元体积设为极大值，模拟定压边界
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x1) < 0.0001:
            cell.vol = 1.0e8

    # 定义三种流体：
    #   gas：密度100 kg/m3，粘度1e-4 Pa·s（轻质、易流动）
    #   water：密度1000 kg/m3，粘度1e-3 Pa·s（重质、中等粘度）
    #   oil：密度800 kg/m3，粘度1e-2 Pa·s（中等密度、高粘度）
    fluid_defs = [
        FluDef(den=100,  vis=1.0e-4, name='gas'),
        FluDef(den=1000, vis=1.0e-3, name='water'),
        FluDef(den=800,  vis=1.0e-2, name='oil'),
    ]

    if s is None:
        s = {'water': 0.333, 'oil': 0.333, 'gas': 0.333}

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

    # 查找注入位置的单元：左侧底部（x最小，y<径向一半）
    ca_vol = model.get_cell_key('vol')
    all_vol = 0
    cells_inj = []
    for c in model.cells:
        if abs(c.x - x0) < 0.001 and c.y < y1 * 0.5:
            cells_inj.append(c)
            all_vol += c.get_attr(ca_vol)

    # 以恒定流量1e-6 m3/s注入水（流体ID=1），按体积比例分配
    q_inj = 1.0e-6
    for cell in cells_inj:
        model.add_injector(
            fluid_id=1,
            flu=cell.get_fluid(1),
            pos=cell.pos,
            radi=0.1,
            opers=[(0, q_inj * cell.get_attr(ca_vol) / all_vol)]
        )


    # 设置最大时间步长为1天（86400秒）
    tfc.set_dt_max(model, 3600 * 24)
    return model


def show(model: Seepage, jx: int, jy: int):
    """
    在界面上显示模型的状态。
    显示三个子图：压力分布云图、Gas饱和度云图、Oil饱和度云图。

    Args:
        model: 渗流模型对象
        jx: x方向（轴向）网格单元数量
        jy: y方向（径向）网格单元数量
    """
    x = tfc.get_x(model, shape=(jx, jy))
    y = tfc.get_y(model, shape=(jx, jy))
    p = tfc.get_p(model, shape=(jx, jy))
    s0 = tfc.get_v(model, 0, shape=(jx, jy)) / tfc.get_v(model, None, shape=(jx, jy))
    s2 = tfc.get_v(model, 2, shape=(jx, jy)) / tfc.get_v(model, None, shape=(jx, jy))

    def on_figure(figure):
        layout = AutoFigLayout(figure, 3, subplot_aspect_ratio=4.0, xlabel='x/m', ylabel='r/m', aspect='equal')
        layout.add_axes2(
            add_contourf, x, y, p, cbar=dict(label='Pressure', shrink=0.7), title='Pressure'
        )
        layout.add_axes2(
            add_contourf, x, y, s0, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm', title='Gas Saturation'
        )
        layout.add_axes2(
            add_contourf, x, y, s2, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm', title='Oil Saturation'
        )

    plot(on_figure, caption=f'Seepage({model.handle_str})', tight_layout=True)


def main():
    """
    主函数：创建网格为100x30的圆柱模型（初始为气-油各50%），求解2小时的驱替过程。
    """
    jx, jy = 100, 30
    model = create(jx, jy, s={'gas': 0.5, 'oil': 0.5})
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=3600*2)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
