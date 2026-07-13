#  '平面应力T6单元应变验证：悬臂梁(L=4,H=1)，左侧固定，右上角y负方向力'

from zmlx.fem.xy import Mesh3
from zmlx.fem.dyn import create_dyn
from zmlx.fem.elements.planar_stress_t6 import calc_stiffness
from zmlx.fem.mesh_utils import enrich_with_mid_nodes
import numpy as np


def create_mesh():
    """
    创建悬臂梁mesh (L=4, H=1, Nx=16, Ny=4)，每格两个CST三角形，
    然后使用enrich_with_mid_nodes转换为6节点T6单元
    """
    Lx, Ly = 4.0, 1.0
    Nx, Ny = 16, 4
    dx, dy = Lx / Nx, Ly / Ny

    # 创建角节点坐标（与test_3d完全相同）
    coords = []
    for j in range(Ny + 1):
        for i in range(Nx + 1):
            coords.append((i * dx, j * dy))

    def _node(i, j):
        return j * (Nx + 1) + i

    # 构建角节点单元（与test_3d的CST三角形连通性完全相同）
    corner_elements = []
    for j in range(Ny):
        for i in range(Nx):
            n0, n1 = _node(i, j), _node(i + 1, j)
            n2, n3 = _node(i, j + 1), _node(i + 1, j + 1)
            corner_elements.append([n0, n1, n2])
            corner_elements.append([n1, n3, n2])

    # 补全边中点，得到6节点T6单元
    enriched, coords, _ = enrich_with_mid_nodes(corner_elements, coords, 't6')

    return coords, enriched


class _Model:
    """
    有限元模型（Mesh3不支持6节点面，直接使用DynSys组装）
    """

    def __init__(self, coords, enriched, E=1.0, mu=0.2, thickness=1.0, density=1.0):
        nn = len(coords)
        ndof = nn * 2

        # 质量
        masses = [0.0] * ndof
        for elem in enriched:
            c0 = np.array(coords[elem[0]], dtype=float)
            c1 = np.array(coords[elem[1]], dtype=float)
            c2 = np.array(coords[elem[2]], dtype=float)
            v1, v2 = c1 - c0, c2 - c0
            area = 0.5 * abs(v1[0] * v2[1] - v1[1] * v2[0])
            m_per_node = area * thickness * density / len(elem)
            for ni in elem:
                masses[ni * 2] += m_per_node
                masses[ni * 2 + 1] += m_per_node

        # 自由度单元
        dof_elements = []
        for elem in enriched:
            dofs = []
            for ni in elem:
                dofs.append(ni * 2)
                dofs.append(ni * 2 + 1)
            dof_elements.append(dofs)

        # 刚度矩阵
        matrices = []
        for elem in enriched:
            nodes_xy = [coords[ni] for ni in elem]
            K = calc_stiffness(nodes_xy, E, mu, thickness)
            matrices.append(K)

        self._dyn = create_dyn(masses, dof_elements, matrices)
        self._node_x = np.array([c[0] for c in coords])
        self._node_y = np.array([c[1] for c in coords])
        self._coords = coords
        self._enriched = enriched

    def get_pos(self):
        return np.copy(self._node_x), np.copy(self._node_y)

    def get_disp(self):
        buffer = np.zeros(self._dyn.size, dtype=np.float64)
        self._dyn.write_pos(buffer)
        return buffer[0::2], buffer[1::2]

    def iterate(self, dt):
        return self._dyn.iterate(dt)

    def set_mass(self, node_id, dim, value):
        self._dyn.set_mass(node_id * 2 + dim, value)

    def set_force(self, node_id, dim, value):
        self._dyn.get_p2f(node_id * 2 + dim).c = value


