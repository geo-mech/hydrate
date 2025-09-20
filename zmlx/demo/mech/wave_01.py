# ** desc = '动态的有限元计算：添加初始的冲击速度，计算应力波的传递过程'

from zmlx import *
from zmlx.data import mesh_c10000 as data
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def main():
    mesh = data.get_mesh3(z=0)
    assert isinstance(mesh, Mesh3)

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

    solver = ConjugateGradientSolver(tolerance=1.0e-20)

    def on_figure(fig):
        x1 = np.array([model.get_pos(idx * 2) for idx in range(mesh.node_number)])
        y1 = np.array([model.get_pos(idx * 2 + 1) for idx in range(mesh.node_number)])
        dx = x1 - x0
        dy = y1 - y0
        dist = np.sqrt(dx ** 2 + dy ** 2)
        add_axes2(
            fig, add_tricontourf, x1, y1, dist,
            cbar=dict(label='disp/m'), title='位移',
            aspect='equal', xlabel='x/m', ylabel='y/m'
        )
        fig.tight_layout()

    for i in range(300):
        gui.break_point()
        model.iterate(dt=0.000001, solver=solver)
        if i % 10 == 0:
            print(i)
            plot(on_figure, caption='位移场')


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
