# ** desc = 'Truss2杆单元理论验证：静定悬臂桁架(L=3,H=1)，方法of joints + 虚功原理'

from zmlx.fem.xy import FemModel, Mesh3, LinkType
from zmlx.fem.elements.truss2 import calc_strain
import numpy as np

# 模型参数
Lx = 3.0      # 悬臂梁长度 (3跨)
Ly = 1.0      # 悬臂梁高度
Nx = 3        # 跨数
E = 1.0       # 杨氏模量
A = 0.1       # 杆截面积
F = -0.001    # 悬臂端底节点-y方向力


def create_mesh():
    """
    3跨静定悬臂桁架: 8节点, 13杆, 3支座约束 (r=3)
    顶弦: T0..T3, 底弦: B0..B3
    斜杆每跨左下→右上: B0-T1, B1-T2, B2-T3
    """
    mesh = Mesh3()
    dx, dy = Lx / Nx, Ly

    nodes = []
    for i in range(Nx + 1):
        nodes.append(mesh.add_node(i * dx, dy, 0))
    for i in range(Nx + 1):
        nodes.append(mesh.add_node(i * dx, 0, 0))

    def T(i):
        return nodes[i]

    def B(i):
        return nodes[Nx + 1 + i]

    # 杆件 (13根) — 存储以备面使用
    bot_chords = [mesh.add_link([B(i), B(i + 1)]) for i in range(Nx)]
    top_chords = [mesh.add_link([T(i), T(i + 1)]) for i in range(Nx)]
    verts = [mesh.add_link([T(i), B(i)]) for i in range(Nx + 1)]
    diags = [mesh.add_link([B(i), T(i + 1)]) for i in range(Nx)]

    # 三角面仅用于质量计算 (每跨2个)
    for i in range(Nx):
        # 三角形 B(i)-B(i+1)-T(i+1): links B(i)-B(i+1), B(i+1)-T(i+1), T(i+1)-B(i)
        mesh.add_face([bot_chords[i], verts[i + 1], diags[i]])
        # 三角形 B(i)-T(i)-T(i+1): links B(i)-T(i), T(i)-T(i+1), T(i+1)-B(i)
        mesh.add_face([verts[i], top_chords[i], diags[i]])

    return mesh


def _create(mesh: Mesh3):
    """
    支座: B0铰支(r=2) + T0仅约束x(r=1) → 静定
    荷载: B3处-y方向力
    """
    model = FemModel()
    model.set_mesh(
        mesh,
        face_density=[1.0] * mesh.face_number,
        face_thickness=[1.0] * mesh.face_number,
        link_types=[LinkType.Truss2] * mesh.link_number,
        link_area=[A] * mesh.link_number,
        link_ym=[E] * mesh.link_number,
    )

    # B0 (0,0): 铰支 — 固定 x 和 y
    for node in mesh.nodes:
        if abs(node.pos[0]) < 1e-6 and abs(node.pos[1]) < 1e-6:
            model.set_mass(node_id=node.index, dim=0, value=1e20)
            model.set_mass(node_id=node.index, dim=1, value=1e20)

    # T0 (0,1): 仅约束 x (滚动支座)
    for node in mesh.nodes:
        if abs(node.pos[0]) < 1e-6 and abs(node.pos[1] - Ly) < 1e-6:
            model.set_mass(node_id=node.index, dim=0, value=1e20)

    # B3 (Lx,0): 加载点 — 施加 -y 方向力
    for node in mesh.nodes:
        if abs(node.pos[0] - Lx) < 1e-6 and abs(node.pos[1]) < 1e-6:
            model.set_force(node_id=node.index, dim=1, value=F)
            break

    return model


