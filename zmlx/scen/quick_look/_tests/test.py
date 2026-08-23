"""测试: 2D 单相流压力评估 + 绘图."""

import os

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from zmlx.scen.quick_look import evaluate


def test():
    r = evaluate(
        x_range=(0, 100), y_range=(0, 100),
        dx=1,
        p=lambda x, y, z: 15e6 if x < 50 else 5e6,
        perm=1e-14,
        control_p=[
            (0, 0),
            (90, 80),
        ],
        time_forward=3600 * 24 * 1000,
        step_max=50,
    )

    print(f"网格: {len(r['x'])} cells")
    print(f"迭代步数: {r['n_step']}")
    print(f"压力范围: {r['p'].min() / 1e6:.2f} ~ {r['p'].max() / 1e6:.2f} MPa")

    # 绘图
    fig, ax = plt.subplots()
    tcf = ax.tricontourf(r['x'], r['y'], r['p'] / 1e6, levels=20, cmap='viridis')
    fig.colorbar(tcf, ax=ax, label='Pressure (MPa)')
    ax.set_title(f'Pressure  n_step={r["n_step"]}')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_aspect('equal')
    fname = os.path.join(os.path.dirname(__file__), 'test_pressure.png')
    fig.savefig(fname, dpi=150)
    print(f'图片: {fname}')
    plt.close(fig)

    return r


if __name__ == '__main__':
    test()
