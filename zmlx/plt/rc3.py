"""rc3 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.plt.on_ui import show_rc3

warn(
    'The module zmlx.plt.rc3 已弃用（remove after 2027-5-23）：'
    '请改用 `from zmlx import show_rc3`',
    DeprecationWarning, stacklevel=2)


def test():
    from zmlx.geometries.dfn_v3 import to_rc3, create_demo
    import random
    rc3 = to_rc3(create_demo())
    color = []
    alpha = []
    for _ in rc3:
        color.append(random.uniform(5, 9))
        alpha.append(random.uniform(0, 1))
    show_rc3(rc3, gui_mode=True,
             cbar=dict(label='Index', title='Index', shrink=0.5),
             )


if __name__ == '__main__':
    test()