def _compute_theory():
    """
    方法 of joints + 虚功原理求理论解

    节点自由度数: 2*j = 16, 未知数: 13杆轴力 + 3支座反力 = 16
    全局平衡方程: C * N + S * R = -P

    其中:
      C[16×13]: 杆 k (方向 a→b, 余弦 cx,cy) 对节点自由度的贡献
        杆端a: +cx, +cy  (杆拉节点a沿杆方向)
        杆端b: -cx, -cy  (杆拉节点b反向)
      S[16×3]: 支座反力对应自由度的单位向量 (reaction in +coord direction)
      P[16×1]: 外荷载 (+coord direction)

    方程: Σ(bar_forces) + support_reactions + P = 0
         C*N + S*R = -P

    虚功原理求B3_y方向位移:
      n_k = +y方向单位虚荷载下各杆内力
      δ_B3y = Σ(n_k * N_k * L_k) / (E * A)
    """
    j = 2 * (Nx + 1)
    m = 4 * Nx + 1
    dofs = 2 * j

    top_start, bot_start = 0, Nx + 1
    coords = {}
    for i in range(Nx + 1):
        coords[top_start + i] = np.array([i * Lx / Nx, Ly], dtype=float)
        coords[bot_start + i] = np.array([i * Lx / Nx, 0.0], dtype=float)

    def dof_idx(node_i, dim):
        return 2 * node_i + dim

    # 杆件定义: (node_a, node_b) — 方向 a→b
    bars = []
    for i in range(Nx):
        bars.append((bot_start + i, bot_start + i + 1))  # 底弦 (左→右)
    for i in range(Nx):
        bars.append((top_start + i, top_start + i + 1))  # 顶弦 (左→右)
    for i in range(Nx + 1):
        bars.append((top_start + i, bot_start + i))      # 竖杆 (上→下)
    for i in range(Nx):
        bars.append((bot_start + i, top_start + i + 1))  # 斜杆 (左下→右上)

    bar_lengths = []
    bar_cosines = []

    for a_idx, b_idx in bars:
        va, vb = coords[a_idx], coords[b_idx]
        vec = vb - va
        length = np.linalg.norm(vec)
        bar_lengths.append(length)
        bar_cosines.append(vec / length)

    # 构建 C[16×13]
    # 杆端a: +cx,杆端b: -cx (杆内力的 + 方向为 a→b 拉伸)
    C = np.zeros((dofs, m))
    for k, ((a_idx, b_idx), (cx, cy)) in enumerate(zip(bars, bar_cosines)):
        C[dof_idx(a_idx, 0), k] = cx
        C[dof_idx(a_idx, 1), k] = cy
        C[dof_idx(b_idx, 0), k] = -cx
        C[dof_idx(b_idx, 1), k] = -cy

    # 支座反力: B0 铰支 (r=2: x,y), T0 仅约束 x (r=1)
    supports = [
        (bot_start, 0),
        (bot_start, 1),
        (top_start, 0),
    ]
    S = np.zeros((dofs, len(supports)))
    for s_i, (node_i, dim) in enumerate(supports):
        S[dof_idx(node_i, dim), s_i] = 1.0

    # 外荷载: B3 处 -y 方向力
    P = np.zeros(dofs)
    load_node = bot_start + Nx
    P[dof_idx(load_node, 1)] = F  # F = -0.001

    # 解 C*N + S*R = -P
    CS = np.hstack([C, S])
    sol = np.linalg.solve(CS, -P)
    N_real = sol[:m]
    R = sol[m:]

    # 虚功原理求 B3 y 位移 (+y 方向单位荷载)
    P_virtual = np.zeros(dofs)
    P_virtual[dof_idx(load_node, 1)] = 1.0  # 单位力在 +y 方向
    sol_virtual = np.linalg.solve(CS, -P_virtual)
    n_virtual = sol_virtual[:m]

    # δ_B3y = Σ(n_k * N_k * L_k) / (E * A)
    delta_B3y = np.sum(n_virtual * N_real * np.array(bar_lengths)) / (E * A)

    return N_real, n_virtual, bar_lengths, bars, delta_B3y, R


def _add_truss_edges(ax, mesh, vx, vy, **kwargs):
    """绘制所有杆单元"""
    defaults = {'color': 'k', 'linewidth': 0.5, 'alpha': 0.5}
    defaults.update(kwargs)
    drawn = set()
    for link in mesh.links:
        if link.index in drawn:
            continue
        drawn.add(link.index)
        a, b = link.nodes[0], link.nodes[1]
        ax.plot([vx[a.index], vx[b.index]],
                [vy[a.index], vy[b.index]],
                defaults.pop('color'), **defaults)


