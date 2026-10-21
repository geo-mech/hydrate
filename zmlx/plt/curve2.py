"""
二维的曲线

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
from zmlx.plt.on_ui import show_xy as plot_xy

warn(
    'The module zmlx.plt.curve2 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import plot_xy`（即 show_xy）',
    DeprecationWarning, stacklevel=2)


def plotxy(*args, **kwargs):
    """已弃用（保留转发）：请直接用 ``from zmlx import plot_xy``（即 ``show_xy``）。"""
    warn(
        'zmlx.plt.curve2.plotxy 已弃用（remove after 2027-5-23）：'
        '请改用 plot_xy（即 show_xy，``from zmlx import plot_xy``）',
        DeprecationWarning,
        stacklevel=2,
        tag='zmlx.plt.curve2.plotxy')
    plot_xy(*args, **kwargs)


def test():
    import numpy as np
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    plot_xy(x, y, title='sin(x)', xlabel='x', ylabel='y',
            caption='sin(x)', gui_mode=True)


if __name__ == '__main__':
    test()
