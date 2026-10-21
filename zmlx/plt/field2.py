"""field2 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.plt.on_ui import show_field2

warn(
    'The module zmlx.plt.field2 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import show_field2`',
    DeprecationWarning, stacklevel=2)


def test():
    from zmlx.fluids.ch4 import create
    flu = create()
    show_field2(
        flu.den, xr=[4e6, 15e6], yr=[274, 290], caption='Density',
        cbar=dict(label='Density', title='Title', shrink=0.5),
        xlabel='Pressure / MPa', ylabel='Temperature',
        title='Density', cmap='coolwarm',
        x_times=1.0e-6
    )
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='Viscosity')


if __name__ == '__main__':
    from zmlx import gui

    gui.execute(test, close_after_done=False)
