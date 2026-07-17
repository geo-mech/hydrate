# ** desc = '侵入逾渗(IP)模型计算油气运移成藏'

# 本案例使用侵入逾渗（Invasion Percolation, IP）模型模拟油气在
# 多孔介质中的二次运移和聚集成藏过程。
# 物理问题：油气在浮力驱动下从深部（注入点）向上运移，穿过孔隙-喉道网络，
# 在遇到合适的圈闭条件时聚集成藏。模型中每个节点代表一个孔隙（具有随机半径），
# 每条边代表连接孔隙的喉道（也具有随机半径），流体优先通过阻力最小的通道运移。
# 建模方法：在一个100m x 300m的二维网格上构建IP模型，节点和喉道的半径随机赋值
# 以模拟孔隙介质的非均质性。设置两个注入点（底部），一个出口（顶部），
# 在浮力作用下模拟油气从底部向顶部的运移过程。使用GuiIterator进行迭代，
# 步进式展示逾渗过程的演化。

from zmlx import *


def create(jx=100, jy=300):
    """
    创建侵入逾渗（IP）模型。

    在100m x 300m的二维区域上建立孔隙-喉道网络：
    - 每个网格单元对应一个孔隙节点，节点位置由网格中心确定
    - 节点半径在1.0~2.0范围内随机分布，模拟孔隙大小的非均质性
    - 相邻节点之间的连接（喉道）半径在0.5~1.0范围内随机分布
    - 设置重力方向为负y方向（浮力向上），两种流体的密度差产生驱动力
    - 设置顶部出口和底部两个注入点

    参数:
        jx: x方向网格数量（默认100）
        jy: y方向网格数量（默认300）

    返回:
        InvasionPercolation: 创建好的IP模型对象
    """
    assert np is not None
    import random
    # 创建100x300的二维网格，每个网格单元对应一个孔隙节点
    mesh = create_cube(
        x=np.linspace(0, 100, jx + 1),
        y=np.linspace(0, 300, jy + 1),
        z=(0, 1))
    model = InvasionPercolation()  # 创建IP模型实例
    random.seed(1000000)  # 固定随机种子，确保结果可重复

    # 遍历所有网格单元，为每个单元创建一个孔隙节点
    for cell in mesh.cells:
        node = model.add_node()  # 添加节点
        node.pos = cell.pos  # 设置节点位置为网格单元中心
        node.phase = 0  # 初始相位为0（背景流体）
        node.radi = random.uniform(1.0, 2.0)  # 随机节点半径（1~2）
    node_n = model.node_n
    print(f'Load nodes. Count = {node_n}')

    # 遍历所有面（相邻单元之间的连接），为每对相邻节点创建喉道（键）
    for face in mesh.faces:
        i0 = face.get_cell(0).index
        i1 = face.get_cell(1).index
        assert node_n > i0 != i1 < node_n
        bond = model.add_bond(i0, i1)  # 添加连接两个节点的键
        bond.radi = random.uniform(0.5, 1.0)  # 随机喉道半径（0.5~1）
    bond_n = model.bond_n
    print(f'Load bonds. Count = {bond_n}')

    # 设置重力方向和流体密度（用于计算浮力）
    model.gravity = (0, -0.001, 0)  # 重力方向为负y方向
    model.set_density(0, 1.0)  # 背景流体密度
    model.set_density(1, 0.1)  # 入侵流体（油气）密度 —— 密度差产生浮力

    # 设置出口：在顶部中央位置作为流体排出的出口
    model.outlet_n = 1
    model.set_outlet(
        0, model.get_nearest_node(pos=(50, 300, 0)).index)

    # 设置第一个注入点（底部偏左位置）
    inj = model.add_inj()
    inj.node_id = model.get_nearest_node(pos=(30, 0, 0)).index
    inj.phase = 1  # 注入流体相位为1（油气）
    inj.qinj = 1  # 注入速率

    # 设置第二个注入点（底部偏右位置），注入速率较低
    inj = model.add_inj()
    inj.node_id = model.get_nearest_node(pos=(70, 0, 0)).index
    inj.phase = 1
    inj.qinj = 0.5

    return model


def solve(model, jx, jy):
    """
    求解侵入逾渗模型并实时显示逾渗过程。

    使用GuiIterator驱动模型迭代，每次迭代后更新图形显示。
    共进行4000步迭代，每50步输出当前状态并强制更新图形。
    通过记录每次入侵操作的路径（节点对），追踪流体的运移轨迹。

    参数:
        model: 要求解的IP模型对像
        jx: x方向网格数量
        jy: y方向网格数量
    """
    # 创建GUI迭代器，每次迭代后更新xy平面显示
    it = GuiIterator(iterate=model.iterate, plot=lambda: ip.show_xy(model, jx=jx, jy=jy), ratio=0.2)
    for step in range(4000):
        gui.break_point()  # 检查GUI中断请求
        it(forced_plot=step % 50 == 0)  # 执行迭代，每50步强制更新图形
        if step % 50 == 0:
            print(f'step = {step}, time = {model.time}, ', end='')
            print('Invade operations: ', end='')
            # 输出本次操作的入侵路径
            for idx in range(model.oper_n):
                oper = model.get_oper(idx)
                print(f'({oper.get_node(0).index} -> {oper.get_node(1).index})',
                      end=', ')
            print('')


def execute(gui_mode=True, close_after_done=False):
    """
    程序入口：执行侵入逾渗模拟。

    创建模型并添加初始倾斜（x坐标偏移），然后进行迭代求解。

    参数:
        gui_mode: 是否启用GUI显示（默认为True）
        close_after_done: 计算完成后是否自动关闭窗口（默认为False）
    """
    jx, jy = 100, 300
    model = create(jx, jy)
    # 对模型添加x方向偏移（模拟构造倾斜，使油气向构造高部位运移）
    ip.set_x(model, ip.get_x(model) + ip.get_y(model) * 0.3)
    gui.execute(lambda: solve(model, jx, jy), close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
