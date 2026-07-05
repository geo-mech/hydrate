#  'C3D4四面体单元应变验证：悬臂梁(L=4,H=1,W=0.5)，左侧固定，右上角y负方向力'

from zmlx.exts import Mesh3
from zmlx.fem.xyz import FemModel
from zmlx.fem.elements.c3d4 import calc_strain
import numpy as np


def create_mesh():
    """
    创建悬臂梁mesh (L=4, H=1, W=0.5, Nx=20, Ny=4, Nz=2)，每格5个四面体
    """
    Lx, Ly, Lz = 4.0, 1.0, 0.5
    Nx, Ny, Nz = 20, 4, 2
    dx, dy, dz = Lx / Nx, Ly / Ny, Lz / Nz

    mesh = Mesh3()
    nodes = []
    for k in range(Nz + 1):
        for j in range(Ny + 1):
            for i in range(Nx + 1):
                nodes.append(mesh.add_node(i * dx, j * dy, k * dz))

    def _node(ii, jj, kk):
        return nodes[kk * (Nx + 1) * (Ny + 1) + jj * (Nx + 1) + ii]

    def _link(a, b):
        return mesh.add_link([a, b])

    def _tri(a, b, c):
        return mesh.add_face([_link(a, b), _link(b, c), _link(c, a)])

    def _tet(a, b, c, d):
        mesh.add_body([_tri(a, b, c), _tri(a, b, d), _tri(b, c, d), _tri(c, a, d)])

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                n0 = _node(i, j, k)
                n1 = _node(i + 1, j, k)
                n2 = _node(i + 1, j + 1, k)
                n3 = _node(i, j + 1, k)
                n4 = _node(i, j, k + 1)
                n5 = _node(i + 1, j, k + 1)
                n6 = _node(i + 1, j + 1, k + 1)
                n7 = _node(i, j + 1, k + 1)
                _tet(n0, n1, n2, n6)
                _tet(n0, n2, n3, n6)
                _tet(n0, n3, n7, n6)
                _tet(n0, n7, n4, n6)
                _tet(n0, n4, n5, n6)

    return mesh


def _create(mesh: Mesh3):
    """
    根据mesh创建模型：左侧面固定，右上角中点y负方向力
    """
    model = FemModel()
    model.set_mesh(mesh, body_density=[1.0] * mesh.body_number,
                   body_ym=[1.0] * mesh.body_number, body_mu=[0.2] * mesh.body_number)
    for node in mesh.nodes:
        if abs(node.pos[0]) < 1e-6:
            i = node.index
            for d in range(3):
                model.set_mass(node_id=i, dim=d, value=1e20)

    x_max = max(n.pos[0] for n in mesh.nodes)
    y_max = max(n.pos[1] for n in mesh.nodes)
    z_mid = 0.5 * (min(n.pos[2] for n in mesh.nodes) + max(n.pos[2] for n in mesh.nodes))
    target = None
    min_dist = 1e100
    for node in mesh.nodes:
        d = abs(node.pos[0] - x_max) + abs(node.pos[1] - y_max) + abs(node.pos[2] - z_mid)
        if d < min_dist:
            min_dist = d
            target = node.index
    model.set_force(node_id=target, dim=1, value=-0.0001)
    return model


def _surface_faces_3d(mesh, model, eps):
    """通过节点 Delaunay 三角剖分重建外表面面片"""
    from scipy.spatial import Delaunay
    import matplotlib.pyplot as plt

    dx, dy, dz = model.get_disp()
    pos = np.array([n.pos for n in mesh.nodes])
    disp = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    vmin, vmax = disp.min(), disp.max()
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.cm.jet

    surfaces_def = [
        (0, pos[:, 0].min()), (0, pos[:, 0].max()),
        (1, pos[:, 1].min()), (1, pos[:, 1].max()),
        (2, pos[:, 2].min()), (2, pos[:, 2].max()),
    ]

    patches = []
    colors = []
    for axis, target in surfaces_def:
        idx = [i for i in range(mesh.node_number) if abs(pos[i, axis] - target) < eps]
        if len(idx) < 3:
            continue
        idx = np.array(idx)
        a, b = [d for d in range(3) if d != axis]
        proj = np.column_stack([pos[idx, a], pos[idx, b]])
        tri = Delaunay(proj)
        for s in tri.simplices:
            vi = idx[s]
            verts = [[pos[i, 0] + dx[i], pos[i, 1] + dy[i], pos[i, 2] + dz[i]] for i in vi]
            patches.append(verts)
            colors.append(cmap(norm(disp[vi].mean())))

    return patches, colors, norm, cmap


