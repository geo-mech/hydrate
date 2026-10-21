# ** name = '数据编辑器与测试数据'
# ** desc = '注册 Array / XY / XYZ / Interp1 / Interp2 五种数据编辑器的「打开」命令，并在「文件 → 生成测试数据」下生成示例文件（默认不加载）'
# ** enabled = False
"""把「数据编辑器」这套控件挂成可用的 GUI 命令（插件，默认不加载）.

本文件只管**装配**，控件本体一直在 :mod:`zmlx.ui.widgets.editors` —— 那是个
**控件模块**（``TextEdit`` / ``ArrayEdit`` / ``Interp1Edit`` ……），``seepage.py``
还 ``from zmlx.ui.widgets.editors import *`` 复用它，所以控件**不能**搬进插件。

它原来挂在「帮助 → 加载 → Editors」：先点一下才生成「文件 → 生成测试数据」下的
五个条目。作为插件，这一层「加载」被去掉 —— **插件被执行，菜单就当场出现**
（2026-10-18）。同时这五个条目**从「帮助」移到「文件」**下：它们是往工作路径里
造文件，属于「文件」那一类动作，与「帮助」里的文档条目不是一回事。

为什么默认不加载
----------------

这五个条目全是「**造一份示例文件再用编辑器打开**」的演示动作（``ArrayExample.npy``
之类会真的写盘），日常建模用不上，默认开只会让「文件」菜单堆一串无关入口。
它们仍然随包分发 —— 想要就去「设置 → 插件」里勾上，重启后出现。

⚠️ **本插件只装配菜单，不注册 ``gui.open_xxx`` 命令**：那些命令由
:meth:`ArrayEdit.setup_ui` 等各控件自己 ``reg_file_type`` 时注册（见
:func:`_register_file_types`）。所以就算本插件被禁用，「打开已有文件」照常能用，
只是少了「造示例数据」这几个快捷入口。

⚠️ 作为插件，顶层**必须自己调** ``setup_ui()``（见文件末尾）—— 没有谁会替它调。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-18: 从 ``widgets/editors.py`` 抽出菜单装配，改为插件；
    去掉「帮助 → 加载 → Editors」中间层，并默认不加载
"""

import os

from zmlx.system import execute_once


@execute_once(file=__file__)
def _register_file_types():
    """让五种编辑器各自注册「文件类型」与 ``gui.open_xxx`` 命令.

    ⚠️ 这就是原来 ``widgets/editors.py`` 的 ``setup_ui()`` 做的事：控件类各自有
    静态方法 ``setup_ui()``（名字撞车，但它注册的是**文件类型**，不是菜单）。
    单个装不上不该影响其它，所以逐个 ``try``。
    """
    from zmlx.ui.widgets.editors import (
        ArrayEdit, Interp1Edit, Interp2Edit, XyEdit, XyzEdit)

    for obj in [ArrayEdit, XyEdit, XyzEdit, Interp1Edit, Interp2Edit]:
        try:
            obj.setup_ui()
        except Exception as err:
            print(err)


def _make_actions():
    """在「文件 → 生成测试数据」下挂五个「造一份示例文件并打开」的条目.

    ⚠️ 全在**工作路径**里落文件（``os.path.abspath``），所以菜单文字把文件名
    写全，用户点之前就知道会多出什么。
    """
    import numpy as np

    from zmlx.exts import Interp1
    from zmlx.ui import gui
    from zmlx.ui.widgets.editors import NumpyAlgs

    def test_data1():
        data = np.random.uniform(0, 2, size=[10, 3])
        fname = os.path.abspath('ArrayExample.npy')
        NumpyAlgs.save(data, fname)
        gui.open_numpy_array(fname)

    gui.add_action(menu=['文件', '生成测试数据'],
                   text='ArrayExample.npy', slot=test_data1)

    def test_data2():
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        data = np.column_stack([x, y])
        fname = os.path.abspath('XY数据.npy')
        np.save(fname, data)
        gui.open_xy_data(fname)

    gui.add_action(menu=['文件', '生成测试数据'],
                   text='XY数据.npy', slot=test_data2)

    def test_data3():
        x = np.linspace(-5, 5, 30)
        y = np.linspace(-5, 5, 30)
        x, y = np.meshgrid(x, y)
        z = np.sin(np.sqrt(x ** 2 + y ** 2))
        data = np.column_stack([x.flatten(), y.flatten(), z.flatten()])
        fname = os.path.abspath('XYZ数据.npy')
        np.save(fname, data)
        gui.open_xyz_data(fname)

    gui.add_action(menu=['文件', '生成测试数据'],
                   text='XYZ数据.npy', slot=test_data3)

    def test_data4():
        x = np.linspace(0, 5, 20)
        y = np.sin(x)
        data = Interp1(x=x, y=y)
        fname = os.path.abspath('Example.interp1')
        data.save(fname)
        gui.open_interp1(fname)

    gui.add_action(menu=['文件', '生成测试数据'],
                   text='Example.interp1', slot=test_data4)

    def test_data5():
        from zmlx.fluids import ch4
        f = ch4.create()
        f.den.save('Example.interp2')
        gui.open_interp2('Example.interp2')

    gui.add_action(
        menu=['文件', '生成测试数据'],
        text='Example.interp2', slot=test_data5)


@execute_once(file=__file__)
def setup_ui():
    """注册编辑器、挂上五个示例数据条目（插件被执行时调一次）."""
    _register_file_types()
    _make_actions()


# ⚠️ 插件路径：由 run_setup exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**（``extra_setups/*.py`` 则由 ``extra_setups/__init__.py``
#    统一调用 —— 这是两者唯一的区别）。插件机制执行时 ``__name__`` 是
#    ``'__zml_plugin__'``；直接 ``python editors_menu.py`` 时才是 ``'__main__'``
#    （见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
