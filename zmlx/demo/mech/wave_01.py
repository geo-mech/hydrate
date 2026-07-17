# ** desc = '动态的有限元计算：添加初始的冲击速度，计算应力波的传递过程'
#
# 【详细说明】
# 本案例演示了二维有限元方法模拟应力波传播的完整过程。
# 使用来自mesh_c10000数据集的圆盘形网格，在圆盘中部（x≈0.16）的带状区域
# 施加相反的初始速度（左侧-1，右侧+1），模拟一个向两侧传播的拉伸/压缩波。
#
# 关键技术细节：
#   1. 使用预定义的圆盘形三角形网格（约10000个单元）
#   2. 初始条件为速度冲击，而非力载荷或位移载荷
#   3. 极小的固定时间步长（dt=1e-6），满足CFL条件
#   4. 使用共轭梯度隐式求解器，保证数值稳定性
#   5. 共推进300步，每10步更新可视化，观察波从中心向四周传播的过程
#
# 该问题类似于地震学中的点源激发，是弹性动力学的基础案例。

from zmlx import *
from zmlx.data import mesh_c10000 as data
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：使用预定义圆盘网格，模拟初始速度冲击下的应力波传播。

    在圆盘中部（x≈0.16）带状区域施加方向相反的初始速度：
      - 左侧节点：速度-1（向左）
      - 右侧节点：速度+1（向右）
    模拟一个向两侧对称传播的弹性波。
    """
    # 从预定义数据加载圆盘形三角形网格（z=0平面）
    mesh = data.get_mesh3(z=0)
    assert isinstance(mesh, Mesh3)

    # Mesh的face的自定义属性的ID
    fa_ym = 0    # 杨氏模量 [Pa]
    fa_mu = 1    # 泊松比 [无量纲]
    fa_den = 2   # 密度 [kg/m^3]
    fa_h = 3     # 厚度 [m]

    # 设置所有单元的材料属性
    for face in mesh.faces:
        face.set_attr(fa_ym, 1.0e9)  # 杨氏模量: 1 GPa
        face.set_attr(fa_mu, 0.2)    # 泊松比: 0.2
        face.set_attr(fa_den, 1000.0) # 密度: 1000 kg/m^3
        face.set_attr(fa_h, 1.0)     # 厚度: 1 m

    # 计算每个三角形单元的刚度矩阵
    face_stiffs = compute_face_stiff2(
        mesh, fa_E=fa_ym, fa_mu=fa_mu,
        fa_h=fa_h)

    # 组装全局动力学系统
    model = FemAlg.create2(
        mesh=mesh, fa_den=fa_den, fa_h=fa_h,
        face_stiffs=face_stiffs)

    assert isinstance(model, DynSys)

    # 保存初始节点坐标（用于后续计算位移变化量）
    x0 = np.array([node.pos[0] for node in mesh.nodes])
    y0 = np.array([node.pos[1] for node in mesh.nodes])

    # 在圆盘中部施加初始速度冲击
    for node in mesh.nodes:
        assert isinstance(node, Mesh3.Node)
        x, y = node.pos[:2]
        xx = 0.16  # 冲击波初始位置x坐标
        # 在x≈0.16的带状区域（宽度0.1），y方向范围-0.3~0.3内施加速度
        if xx - 0.05 < x < xx + 0.05 and -0.3 < y < 0.3:
            v = -1 if x < xx else 1  # 左侧向左、右侧向右，形成拉伸
        else:
            v = 0  # 其他区域初始速度为零
        model.set_vel(node.index * 2, v)  # 设置x方向初始速度

    # 创建共轭梯度求解器
    solver = ConjugateGradientSolver(tolerance=1.0e-20)

    def on_figure(fig):
        """
        绘制位移幅值云图的回调函数。

        计算每个节点相对于初始位置的位移幅值（sqrt(dx^2 + dy^2)），
        并以三角形等值线图显示。

        Args:
            fig: matplotlib图形对象
        """
        x1 = np.array([model.get_pos(idx * 2) for idx in range(mesh.node_number)])
        y1 = np.array([model.get_pos(idx * 2 + 1) for idx in range(mesh.node_number)])
        dx = x1 - x0
        dy = y1 - y0
        dist = np.sqrt(dx ** 2 + dy ** 2)  # 位移幅值
        add_axes2(
            fig, add_tricontourf, x1, y1, dist,
            cbar=dict(label='disp/m'), title='位移',
            aspect='equal', xlabel='x/m', ylabel='y/m'
        )
        fig.tight_layout()

    # 时间推进：300步，步长1e-6，每10步更新可视化
    for i in range(300):
        gui.break_point()              # 检查GUI中断请求
        model.iterate(dt=0.000001, solver=solver)  # 推进一个时间步
        if i % 10 == 0:
            print(i)
            plot(on_figure, caption='位移场')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
