# ** desc = '对于2m*2m的区域，在中间的一个小矩形区域内，添加流体压力'

from zmlx import *
from zmlx.fem import alg_xy
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def main():
    # 定义矩形区域的边界
    x_min = -1
    x_max = 1
    y_min = -1
    y_max = 1

    # Mesh的face的自定义属性的ID
    fa_ym = 0
    fa_mu = 1
    fa_den = 2
    fa_h = 3

    mesh = layered_triangles(x_min, x_max, 50, y_min, y_max, 60, as_mesh=True)
    assert isinstance(mesh, Mesh3)

    for face in mesh.faces:
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

    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        x, y = face.pos[:2]
        if abs(x) < 0.2 and abs(y) < 0.2:
            alg_xy.add_face_pressure(model, mesh, face.index, pressure=1e6, thick=1.0)

    solver = ConjugateGradientSolver(tolerance=1.0e-30)
    model.iterate(dt=1, solver=solver)

    def on_figure(fig):
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
