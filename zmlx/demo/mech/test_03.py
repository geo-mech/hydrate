# ** desc = '3m*1m的矩形区域：左侧固定，右侧受到面力作用(力的方向向左)。和上一个case的差异：设置较小的时间步长，计算动态的应力波传递的过程'

from zmlx import *
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def main():
    # 定义矩形区域的边界
    X_MIN = 0
    X_MAX = 3
    Y_MIN = 0
    Y_MAX = 1

    mesh = layered_triangles(X_MIN, X_MAX, 30, Y_MIN, Y_MAX, 10, as_mesh=True)

    # Mesh的face的自定义属性的ID
    fa_ym = 0
    fa_mu = 1
    fa_den = 2
    fa_h = 3

    for face in mesh.faces:
        face.set_attr(fa_ym, 1.0e9)  # 杨氏模量
        face.set_attr(fa_mu, 0.2)
        face.set_attr(fa_den, 1000.0)
        face.set_attr(fa_h, 1.0)

    face_stiffs = compute_face_stiff2(
        mesh, fa_E=fa_ym, fa_mu=fa_mu,
        fa_h=fa_h)

    model = FemAlg.create2(
        mesh=mesh, fa_den=fa_den, fa_h=fa_h,
        face_stiffs=face_stiffs)

    for i in range(mesh.node_number):
        x = mesh.get_node(i).pos[0]
        if x < 0.01:  # 对于左侧的所有node，增大质量，确保位置不变
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
        if x > 2.99:  # 对于右侧的node，添加一个纵向的压力
            f = model.get_p2f(i * 2)
            f.c -= 1e3

    def on_figure(fig):
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        dy = [vy[i] - mesh.get_node(i).pos[1] for i in range(mesh.node_number)]

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=2, ncols=1)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)
        fig.tight_layout()

    def solve():
        """
        求解动态的过程
        """
        for step in range(200):
            print(f'第{step}步')
            solver = ConjugateGradientSolver(tolerance=1.0e-30)
            model.iterate(dt=0.0001, solver=solver)
            plot(on_figure, gui_mode=True, caption='位移场')

    gui.execute(solve, close_after_done=False)


if __name__ == '__main__':
    main()
