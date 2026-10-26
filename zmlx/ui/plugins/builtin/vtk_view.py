# ** name = 'VtkView'
# ** desc = '用 pyvista 做的 3D 演示：显示一个带「高程」标量着色的球体（需要安装 pyvista）'
# ** enabled = False
"""VTK/pyvista 可视化动作（「帮助 → VtkView」下的两个 3D 演示）.

算例很小：显示一个带「高程」标量着色的球体。真正干活的是 :func:`get_vtk_view`
（它把一个 ``QtInteractor`` 开成标签页，并把 ``init(plotter)`` 跑在里面）。

⚠️ **``get_vtk_view`` 2026-10-22 从 ``MainWindow`` 搬到这里**（原来叫
``MainWindow.get_vtk_view``）。理由是它**只服务本插件**，且依赖**可选库** ``pyvistaqt``：

- ``MainWindow`` 里**仍留着一个同名方法**（签名是 ``(*args, **kwargs)``，一个参数都不读，
  所以也不复制本文件的参数表），但它只是**占位**（打印「请先启用 VtkView 插件」）——
  这样插件没启用时 ``gui.get_vtk_view`` 依然存在、不会报 ``gui function <...> not found``，
  而且给出的是可操作的提示。⚠️ 顺带保证了一条老路径：``main_window.get_vtk_view(...)``
  （直接调主窗口方法）永远不炸；
- **插件启用后，本文件的 ``gui.add_func`` 会把那个占位覆盖掉** —— 命令表
  ``GuiApi.funcs`` 是普通的 ``SharedDict``，``set`` 就是赋值，**后写者胜**。插件在控制台
  线程里执行、``MainWindow`` 在 GUI 线程里构造（且 ``gui.set(api)`` 早在
  ``__on_init`` 里完成），所以这里是**后写**。⚠️ 这个先后关系是**有意的**，改动
  ``__console_kernel`` 的执行顺序时要重新确认（见 ``plugins/AGENTS.md`` 的顺序契约）。

⚠️ **``pyvista`` / ``pyvistaqt`` 是可选依赖**：导入放在函数体内 —— 没装时插件照样能注册、
菜单照样出现，点了才会给出 ``ImportError``。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-18: 改为插件；去掉「帮助 → 加载 → VtkView」那一级，
    插件执行后菜单直接出现
Modified by DeepSeek, 2026-10-22: ``MainWindow.get_vtk_view`` 搬入本文件（只有本插件用，
    且依赖可选库），并在 ``setup_ui`` 里显式注册 ``gui.get_vtk_view`` 保住命令名
Modified by DeepSeek, 2026-10-22: ``MainWindow`` 里补回一个**占位**同名方法（只打印提示，
    **不用** ``func is None`` 注销命令——那条路会让「直接调主窗口方法」
    ``main_window.get_vtk_view()`` 也一并失效），这里靠 ``add_func`` 后写覆盖它
"""

from zmlx.system import execute_once


def get_vtk_view(caption=None, on_top=None, init=None, oper=None):
    """打开（或取回）一个 pyvista 的 ``QtInteractor`` 标签页.

    Args:
        caption: 窗口的标题。
        on_top: 是否将窗口置顶。
        init: 初始化函数，首次创建控件、显示之前调用，签名 ``init(plotter)``。
        oper: 操作函数，**每次**调用都会执行（包括已经存在、只是切到前面那一次）。

    Returns:
        QtInteractor | None: 标签页控件；``pyvistaqt`` 未安装或创建失败时为 ``None``。

    ⚠️ **同名标题只会有一个标签页**（由 ``TabWidget.get_widget`` 的
    「类型 + 标题」匹配规则保证），重复调用只是把它切到前面。
    """
    from pyvistaqt import QtInteractor

    from zmlx.ui import gui

    # ⚠️ 用 GUI 命令 ``gui.get_widget`` 而不是去抓 ``MainWindow``：本函数可能在任意线程
    #    被调用（菜单 slot、插件、脚本），``gui.xxx`` 会把它派发到 GUI 线程。
    return gui.get_widget(
        the_type=QtInteractor, caption=caption, on_top=on_top, init=init, oper=oper)


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
    """注册 ``gui.get_vtk_view``，并把两个演示挂到「帮助 → VtkView」下.

    ⚠️ **``gui.add_func`` 那行不是可有可无的**，而且它**覆盖**的是 ``MainWindow`` 里那个
    同名**占位**方法（只打印提示）：命令表是先注册占位、后注册这里的，后写者胜
    （见模块文档）。不显式注册就等于插件启用后仍然只得到一句提示。

    ⚠️ **不再有「帮助 → 加载 → VtkView」那一级**（2026-10-18 改）：插件一旦
    被执行，菜单就该**当场出现**，不必再点一次「加载」。
    """
    from zmlx.ui import gui

    gui.add_func('get_vtk_view', get_vtk_view)

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体1',
        slot=lambda: gui.get_vtk_view(caption='球体1', init=_show_sphere),
    )

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体2',
        slot=lambda: gui.get_vtk_view(caption='球体2', init=_show_sphere),
    )


# ⚠️ 插件的标准形式：**注册写在这个分支里**。
#    插件机制用 ``exec`` 执行本文件时，命名空间里的 ``__name__`` 被设成
#    ``'__zml_plugin__'``，于是这里成立 —— 只注册，不开窗口。
#    ⚠️ **不要**在顶层裸写 ``setup_ui()``：那样「插件加载」与「直接运行本文件」
#    走同一段代码，既无法区分两种意图，也无法在 ``python vtk_view.py`` 时自测。
if __name__ == '__zml_plugin__':
    setup_ui()
