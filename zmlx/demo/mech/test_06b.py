# ** desc = '对于2m*2m的区域，在中间的一个小矩形区域内，添加流体压力'

from zmlx import *
from zmlx.fem import alg_xy, xy
from zmlx.mesh.triangle import layered_triangles
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def main():
    # 定义矩形区域的边界
    x_min = -1
    x_max = 1
    y_min = -1
    y_max = 1

    mesh = layered_triangles(x_min, x_max, 50, y_min, y_max, 60, as_mesh=True)
    assert isinstance(mesh, Mesh3)

    face_n = mesh.face_number

    model = xy.create_dyn(
        mesh=mesh, face_ym=[1.0e9] * face_n, face_mu=[0.2] * face_n,
        face_density=[1000.0] * face_n,
        face_thickness=[1.0] * face_n
    )

    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        x, y = face.pos[:2]
        if abs(x) < 0.2 and abs(y) < 0.2:
            alg_xy.add_face_pressure(model, mesh, face.index, pressure=1e6, thick=1.0)

    model.iterate(dt=1)

    def on_figure(fig):
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
