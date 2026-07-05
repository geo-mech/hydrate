# '平面应变CST单元应变验证（加密网格）：悬臂梁(L=4,H=1)，左侧固定，右上角y负方向力'

from zmlx.fem.xy import FemModel, Mesh3, FaceType
import numpy as np


def create_mesh():
    """
    创建悬臂梁mesh (L=4, H=1, Nx=64, Ny=16)，每格两个CST三角形
    """
    Lx, Ly = 4.0, 1.0
    Nx, Ny = 64, 16
    dx, dy = Lx / Nx, Ly / Ny

    mesh = Mesh3()
    nodes = []
    for j in range(Ny + 1):
        for i in range(Nx + 1):
            nodes.append(mesh.add_node(i * dx, j * dy, 0))

    def _node(i, j):
        return nodes[j * (Nx + 1) + i]

    for j in range(Ny):
        for i in range(Nx):
            n0, n1 = _node(i, j), _node(i + 1, j)
            n2, n3 = _node(i, j + 1), _node(i + 1, j + 1)
            mesh.add_face([
                mesh.add_link([n0, n1]),
                mesh.add_link([n1, n2]),
                mesh.add_link([n2, n0])
            ])
            mesh.add_face([
                mesh.add_link([n1, n3]),
                mesh.add_link([n3, n2]),
                mesh.add_link([n2, n1])
            ])

    return mesh


def _create(mesh: Mesh3):
    """
    根据mesh创建模型：左侧固定，右上角y负方向力
    """
    model = FemModel()
    model.set_mesh(
        mesh,
        face_density=[1.0] * mesh.face_number,
        face_thickness=[1.0] * mesh.face_number,
        face_ym=[1.0] * mesh.face_number,
        face_mu=[0.2] * mesh.face_number,
        face_types=[FaceType.PlanarStrainCST] * mesh.face_number,
    )
    for node in mesh.nodes:
        if abs(node.pos[0]) < 1e-6:
            model.set_mass(node_id=node.index, dim=0, value=1e20)
            model.set_mass(node_id=node.index, dim=1, value=1e20)

    max_x = max(n.pos[0] for n in mesh.nodes)
    max_y = max(n.pos[1] for n in mesh.nodes)
    target = None
    min_dist = 1e100
    for node in mesh.nodes:
        d = abs(node.pos[0] - max_x) + abs(node.pos[1] - max_y)
        if d < min_dist:
            min_dist = d
            target = node.index
    model.set_force(node_id=target, dim=1, value=-0.001)
    return model


def _add_mesh_edges(ax, mesh, vx, vy):
    drawn = set()
    for face in mesh.faces:
        for link in face.links:
            if link.index in drawn:
                continue
            drawn.add(link.index)
            n0, n1 = link.nodes[0], link.nodes[1]
            ax.plot([vx[n0.index], vx[n1.index]],
                    [vy[n0.index], vy[n1.index]],
                    'k-', linewidth=0.1, alpha=0.3)


def _show(model: FemModel):
    from zmlx.plt import add_tricontourf, plot_on_figure
    mesh = model.get_mesh()
    dx, dy = model.get_disp()
    vx, vy = model.get_pos()

    def on_figure(figure):
        from zmlx.plt import add_axes2
        ax = add_axes2(figure, nrows=2, ncols=1, index=1, title='displacement x',
                        xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dx, cbar={'label': 'dx'})
        _add_mesh_edges(ax, mesh, vx, vy)
        ax = add_axes2(figure, nrows=2, ncols=1, index=2, title='displacement y',
                        xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dy, cbar={'label': 'dy'})
        _add_mesh_edges(ax, mesh, vx, vy)
        figure.tight_layout()

    plot_on_figure(on_figure, caption='PlanarStrainCST (refined)')

    # 理论解对比
    def on_figure_theory(figure):
        from zmlx.plt import add_axes2
        top_nodes = sorted(
            [n for n in mesh.nodes if abs(n.pos[1] - 1.0) < 1e-6],
            key=lambda n: n.pos[0]
        )
        x_fem = np.array([n.pos[0] for n in top_nodes])
        dy_fem = np.array([dy[n.index] for n in top_nodes])

        L, H = 4.0, 1.0
        E_eff = 1.0 / (1 - 0.2 ** 2)
        I = 1.0 / 12
        F = -0.001
        x_theory = np.linspace(0, L, 100)
        dy_theory = F * x_theory ** 2 * (3 * L - x_theory) / (6 * E_eff * I)

        ax = add_axes2(figure, nrows=1, ncols=1, index=1,
                        title='Top edge y-displacement vs Euler-Bernoulli (refined)',
                        xlabel='x', ylabel='dy')
        ax.plot(x_fem, dy_fem, 'ro-', label='FEM', markersize=2)
        ax.plot(x_theory, dy_theory, 'b-', label='Euler-Bernoulli')
        ax.legend()
        figure.tight_layout()

    plot_on_figure(on_figure_theory, caption='Theory comparison (refined)')


def _solve(model: FemModel):
    """
    求解给定的模型
    """
    from zmlx import gui
    for step in range(10):
        gui.break_point()
        print(f'step = {step}')
        model.iterate(dt=1000)
        _show(model)


def _test(gui_mode=True, close_after_done=False):
    """
    主函数
    """
    from zmlx import gui
    mesh = create_mesh()
    model = _create(mesh)
    gui.execute(func=_solve, args=[model],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    _test()
