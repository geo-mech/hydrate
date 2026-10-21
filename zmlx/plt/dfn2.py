"""dfn2 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.plt.on_ui import show_dfn2

warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)


def test():
    from zmlx.geometries.dfn2 import dfn2
    fractures = dfn2(
        lr=[10, 100], ar=[0, 1], p21=0.2, xr=[-100, 100],
        yr=[-100, 100], l_min=2)
    show_dfn2(fractures)


if __name__ == '__main__':
    test()
