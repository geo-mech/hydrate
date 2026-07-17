# ** desc = '对于2m*2m的区域，在中间的一个小矩形区域内，添加流体压力'
#
# 【详细说明】
# 本案例模拟一个2m × 2m的矩形弹性体，在中心一个小区域（|x|<0.2, |y|<0.2）内
# 施加流体压力（1 MPa），计算弹性体的变形响应。
#
# 该问题模拟了水力压裂或流体注入导致地层膨胀的物理过程：
#   - 中心区域的流体压力使单元面受到法向压力
#   - 弹性体在内部压力作用下发生膨胀变形
#   - 通过alg_xy.add_face_pressure在三角形面上施加压力载荷
#
# 与前面案例的区别：载荷不是施加在边界上，而是施加在内部单元的面上，
# 模拟体积力（流体压力）的效应。使用较密的网格（50×60）提高精度。

from zmlx import *
from zmlx.fem import alg_xy
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt import add_tricontourf
from zmlx.plt.on_figure import add_axes2


def main():
    """
    主函数：模拟在方形弹性体中心区域施加流体压力引起的变形。

    使用三角形网格（50×60），杨氏模量1 GPa，泊松比0.2。
    在中心区域（|x|<0.2, |y|<0.2）的每个三角形面上施加1 MPa的均匀压力，
    通过alg_xy.add_face_pressure实现。
    """
    # 定义方形区域的边界 [m]
    x_min = -1
    x_max = 1
    y_min = -1
    y_max = 1

    # Mesh的face的自定义属性的ID
    fa_ym = 0    # 杨氏模量 [Pa]
    fa_mu = 1    # 泊松比 [无量纲]
    fa_den = 2   # 密度 [kg/m^3]
    fa_h = 3     # 厚度 [m]

    # 生成较密的三角形网格（50×60），中心区域需要较高的分辨率
    mesh = layered_triangles(x_min, x_max, 50, y_min, y_max, 60, as_mesh=True)
    assert isinstance(mesh, Mesh3)

    # 设置所有单元的材料属性
    for face in mesh.faces:
        face.set_attr(fa_ym, 1.0e9)   # 杨氏模量: 1 GPa
        face.set_attr(fa_mu, 0.2)     # 泊松比: 0.2
        face.set_attr(fa_den, 1000.0) # 密度: 1000 kg/m^3
        face.set_attr(fa_h, 1.0)      # 厚度: 1 m

    # 计算每个三角形单元的刚度矩阵
    face_stiffs = compute_face_stiff2(
        mesh, fa_E=fa_ym, fa_mu=fa_mu,
        fa_h=fa_h)

    # 组装全局动力学系统
    model = FemAlg.create2(
        mesh=mesh, fa_den=fa_den, fa_h=fa_h,
        face_stiffs=face_stiffs)

    # 在中心小区域（|x|<0.2, |y|<0.2）的每个三角形面上施加流体压力
    # 压力方向垂直于单元面，大小为1 MPa
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        x, y = face.pos[:2]
        if abs(x) < 0.2 and abs(y) < 0.2:
            # 在三角形面上施加均匀压力，转换为等效节点力
            alg_xy.add_face_pressure(model, mesh, face.index, pressure=1e6, thick=1.0)

    # 执行静态求解
    solver = ConjugateGradientSolver(tolerance=1.0e-30)
    model.iterate(dt=1, solver=solver)

    def on_figure(fig):
        """
        绘制位移场云图的回调函数。

        Args:
            fig: matplotlib图形对象
        """
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        dy = [vy[i] - mesh.get_node(i).pos[1] for i in range(mesh.node_number)]

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=1, ncols=2)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)

    plot(on_figure, gui_mode=True, caption='位移场')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
