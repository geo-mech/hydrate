# ** desc = '侵入逾渗(IP)模型计算油气运移成藏(测试更多的批量接口，包括创建过程)'

# 本案例是IP.py和IP_v2.py的进一步扩展，重点测试IP模型节点和键的批量创建接口。
# 物理问题同前：油气在浮力驱动下从底部向顶部运移，穿过随机孔隙-喉道网络。
# 建模方法：与前两版最大的不同在于节点和喉道的创建方式。本案例使用ip.set_nodes
# 和ip.set_batches批量接口一次性创建所有节点和喉道，而非逐个添加。
# 这种方法在处理大规模模型时具有显著的性能优势。同时，注入点和出口的设置
# 仍使用批量接口（与IP_v2.py相同）。求解过程依旧复用IP.py中的solve函数，
# 以验证批量创建API的正确性和兼容性。

from zmlx import *


def create(jx=100, jy=300):
    """
    创建侵入逾渗（IP）模型，使用批量接口创建节点和喉道。

    与IP.py和IP_v2.py的最主要区别：
    - 节点创建：使用ip.set_nodes批量接口，一次性传入所有节点的坐标、相位和半径
    - 喉道创建：使用ip.set_bonds批量接口，一次性传入所有连接信息和喉道半径
    - 注入点和出口使用批量接口设置（同IP_v2.py）

    批量创建方式在大规模模型中能大幅提高创建效率，避免逐个添加的开销。

    参数:
        jx: x方向网格数量（默认100）
        jy: y方向网格数量（默认300）

    返回:
        InvasionPercolation: 创建好的IP模型对象
    """
    assert np is not None
    import random
    # 创建100x300的二维网格
    mesh = create_cube(
        x=np.linspace(0, 100, jx + 1),
        y=np.linspace(0, 300, jy + 1),
        z=(0, 1))

    # 预先提取所有节点的坐标和所有面的连接关系
    node_pos = np.asarray([c.pos for c in mesh.cells])  # 节点位置数组
    links = np.asarray([f.link for f in mesh.faces])    # 连接关系数组（每行两个节点索引）

    model = InvasionPercolation()
    random.seed(1000000)  # 固定随机种子

    # 使用批量接口一次性创建所有节点
    ip.set_nodes(
        model, mesh.cell_number,
        x=node_pos[:, 0], y=node_pos[:, 1], z=node_pos[:, 2],
        phase=0,  # 所有节点初始相位为0
        radi=[random.uniform(1.0, 2.0) for _ in range(mesh.cell_number)])  # 随机半径
    node_n = model.node_n
    print(f'Load nodes. Count = {node_n}')

    # 使用批量接口一次性创建所有喉道
    ip.set_bonds(
        model, mesh.face_number, node0=links[:, 0], node1=links[:, 1],
        radi=[random.uniform(0.5, 1.0) for _ in range(mesh.face_number)])  # 随机喉道半径
    bond_n = model.bond_n
    print(f'Load bonds. Count = {bond_n}')

    # 设置重力和流体密度
    model.gravity = (0, -0.001, 0)
    model.set_density(0, 1.0)  # 背景流体密度
    model.set_density(1, 0.1)  # 入侵流体（油气）密度

    # 使用批量接口设置出口和注入点
    model.outlet_n = 1
    model.read_outlet(
        const_f64_ptr([model.get_nearest_node(pos=(50, 300, 0)).index]))

    i0 = model.get_nearest_node(pos=(30, 0, 0)).index
    i1 = model.get_nearest_node(pos=(70, 0, 0)).index

    model.inj_n = 2
    model.read_inj_node_id(
        const_f64_ptr([i0, i1]))
    model.read_inj_phase(
        const_f64_ptr([1, 1]))
    model.read_inj_q(
        const_f64_ptr([1, 0.5]))
    return model


def execute(gui_mode=True, close_after_done=False):
    """
    程序入口：执行侵入逾渗模拟（使用批量创建接口测试）。

    创建模型（全部使用批量API），然后复用IP.py中的solve函数进行求解。
    通过复用求解函数，确保批量创建的模型与逐个创建的模型行为一致。

    参数:
        gui_mode: 是否启用GUI显示（默认为True）
        close_after_done: 计算完成后是否自动关闭窗口（默认为False）
    """
    from zmlx.demo.others.IP import solve  # 复用IP.py中的求解函数
    jx, jy = 100, 300
    model = create(jx, jy)
    ip.set_x(model, ip.get_x(model) + ip.get_y(model) * 0.3)  # 构造倾斜
    gui.execute(lambda: solve(model, jx, jy), close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