def _add_midplane_edges(ax, mesh, mask):
    drawn = set()
    for face in mesh.faces:
        for link in face.links:
            if link.index in drawn:
                continue
            drawn.add(link.index)
            n0, n1 = link.nodes[0], link.nodes[1]
            if not (mask[n0.index] and mask[n1.index]):
                continue
            ax.plot([n0.pos[0], n1.pos[0]],
                    [n0.pos[1], n1.pos[1]],
                    'k-', linewidth=0.3, alpha=0.5)


def _show(model: FemModel):
    from zmlx.plt import add_tricontourf, plot_on_figure

    mesh = model.get_mesh()
    dx, dy, dz = model.get_disp()
    x, y, z = model.get_pos()

    # 中平面位移云图
    z_all = np.array([node.pos[2] for node in mesh.nodes])
    z_mid = 0.5 * (z_all.min() + z_all.max())
    eps_z = (z_all.max() - z_all.min()) * 0.01
    mask = np.abs(z - z_mid) < eps_z
    vx = x[mask]
    vy = y[mask]
    dx_n = dx[mask]
    dy_n = dy[mask]

    def on_figure1(figure):
        from zmlx.plt import add_axes2
        ax = add_axes2(figure, nrows=2, ncols=1, index=1, title='displacement x',
                        xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dx_n, cbar={'label': 'dx'})
        _add_midplane_edges(ax, mesh, mask)
        ax = add_axes2(figure, nrows=2, ncols=1, index=2, title='displacement y',
                        xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dy_n, cbar={'label': 'dy'})
        _add_midplane_edges(ax, mesh, mask)
        figure.tight_layout()

    plot_on_figure(on_figure1, caption='C3D4 mid-plane')

    # 3D 悬臂梁表面贴图
    pos = np.array([n.pos for n in mesh.nodes])
    xmin, xmax = pos[:, 0].min(), pos[:, 0].max()
    ymin, ymax = pos[:, 1].min(), pos[:, 1].max()
    zmin, zmax = pos[:, 2].min(), pos[:, 2].max()
    eps = (xmax - xmin + ymax - ymin + zmax - zmin) * 1e-3

    patches, colors, norm, cmap = _surface_faces_3d(mesh, model, eps)
    if patches:

        def on_figure3(figure):
            import matplotlib.pyplot as plt
            from matplotlib.ticker import MaxNLocator
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection
            ax = figure.add_subplot(111, projection='3d',
                                     xlabel='$x$', ylabel='$y$', zlabel='$z$')
            ax.set_title('C3D4: 3D surface total displacement')

            pc = Poly3DCollection(patches, facecolors=colors,
                                  edgecolors='k', linewidths=0.05, alpha=0.9)
            ax.add_collection3d(pc)

            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.set_zlim(zmin, zmax)
            ax.set_box_aspect([xmax - xmin, ymax - ymin, zmax - zmin])

            for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
                axis.set_major_locator(MaxNLocator(nbins=5))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
            ax.zaxis.set_major_locator(MaxNLocator(nbins=3))

            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='$|u|$', shrink=0.6, pad=0.15)

        plot_on_figure(on_figure3, caption='C3D4 3D surface')

    # 理论解对比：中平面顶边 y 位移
    z_all = np.array([node.pos[2] for node in mesh.nodes])
    z_mid = 0.5 * (z_all.min() + z_all.max())
    top_nodes = sorted(
        [n for n in mesh.nodes
         if abs(n.pos[1] - 1.0) < 1e-6 and abs(n.pos[2] - z_mid) < eps_z],
        key=lambda n: n.pos[0]
    )
    if top_nodes:
        x_fem = np.array([n.pos[0] for n in top_nodes])
        dy_fem = np.array([dy[n.index] for n in top_nodes])

        L, H = 4.0, 1.0
        I = 0.5 / 12
        F = -0.0001
        x_theory = np.linspace(0, L, 100)
        dy_theory = F * x_theory ** 2 * (3 * L - x_theory) / (6 * 1.0 * I)

        def on_figure_theory(figure):
            from zmlx.plt import add_axes2
            ax = add_axes2(figure, nrows=1, ncols=1, index=1,
                            title='Mid-plane top edge y-displacement vs Euler-Bernoulli',
                            xlabel='x', ylabel='dy')
            ax.plot(x_fem, dy_fem, 'ro-', label='FEM', markersize=4)
            ax.plot(x_theory, dy_theory, 'b-', label='Euler-Bernoulli')
            ax.legend()
            figure.tight_layout()

        plot_on_figure(on_figure_theory, caption='Theory comparison')


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
    print(f'Mesh: {mesh.node_number} nodes, {mesh.body_number} bodies')
    model = _create(mesh)
    gui.execute(func=_solve, args=[model],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    _test()
