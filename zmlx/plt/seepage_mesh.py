"""seepage mesh 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.plt.on_axes import add_seepage_mesh

# ⚠️ 不要写 `from zmlx.plt.on_axes import plot_on_axes`：
#    ``zmlx.plt.on_axes`` 既是**子包**、也是该子包里一个**同名函数**，属性查找
#    拿到的是子包模块，于是 ``plot_on_axes(...)`` 会变成
#    ``TypeError: 'module' object is not callable``。
from zmlx.plt.on_figure import plot_on_axes

warn(
    'The module zmlx.plt.seepage_mesh 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import add_seepage_mesh` / `from zmlx import plot_on_axes`',
    DeprecationWarning, stacklevel=2)


def test():
    """
    测试
    """
    from zmlx import create_cube
    import random
    import numpy as np

    mesh = create_cube(
        x=np.linspace(0, 10, 30),
        y=np.linspace(0, 20, 50),
        z=[-1, 1])

    for c in mesh.cells:
        c.vol = random.uniform(0.5, 5)
        x, y, z = c.pos
        z = np.sin(x / 5) * np.cos(y / 5) * 3
        c.pos = [x, y, z]

    plot_on_axes(add_seepage_mesh, mesh, dim=3,
                 cbar=dict(label='Volume', shrink=0.5),
                 gui_mode=True,
                 aspect='equal', xlabel='x', ylabel='y', zlabel='z', title=f'A Seepage Mesh'
                 )


if __name__ == '__main__':
    test()
