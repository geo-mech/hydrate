# ** desc = '对于3m*1m的矩形的区域，划分三角形网格 (在顶部1<x<2的范围内，添加分布力的载荷)'

from zmlx import *
from zmlx.fem import alg_xy
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def main():
    # 定义矩形区域的边界
    x_min = 0
    x_max = 3
    y_min = 0
    y_max = 1

    # Mesh的face的自定义属性的ID
    fa_ym = 0
    fa_mu = 1
    fa_den = 2
    fa_h = 3

    mesh = layered_triangles(x_min, x_max, 100, y_min, y_max, 30, as_mesh=True)

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
        x, y = mesh.get_node(i).pos[0], mesh.get_node(i).pos[1]
        if x < 0.01 or x > x_max - 0.01:  # 左右的node，固定x方向的位移
            model.set_mass(i * 2, model.get_mass(i * 2) * 1.0e20)
            continue
        if y < 0.01:  # 底部，固定y方向的位移
            model.set_mass(i * 2 + 1, model.get_mass(i * 2 + 1) * 1.0e20)
            continue

    for link in mesh.links:  # 顶部，添加向下的压力
        assert isinstance(link, Mesh3.Link)
        if link.face_number == 1:
            x, y = link.pos[0], link.pos[1]
            if 1 < x < 2 and y > y_max - 0.01:
                alg_xy.add_link_force(model, mesh, link.index, [0, -1e6 * link.length])

    solver = ConjugateGradientSolver(tolerance=1.0e-30)
    model.iterate(dt=1, solver=solver)

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

    plot(on_figure, gui_mode=True, caption='位移场')


if __name__ == '__main__':
    main()
