# ** desc = '对于2m*2m的区域，在中间的一个小矩形区域内，添加流体压力'
#
# 【详细说明】
# 本案例是test_06.py的对应版本，模拟完全相同的物理问题
# （2m × 2m弹性体，中心区域施加1 MPa流体压力），
# 但使用zmlx.fem.xy模块的高级API（xy.create_dyn）来实现。
#
# 对比test_06.py（低级API）和test_06b.py（高级API）可以看出：
#   1. 高级API（xy.create_dyn）将材料属性设置和系统组装合并为一行
#   2. 高级API不需要显式创建ConjugateGradientSolver
#   3. 载荷施加方式（alg_xy.add_face_pressure）在两种API中相同

from zmlx import *
from zmlx.fem import alg_xy, xy
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：使用xy.create_dyn高级API创建模型，模拟流体压力引起的变形。

    与test_06.py的差异：使用高级API简化建模流程，不显式指定求解器。
    载荷施加方式相同，均通过alg_xy.add_face_pressure实现。
    """
    # 定义方形区域的边界 [m]
    x_min = -1
    x_max = 1
    y_min = -1
    y_max = 1

    # 生成较密的三角形网格（50×60）
    mesh = layered_triangles(x_min, x_max, 50, y_min, y_max, 60, as_mesh=True)
    assert isinstance(mesh, Mesh3)

    # 获取面的数量，用于创建材料属性列表
    face_n = mesh.face_number

    # 使用xy.create_dyn高级API创建动力学系统
    model = xy.create_dyn(
        mesh=mesh, face_ym=[1.0e9] * face_n, face_mu=[0.2] * face_n,
        face_density=[1000.0] * face_n,
        face_thickness=[1.0] * face_n
    )

    # 在中心小区域（|x|<0.2, |y|<0.2）的每个三角形面上施加流体压力
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        x, y = face.pos[:2]
        if abs(x) < 0.2 and abs(y) < 0.2:
            # 在三角形面上施加1 MPa的均匀压力
            alg_xy.add_face_pressure(model, mesh, face.index, pressure=1e6, thick=1.0)

    # 执行静态求解（使用默认求解器）
    model.iterate(dt=1)

    def on_figure(fig):
        """
        绘制位移场云图的回调函数。

        Args:
            fig: matplotlib图形对象
        """
        dx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        dy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        vx = [mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        vy = [mesh.get_node(i).pos[1] for i in range(mesh.node_number)]

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=1, ncols=2)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)

    plot(on_figure, gui_mode=True, caption='位移场')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