def _show(model: FemModel):
    from zmlx.plt import add_tricontourf, plot_on_figure
    mesh = model.get_mesh()
    dx, dy = model.get_disp()
    vx, vy = model.get_pos()

    # 理论解
    N_theory, n_virtual, bar_lengths, theory_bars, delta_theory, R = _compute_theory()

    # Figure 1: 位移云图
    def on_figure1(figure):
        from zmlx.plt import add_axes2
        ax = add_axes2(figure, nrows=2, ncols=1, index=1, title='displacement x',
                       xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dx, cbar={'label': 'dx'})
        _add_truss_edges(ax, mesh, vx, vy)

        ax = add_axes2(figure, nrows=2, ncols=1, index=2, title='displacement y',
                       xlabel='x', ylabel='y', aspect='equal')
        add_tricontourf(ax, vx, vy, dy, cbar={'label': 'dy'})
        _add_truss_edges(ax, mesh, vx, vy)
        figure.tight_layout()

    plot_on_figure(on_figure1, caption='Truss2 displacement')

    # Figure 2: 杆单元轴向应变 (FEM)
    strains, lx0, ly0, lx1, ly1 = [], [], [], [], []
    for link in mesh.links:
        a, b = link.nodes[0], link.nodes[1]
        nodes_pos = [a.pos[:2], b.pos[:2]]
        disp = [dx[a.index], dy[a.index], dx[b.index], dy[b.index]]
        eps = calc_strain(nodes_pos, np.array(disp))
        strains.append(eps)
        lx0.append(a.pos[0])
        ly0.append(a.pos[1])
        lx1.append(b.pos[0])
        ly1.append(b.pos[1])

    strains = np.array(strains)

    def on_figure2(figure):
        from zmlx.plt import add_axes2
        ax = add_axes2(figure, nrows=1, ncols=1, index=1, title='Truss2 axial strain',
                       xlabel='x', ylabel='y', aspect='equal')
        vmin, vmax = strains.min(), strains.max()
        rng = max(abs(vmin), abs(vmax), 1e-10)
        for i in range(len(strains)):
            eps = strains[i]
            t = max(0.0, min(1.0, (eps + rng) / (2 * rng)))
            color = (t, 0.0, 1.0 - t)
            ax.plot([lx0[i], lx1[i]], [ly0[i], ly1[i]],
                    color=color, linewidth=3, marker='o', markersize=6)
            mx, my = (lx0[i] + lx1[i]) / 2, (ly0[i] + ly1[i]) / 2
            ax.text(mx, my, f'{eps:.6f}', fontsize=7, ha='center', va='bottom')
        figure.tight_layout()

    plot_on_figure(on_figure2, caption='Truss2 axial strain')

    # Figure 3: 理论解对比 — 底弦各节点竖向位移 vs 虚功原理
    bot_nodes = sorted(
        [n for n in mesh.nodes if abs(n.pos[1]) < 1e-6],
        key=lambda n: n.pos[0]
    )
    x_fem = np.array([n.pos[0] for n in bot_nodes])
    dy_fem = np.array([dy[n.index] for n in bot_nodes])

    # 虚功原理求每个底弦节点的理论位移
    j = 2 * (Nx + 1)
    m = 4 * Nx + 1
    dofs = 2 * j
    top_start, bot_start = 0, Nx + 1

    def dof_idx(node_i, dim):
        return 2 * node_i + dim

    bars = []
    for i in range(Nx):
        bars.append((bot_start + i, bot_start + i + 1))
    for i in range(Nx):
        bars.append((top_start + i, top_start + i + 1))
    for i in range(Nx + 1):
        bars.append((top_start + i, bot_start + i))
    for i in range(Nx):
        bars.append((bot_start + i, top_start + i + 1))

    coords = {}
    for i in range(Nx + 1):
        coords[top_start + i] = np.array([i * Lx / Nx, Ly], dtype=float)
        coords[bot_start + i] = np.array([i * Lx / Nx, 0.0], dtype=float)

    bar_lens = []
    bar_cos = []
    for a_idx, b_idx in bars:
        vec = coords[b_idx] - coords[a_idx]
        bar_lens.append(np.linalg.norm(vec))
        bar_cos.append(vec / bar_lens[-1])

    C = np.zeros((dofs, m))
    for k, ((a_idx, b_idx), (cx, cy)) in enumerate(zip(bars, bar_cos)):
        C[dof_idx(a_idx, 0), k] = cx
        C[dof_idx(a_idx, 1), k] = cy
        C[dof_idx(b_idx, 0), k] = -cx
        C[dof_idx(b_idx, 1), k] = -cy

    supports = [(bot_start, 0), (bot_start, 1), (top_start, 0)]
    S = np.zeros((dofs, len(supports)))
    for s_i, (node_i, dim) in enumerate(supports):
        S[dof_idx(node_i, dim), s_i] = 1.0

    CS = np.hstack([C, S])

    dy_theory = []
    for node in bot_nodes:
        P_v = np.zeros(dofs)
        P_v[dof_idx(node.index, 1)] = 1.0
        n_v = np.linalg.solve(CS, -P_v)[:m]
        dy_theory.append(np.sum(n_v * N_theory * np.array(bar_lens)) / (E * A))

    dy_theory = np.array(dy_theory)

    rel_err = 0.0
    for i in range(len(dy_theory)):
        if abs(dy_theory[i]) > 1e-10:
            rel_err = max(rel_err, abs(dy_fem[i] - dy_theory[i]) / abs(dy_theory[i]))

    def on_figure3(figure):
        from zmlx.plt import add_axes2
        ax = add_axes2(figure, nrows=1, ncols=1, index=1,
                       title='Bottom chord y-displacement: FEM vs Virtual Work',
                       xlabel='x', ylabel='dy')
        ax.plot(x_fem, dy_fem, 'ro-', label='FEM', markersize=6)
        ax.plot(x_fem, dy_theory, 'b-', label='Theory (virtual work)')
        ax.legend()
        ax.text(0.95, 0.05,
                f'max rel err = {rel_err:.2e}',
                transform=ax.transAxes, fontsize=10, ha='right',
                bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.5})
        figure.tight_layout()

    plot_on_figure(on_figure3, caption='Theory comparison')


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
