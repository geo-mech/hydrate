# ** desc = '两相流，流体注入驱替'
#
# 本示例模拟二维平面区域内两相流驱替过程，在具有一定随机性的网格上模拟
# 流体注入驱替。模型区域为约100m×100m的矩形，采用50×50的网格剖分，
# 网格尺寸略有随机变化以模拟真实地质条件的非均匀性。
# 边界设置固定压力（大孔隙体积法模拟恒压边界），内部设置一口注入井
# 以恒定速率注入高密度流体（流体1），驱替初始存在于孔隙中的
# 低密度流体（流体0）。模拟忽略密度/粘度更新和热效应，仅关注
# 两相流动过程，求解时长为1年。通过等值线图展示压力场和饱和度场的时空演化。


from zmlx import *


def create():
    """
    创建一个具有随机性的两相流模型。

    随机性体现在：网格尺寸在一定范围内随机变化（80%~120%），
    两种流体的粘度也具有一定随机性（50%~150%），以及注入井的位置
    在模型中心附近随机偏移。这模拟了地质条件的非均质性。

    Returns:
        返回创建的Seepage模型对象，包含网格、流体定义、边界条件和注入井。
    """
    import random
    mesh = create_cube(
        np.linspace(0, 100 * random.uniform(0.8, 1.2), 50),  # x方向：长度在80~120m间随机，50个网格
        np.linspace(0, 100 * random.uniform(0.8, 1.2), 50),  # y方向同x，网格非均匀以模拟真实地质
        (-0.5, 0.5))  # z方向仅1个单元厚度，构成二维平面模型

    # 获得Mesh的坐标范围
    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    # 固定边界位置的压力（通过赋予极大孔隙体积来模拟恒压边界条件）
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x0) < 0.1 or abs(x - x1) < 0.1 or abs(y - y0) < 0.1 or abs(
                y - y1) < 0.1:
            cell.vol = 1.0e8  # 大孔隙体积 -> 压力几乎不变，相当于Dirichlet边界

    model = tfc.create(
        mesh, porosity=0.2, pore_modulus=100e6,  # 孔隙度0.2，孔隙模量100MPa
        p=1e6, temperature=280,  # 初始压力1MPa，温度280K
        s=(1, 0), perm=1e-14,  # 初始饱和度：流体0占100%，渗透率1e-14 m^2
        disable_update_den=True,  # 禁用密度更新（简化计算，假设不可压缩）
        disable_update_vis=True,  # 禁用粘度更新（假设粘度恒定）
        disable_ther=True,  # 禁用热力学计算（等温假设）
        disable_heat_exchange=True,  # 禁用热交换（忽略温度效应）
        fludefs=[
            FluDef(den=50, vis=1.0e-4 * random.uniform(0.5, 1.5),
                   name='flu0'),  # 流体0：低密度(50)，低粘度，模拟轻质相（如气体）
            FluDef(den=1000, vis=1.0e-3 * random.uniform(0.5, 1.5),
                   name='flu1')]  # 流体1：高密度(1000)，高粘度，模拟水相
    )

    cell = model.get_nearest_cell(
        (40 * random.uniform(0.8, 1.2), 40 * random.uniform(0.8, 1.2), 0))  # 在中心附近随机选取注入井位置
    model.add_injector(fluid_id=1, flu=cell.get_fluid(1),  # 注入流体1（高密度流体）
                       pos=cell.pos,
                       radi=0.1, opers=[(0, 1.0e-5)])  # 注入半径0.1m，注入速率1e-5 kg/s
    tfc.set_dt_max(model, 3600 * 24)  # 限制最大时间步长为1天，确保计算稳定性

    # 返回最终的模型
    return model


def show_model(model: Seepage):
    """
    可视化模型的当前状态（压力场和饱和度场）。

    根据模型的当前时间步，绘制压力等值线图和流体1饱和度等值线图，
    以直观展示驱替过程的进展。需要GUI支持。

    Args:
        model: 待可视化的Seepage渗流模型对象。
    """
    if not gui:
        return

    x = tfc.get_cell_pos(model, dim=0)  # 提取所有单元的x坐标
    y = tfc.get_cell_pos(model, dim=1)  # 提取所有单元的y坐标
    p = tfc.get_cell_pre(model)  # 提取所有单元的压力值
    s = tfc.get_cell_fv(model, fid=1) / tfc.get_cell_fv(model)  # 计算流体1的饱和度（体积分数）

    def on_figure(figure):
        layout = AutoLayout(figure, 2, subplot_aspect_ratio=1.0, xlabel='x', ylabel='y', aspect='equal')
        layout.add_axes2(add_tricontourf, x, y, p, title='Pressure',
                         cbar=dict(label='Pressure')
                         )
        layout.add_axes2(add_tricontourf, x, y, s, title='Saturation',
                         cbar=dict(label='Saturation')
                         )
        figure.suptitle(f'Model when time = {tfc.get_time(model, as_str=True)}')

    plot(on_figure, caption=f'Seepage({model.handle_str})', clear=True)


def main():
    """
    主函数：创建模型并启动瞬态求解。

    使用tfc.solve进行自动时间步进求解，总时长1年（365天）。
    求解过程中定期调用show_model实时可视化压力场和饱和度场的演化。

    Returns:
        无返回值。求解结果保存在'liq_inj'文件夹中。
    """
    model = create()
    tfc.solve(
        model, folder=opath('liq_inj'),
        time_max=3600 * 24 * 365,  # 求解终止时间：365天（1年）
        extra_plot=lambda: show_model(model),  # 每个时间步结束后自动调用，更新可视化
    )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
