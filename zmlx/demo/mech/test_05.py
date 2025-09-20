# ** desc = '对于3m*1m的矩形的区域(在中间添加挖空区，计算挖空之后的位移变化)'

from zmlx import *
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

    # 生成Mesh
    mesh = layered_triangles(x_min, x_max, 100, y_min, y_max, 30, as_mesh=True)

    # -- 建模模型，计算原始的位移场

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

    for i in range(mesh.node_number):  # 顶部，添加向下的压力
        f = model.get_p2f(i * 2 + 1)
        f.c -= 1e2

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

    plot(on_figure, caption='位移场1 (原始在重力作用下)')

    # 备份位移场
    vx0 = [model.get_pos(i * 2) for i in range(mesh.node_number)]
    vy0 = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]

    # -- 建模模型，计算中间的位置挖空之后的应力场

    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        x, y, z = face.pos
        if 1.3 < x < 1.7 and 0.4 < y < 0.6:
            face.set_attr(fa_ym, 1.0e7)  # 杨氏模量折减，模拟挖空区域
        else:
            face.set_attr(fa_ym, 1.0e9)
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

    for i in range(mesh.node_number):  # 顶部，添加向下的压力
        f = model.get_p2f(i * 2 + 1)
        f.c -= 1e2

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

    plot(on_figure, caption='位移场2 (中心挖空之后)')

    def on_figure(fig):
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - vx0[i] for i in range(mesh.node_number)]
        dy = [vy[i] - vy0[i] for i in range(mesh.node_number)]

        args = [fig, add_tricontourf, vx, vy]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=2, ncols=1)

        add_axes2(*args, dx, cbar=dict(label='dx/m'), title='x位移', index=1, **kwds)
        add_axes2(*args, dy, cbar=dict(label='dy/m'), title='y位移', index=2, **kwds)
        fig.tight_layout()

    plot(on_figure, caption='位移场的变化量')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
