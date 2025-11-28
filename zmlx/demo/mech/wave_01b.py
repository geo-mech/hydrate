# ** desc = '动态的有限元计算：添加初始的冲击速度，计算应力波的传递过程'

from zmlx import *
from zmlx.data import mesh_c10000 as data
from zmlx.fem import xy
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def main():
    mesh = data.get_mesh3(z=0)
    assert isinstance(mesh, Mesh3)

    face_n = mesh.face_number

    model = xy.create_dyn(
        mesh=mesh, face_ym=[1.0e9] * face_n, face_mu=[0.2] * face_n,
        face_density=[1000.0] * face_n,
        face_thickness=[1.0] * face_n
    )

    assert isinstance(model, DynSys)

    x0 = np.array([node.pos[0] for node in mesh.nodes])
    y0 = np.array([node.pos[1] for node in mesh.nodes])

    for node in mesh.nodes:
        assert isinstance(node, Mesh3.Node)
        x, y = node.pos[:2]
        xx = 0.16
        if xx - 0.05 < x < xx + 0.05 and -0.3 < y < 0.3:
            v = -1 if x < xx else 1
        else:
            v = 0
        model.set_vel(node.index * 2, v)

    def on_figure(fig):

        dx = np.array([model.get_pos(i * 2) for i in range(mesh.node_number)])
        dy = np.array([model.get_pos(i * 2 + 1) for i in range(mesh.node_number)])
        dist = np.sqrt(dx ** 2 + dy ** 2)
        add_axes2(
            fig, add_tricontourf, x0, y0, dist,
            cbar=dict(label='disp/m'), title='位移',
            aspect='equal', xlabel='x/m', ylabel='y/m'
        )
        fig.tight_layout()

    for i in range(300):
        gui.break_point()
        model.iterate(dt=0.000001)
        if i % 10 == 0:
            print(i)
            plot(on_figure, caption='位移场')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
