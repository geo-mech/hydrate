"""trimesh 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.plt.on_ui import show_trimesh as trimesh

warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)


def test():
    from zmlx.data.trimesh_test import generate_test_mesh
    # 生成测试网格
    triangles, points = generate_test_mesh()
    # 绘制三角形网格
    trimesh(triangles=triangles, points=points, gui_mode=True)


if __name__ == '__main__':
    test()
