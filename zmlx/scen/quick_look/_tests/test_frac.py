"""测试裂缝功能 — 多条裂缝 + 多控压点 + 绘图."""
import os

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from zmlx.scen.quick_look import evaluate
from zmlx import point_distance


def main():
    frac_segs = [
        ((0, 50), (100, 50), 1000),
        ((20, 20), (80, 80), 500),
        ((30, 10), (30, 90), 800),
    ]

    control_p = [
        (50, 50),
    ]

    dx = 2

    def get_p(x, y, z):
        for item in control_p:
            if point_distance(item, [x, y]) < dx * 1.5:
                return 5e6
        return 10e6

    r = evaluate(
        x_range=(0, 100), y_range=(0, 100),
        dx=dx,
        p=get_p,
        perm=1e-14,
        control_p=control_p,
        time_forward=3600*5,
        step_max=50,
        frac_segs=frac_segs,
    )

    print(f"网格: {len(r['x'])} cells")
    print(f"迭代步数: {r['n_step']}")
    print(f"压力范围: {r['p'].min() / 1e6:.2f} ~ {r['p'].max() / 1e6:.2f} MPa")

    if plt is not None:
        fig, ax = plt.subplots()
        tcf = ax.tricontourf(r['x'], r['y'], r['p'] / 1e6, levels=20, cmap='viridis')
        fig.colorbar(tcf, ax=ax, label='Pressure (MPa)')

        # 绘制裂缝
        colors = ['red', 'orange', 'cyan']
        for i, seg in enumerate(frac_segs):
            (x0, y0), (x1, y1) = seg[0], seg[1]
            ax.plot([x0, x1], [y0, y1], color=colors[i % len(colors)],
                    linewidth=2, label=f'frac x{seg[2]}')

        # 绘制控压点
        cp_x = [p[0] for p in control_p]
        cp_y = [p[1] for p in control_p]
        ax.scatter(cp_x, cp_y, marker='s', c='white', edgecolors='black',
                   s=60, zorder=5, label='control_p')

        ax.legend(fontsize=7)
        ax.set_title(f'Fracture + Control Points  n_step={r["n_step"]}')
        ax.set_xlabel('x (m)')
        ax.set_ylabel('y (m)')
        ax.set_aspect('equal')
        fname = os.path.join(os.path.dirname(__file__), 'test_frac.png')
        fig.savefig(fname, dpi=150)
        print(f'图片: {fname}')
        plt.close(fig)

    return r


if __name__ == '__main__':
    main()
