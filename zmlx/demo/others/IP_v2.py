# ** desc = '侵入逾渗(IP)模型计算油气运移成藏(测试更多的批量接口)'

# 本案例是IP.py的变体，主要目的为测试IP模型的批量接口（批量设置属性），
# 以验证大批量节点/键的属性设置效率和正确性。
# 物理问题同IP.py：油气在浮力驱动下从底部注入点向上运移，
# 在孔隙-喉道网络中寻找阻力最小路径，穿过随机介质向顶部出口运移。
# 建模方法：与IP.py相同，使用侵入逾渗模型模拟油气二次运移，但注入点和
# 出口的设置改用批量接口（read_outlet, read_inj_node_id, read_inj_phase,
# read_inj_q），以验证批量API的正确调用方式。
# 求解过程复用IP.py中的solve函数。

from zmlx import *


def create(jx=100, jy=300):
    """
    创建侵入逾渗（IP）模型，使用批量接口设置注入点和出口。

    与IP.py中的create函数功能相同，但出口和注入点的设置方式不同：
    使用read_outlet、read_inj_node_id等批量接口替代逐个添加的方式，
    以测试批量API的可用性。

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
    model = InvasionPercolation()  # 创建IP模型实例
    random.seed(1000000)  # 固定随机种子

    # 逐个添加节点（每个网格单元对应一个孔隙节点）
    for cell in mesh.cells:
        node = model.add_node()
        node.pos = cell.pos
        node.phase = 0  # 初始相位0（背景流体）
        node.radi = random.uniform(1.0, 2.0)  # 随机孔隙半径
    node_n = model.node_n
    print(f'Load nodes. Count = {node_n}')

    # 逐个添加喉道（连接相邻节点）
    for face in mesh.faces:
        i0 = face.get_cell(0).index
        i1 = face.get_cell(1).index
        assert node_n > i0 != i1 < node_n
        bond = model.add_bond(i0, i1)
        bond.radi = random.uniform(0.5, 1.0)  # 随机喉道半径
    bond_n = model.bond_n
    print(f'Load bonds. Count = {bond_n}')

    # 设置重力和流体密度
    model.gravity = (0, -0.001, 0)
    model.set_density(0, 1.0)  # 背景流体密度
    model.set_density(1, 0.1)  # 入侵流体密度

    # 使用批量接口设置出口（相比IP.py的逐个添加方式）
    model.outlet_n = 1
    model.read_outlet(const_f64_ptr([model.get_nearest_node(pos=(50, 300, 0)).index]))

    # 使用批量接口设置两个注入点（相比IP.py的逐个添加方式）
    i0 = model.get_nearest_node(pos=(30, 0, 0)).index
    i1 = model.get_nearest_node(pos=(70, 0, 0)).index

    model.inj_n = 2
    model.read_inj_node_id(
        const_f64_ptr([i0, i1])  # 批量设置注入点节点ID
    )
    model.read_inj_phase(
        const_f64_ptr([1, 1])  # 批量设置注入流体相位
    )
    model.read_inj_q(
        const_f64_ptr([1, 0.5])  # 批量设置注入速率
    )
    return model


def execute(gui_mode=True, close_after_done=False):
    """
    程序入口：执行侵入逾渗模拟（使用批量接口测试）。

    创建模型（使用批量API），然后复用IP.py中的solve函数进行求解。
    通过复用solve函数确保批量接口创建的模型与逐个添加方式创建的模型行为一致。

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
