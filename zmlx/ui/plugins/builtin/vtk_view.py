# ** name = 'VtkView'
# ** desc = '用 pyvista 做的 3D 演示：显示一个带「高程」标量着色的球体（需要安装 pyvista）'
# ** enabled = False
"""VTK/pyvista 可视化动作（「帮助 → VtkView」下的两个 3D 演示）.

算例很小：显示一个带「高程」标量着色的球体。真正干活的是
``MainWindow.get_vtk_view(caption, init)``（它会把 ``init(plotter)`` 跑在一个
pyvista 视图里）。

⚠️ ``pyvista`` 是**可选依赖**，所以导入放在回调内部 —— 没装它时插件照样能注册、
菜单照样出现，点了才会给出 ``ImportError``。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-18: 改为插件；去掉「帮助 → 加载 → VtkView」那一级，
    插件执行后菜单直接出现
"""

from zmlx.system import execute_once


def _show_sphere(plotter):
    """在给定的 pyvista plotter 上画一个底部低、顶部高的球体."""
    import pyvista as pv

    sphere = pv.Sphere()
    sphere['高程'] = sphere.points[:, 2]
    plotter.add_mesh(sphere, scalars='高程', cmap='terrain')
    plotter.add_axes()
    plotter.add_scalar_bar('高程')


@execute_once(file=__file__)
def setup_ui():
    """把两个演示直接挂到「帮助 → VtkView」下.

    ⚠️ **不再有「帮助 → 加载 → VtkView」那一级**（2026-10-18 改）：插件一旦
    被执行，菜单就该**当场出现**，不必再点一次「加载」。
    """
    from zmlx.ui import gui

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体1',
        slot=lambda: gui.get_vtk_view(caption='球体1', init=_show_sphere),
    )

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体2',
        slot=lambda: gui.get_vtk_view(caption='球体2', init=_show_sphere),
    )


# ⚠️ 作为**插件**被 ``run_setup`` 执行时，没人会替我们调 ``setup_ui()``：
#    插件文件必须在**顶层自己调**（``extra_setups/*.py`` 则由
#    ``extra_setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
setup_ui()