def _create(coords, enriched):
    """
    根据mesh创建模型：左侧固定，右上角y负方向力
    """
    model = _Model(coords, enriched, E=1.0, mu=0.2, thickness=1.0, density=1.0)
    for i, (x, y) in enumerate(coords):
        if abs(x) < 1e-6:
            model.set_mass(node_id=i, dim=0, value=1e20)
            model.set_mass(node_id=i, dim=1, value=1e20)

    max_x = max(c[0] for c in coords)
    max_y = max(c[1] for c in coords)
    target = None
    min_dist = 1e100
    for i, (x, y) in enumerate(coords):
        d = abs(x - max_x) + abs(y - max_y)
        if d < min_dist:
            min_dist = d
            target = i
    model.set_force(node_id=target, dim=1, value=-0.001)
    return model


def _draw_mesh(ax, enriched, vx, vy, n_corner=3):
    """
    绘制网格：仅绘制角节点之间的连线，边中点用散点示意
    """
    corner_edges = set()
    mid_nodes = set()
    for elem in enriched:
        # 角节点之间的边
        for i in range(n_corner):
            a, b = elem[i], elem[(i + 1) % n_corner]
            key = (min(a, b), max(a, b))
            corner_edges.add(key)
        # 边中点
        for i in range(n_corner, len(elem)):
            mid_nodes.add(elem[i])
    for a, b in corner_edges:
        ax.plot([vx[a], vx[b]], [vy[a], vy[b]],
                'k-', linewidth=0.3, alpha=0.5)
    if mid_nodes:
        mi = list(mid_nodes)
        ax.plot([vx[i] for i in mi], [vy[i] for i in mi],
                'ko', markersize=1.5, alpha=0.6)


def _show(model: _Model):
    from zmlx.plt import add_tricontourf, plot_on_figure
    dx, dy = model.get_disp()
    vx, vy = model.get_pos()
    enriched = model._enriched
    coords = model._coords

    def on_figure(figure):
        from zmlx.plt import add_axes2
        ax = add_axes2(figure, nrows=2, ncols=1, index=1, title='displacement x',
                        xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dx, cbar={'label': 'dx'})
        _draw_mesh(ax, enriched, vx, vy, n_corner=3)
        ax = add_axes2(figure, nrows=2, ncols=1, index=2, title='displacement y',
                        xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dy, cbar={'label': 'dy'})
        _draw_mesh(ax, enriched, vx, vy, n_corner=3)
        figure.tight_layout()

    plot_on_figure(on_figure, caption='PlanarStressT6')

    # 理论解对比
    def on_figure_theory(figure):
        from zmlx.plt import add_axes2
        top_nodes = sorted(
            [i for i, (x, y) in enumerate(coords) if abs(y - 1.0) < 1e-6],
            key=lambda i: coords[i][0]
        )
        x_fem = np.array([coords[i][0] for i in top_nodes])
        dy_fem = np.array([dy[i] for i in top_nodes])

        L, H = 4.0, 1.0
        I = 1.0 / 12  # 截面惯性矩
        F = -0.001  # 载荷
        G = 1.0 / (2 * (1 + 0.2))  # 剪切模量
        k = 5.0 / 6.0  # 矩形截面剪切系数
        A = H * 1.0  # 截面面积（厚度=1）
        x_theory = np.linspace(0, L, 100)
        # 铁木辛柯梁理论：挠度 = 弯曲挠度 + 剪切挠度
        dy_bend = F * x_theory ** 2 * (3 * L - x_theory) / (6 * 1.0 * I)  # 弯曲项
        dy_shear = F * x_theory / (k * A * G)  # 剪切项
        dy_theory = dy_bend + dy_shear

        ax = add_axes2(figure, nrows=1, ncols=1, index=1,
                        title='Top edge y-displacement vs Timoshenko',
                        xlabel='x', ylabel='dy')
        ax.plot(x_fem, dy_fem, 'ro-', label='FEM', markersize=4)
        ax.plot(x_theory, dy_theory, 'b-', label='Timoshenko')
        ax.legend()
        figure.tight_layout()

    plot_on_figure(on_figure_theory, caption='Theory comparison')


def _solve(model: _Model):
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
    coords, enriched = create_mesh()
    model = _create(coords, enriched)
    gui.execute(func=_solve, args=[model],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    _test()
