# ** desc = '动态的有限元计算：添加初始的冲击速度，计算应力波的传递过程'
#
# 【详细说明】
# 本案例是wave_01.py的对应版本，模拟完全相同的物理问题
# （圆盘形网格，中部初始速度冲击，应力波传播），
# 但使用zmlx.fem.xy模块的高级API（xy.create_dyn）来实现。
#
# 对比wave_01.py和wave_01b.py可以看出：
#   1. 高级API（xy.create_dyn）大幅简化了建模代码
#   2. 高级API不需要显式创建ConjugateGradientSolver
#   3. 初始条件的施加方式在两种API中相同
#   4. 绘图方式略有差异：wave_01b.py使用初始坐标x0/y0作为绘图坐标

from zmlx import *
from zmlx.data import mesh_c10000 as data
from zmlx.fem import xy
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：使用xy.create_dyn高级API创建模型，模拟初始速度冲击下的应力波传播。

    与wave_01.py的差异：使用高级API简化建模流程，不显式指定求解器。
    物理设置和求解参数保持一致（dt=1e-6，300步）。
    """
    # 从预定义数据加载圆盘形三角形网格（z=0平面）
    mesh = data.get_mesh3(z=0)
    assert isinstance(mesh, Mesh3)

    # 获取面的数量，用于创建材料属性列表
    face_n = mesh.face_number

    # 使用xy.create_dyn高级API创建动力学系统
    model = xy.create_dyn(
        mesh=mesh, face_ym=[1.0e9] * face_n, face_mu=[0.2] * face_n,
        face_density=[1000.0] * face_n,
        face_thickness=[1.0] * face_n
    )

    assert isinstance(model, DynSys)

    # 保存初始节点坐标（用于后续可视化）
    x0 = np.array([node.pos[0] for node in mesh.nodes])
    y0 = np.array([node.pos[1] for node in mesh.nodes])

    # 在圆盘中部施加初始速度冲击（与wave_01.py相同）
    for node in mesh.nodes:
        assert isinstance(node, Mesh3.Node)
        x, y = node.pos[:2]
        xx = 0.16
        if xx - 0.05 < x < xx + 0.05 and -0.3 < y < 0.3:
            v = -1 if x < xx else 1  # 左侧向左、右侧向右
        else:
            v = 0
        model.set_vel(node.index * 2, v)  # 设置x方向初始速度

    def on_figure(fig):
        """
        绘制位移幅值云图的回调函数。

        与wave_01.py不同，此处使用初始坐标x0/y0作为绘图坐标，
        位移量直接采用当前节点的x和y方向位移。

        Args:
            fig: matplotlib图形对象
        """
        dx = np.array([model.get_pos(i * 2) for i in range(mesh.node_number)])
        dy = np.array([model.get_pos(i * 2 + 1) for i in range(mesh.node_number)])
        dist = np.sqrt(dx ** 2 + dy ** 2)  # 位移幅值
        add_axes2(
            fig, add_tricontourf, x0, y0, dist,
            cbar=dict(label='disp/m'), title='位移',
            aspect='equal', xlabel='x/m', ylabel='y/m'
        )
        fig.tight_layout()

    # 时间推进：300步，步长1e-6，每10步更新可视化
    for i in range(300):
        gui.break_point()
        model.iterate(dt=0.000001)  # 不使用显式求解器（使用默认设置）
        if i % 10 == 0:
            print(i)
            plot(on_figure, caption='位移场')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
