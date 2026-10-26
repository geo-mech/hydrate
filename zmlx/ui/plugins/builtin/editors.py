# ** name = '数据编辑器'
# ** desc = '数据编辑器（Array / XY / XYZ / Interp1 / Interp2 / FluDef / Seepage）：注册「文件 → 打开 / 新建」的 7 种文件类型，并在「帮助 → 其它 → 生成测试数据」下造示例文件'
# ** enabled = True
"""数据编辑器插件：把「打开 / 新建 / 造示例数据」这一整套编辑器入口挂到界面上.

⚠️ **本文件就是全部装配代码**（2026-10-22 由两处合并而来）：注册表在两个带
``@execute_once`` 的函数里，控件本体在 :mod:`zmlx.ui.widgets.editors`
（``seepage_edit`` / ``field_edit`` 等）。一行控件代码都不在这里 ——
编辑器的 ``set_data`` / ``get_data`` 仍在各自的模块里，这里只是一张表：
「哪个控件配哪种数据」，逐个交给 :func:`zmlx.ui.alg.reg_file_type` 注册成
``gui.open_xxx`` 命令与「文件 → 打开 / 新建」的条目。

⚠️ **顶层什么都不做**（除 import 与定义）：注册只在
``__name__ == '__zml_plugin__'`` 分支里发起 —— 模块级语句在 ``exec`` 下照跑，
放在顶层就等于「import 这个模块 = 注册菜单」，那是导入期副作用
（见 ``ui/AGENTS.md`` §1）。直接 ``python editors.py`` 时走 ``__main__`` 分支自测。

⚠️ **去重靠 ``@execute_once``**：两个入口函数都带它，``load_all`` 在一次运行里可能
重复调用，插件被「临时加载」时也可能再跑一遍 —— 重复注册 ``reg_file_type`` 会在菜单里
多出条目。

⚠️ **名字必须保持 ``editors``**：名单 ``zml_plugins`` 里存的是下面的**绝对路径**，
``_registry.migrate_builtin_paths()`` 的 ``_relocated_paths()`` 把旧的
``editors_menu.py`` / ``seepage_menu.py`` 记录迁移到本文件；改名会让用户勾选过的
状态**静默**丢失（见 ``plugins/AGENTS.md`` §6 第 3 条）。

历史
----

======================  ========================================================
原来                     现在
======================  ========================================================
``ui/extra_setups/editors.py``（常驻注册 7 种文件类型）   本文件的 ``setup_file_types()``
``builtin/editors_menu.py``（5 个 numpy 示例，默认不加载）  本文件的 ``setup_actions()``
``builtin/seepage_menu.py``（1 个流体定义示例，默认不加载）  同上（合并）
``zmlx/scen/editors/__init__.py + _setup.py + zml_plugin.py``  本文件（原先的插件包已删除）
======================  ========================================================

⚠️ 为什么回到 ``plugins/builtin/``：「可关掉的功能，它的代码也应当能一起关掉」仍然成立 ——
本文件**就是**那段可关掉的代码。原先它按「包自己就是一个插件」的形态住进
``zmlx/scen/editors/``（里面还带着三个控件模块），但控件本身并不属于 ``scen`` ——
它们是 `ui/widgets/editors/` 的普通编辑器（``seepage_edit`` / ``field_edit`` 本来就是纯控件，
``seepage_edit`` 只额外依赖 ``zmlx.tfc``）。于是把控件退回 ``ui/widgets/editors/``、
把装配（原先的 ``_setup.py`` + ``zml_plugin.py``）合成这**一个**文件放进 ``builtin/``，
两者各自回到该在的地方。

⚠️ 旧名单记录（``scen/editors/zml_plugin.py``）由
:func:`zmlx.ui.plugins._registry._relocated_paths` 改写到这里、标记原样保留，
所以**勾过的状态不会丢**。

⚠️ 「打开已有文件」（7 种文件类型、``gui.open_xxx`` 命令）原来在 2026-10-22 之前是
**常驻**的，与插件无关；现在它跟着本插件走。**这是有意的**：编辑器整体就是一个可关闭
的单元。代价：禁用后 ``gui.open_seepage`` 等命令不再存在（见 ``ui/ReadMe.md``）。

Created by DeepSeek, 2026-10-22: 由 ``ui/plugins/builtin/editors_menu.py`` +
    ``seepage_menu.py`` + ``ui/extra_setups/editors.py`` 合并而成
Modified by DeepSeek, 2026-10-22: 与 ``zmlx/scen/editors/`` 的 ``_setup.py`` +
    ``zml_plugin.py`` 再合成这一个文件；控件退回 ``ui/widgets/editors/``
Modified by DeepSeek, 2026-10-25: 「生成测试数据」由「文件」下沉到「帮助 → 其它」，
    只改挂载点与文案（菜单文字仍是「生成测试数据」），控件与文件类型注册不变
"""

try:
    import numpy as np
except ImportError:
    np = None

from zmlx.system import execute_once


@execute_once(file=__file__)
def setup_file_types():
    """注册全部数据编辑器的「文件类型」与 ``gui.open_xxx`` 命令.

    ⚠️ **只注册文件类型，不挂菜单**：造示例文件是演示用的动作，单独放在
    :func:`setup_actions` 里，两者由文件末尾的插件分支一起调用。

    ⚠️ **单个表项装不上不该影响其它**，所以**逐个 ``try``**。
    """
    from zmlx.exts import FluDef, Interp1, Interp2, Seepage
    from zmlx.ui import gui
    from zmlx.ui.widgets.editors.array_edit import ArrayEdit, NumpyAlgs
    from zmlx.ui.widgets.editors.data_edit import XyEdit, XyzEdit
    from zmlx.ui.widgets.editors.interp_edit import Interp1Edit, Interp2Edit
    from zmlx.ui.widgets.editors.seepage_edit import FludefEdit, SeepageEdit

    # 三种「numpy 矩阵」文件类型的初始数据：空数组
    def empty_array():
        return np.array([])

    for kwargs in [
        # ---- numpy 数组 / 曲线 / 曲面：数据是一份 ndarray，读写都用 NumpyAlgs ----
        dict(desc='Numpy矩阵', exts=['.npy', '.txt'], name='numpy_array',
             save=NumpyAlgs.save, load=NumpyAlgs.load,
             init=empty_array, widget_type=ArrayEdit),
        dict(desc='XY两列数据(numpy矩阵)', exts=['.npy', '.txt'], name='xy_data',
             save=NumpyAlgs.save, load=NumpyAlgs.load,
             init=empty_array, widget_type=XyEdit),
        dict(desc='XYZ数据(numpy矩阵)', exts=['.npy', '.txt'], name='xyz_data',
             save=NumpyAlgs.save, load=NumpyAlgs.load,
             init=empty_array, widget_type=XyzEdit),

        # ---- 插值：数据是 Interp1 / Interp2，控件自带 set_data / get_data ----
        dict(desc='一维插值 Interp1', exts=['.interp1', '.xml', '.txt'], name='interp1',
             init=Interp1, widget_type=Interp1Edit),
        dict(desc='二维插值 Interp2', exts=['.interp2', '.xml', '.txt'], name='interp2',
             init=Interp2, widget_type=Interp2Edit),

        # ---- Seepage 模型：控件绑定模型对象，改动直接写在模型上 ----
        # ⚠️ 两个类都**必须**成对实现 ``set_data`` / ``get_data``：``reg_file_type`` 用
        #    两个独立的 ``hasattr`` 探测，缺 set_data 就**静默**不挂，打开后会得到空标签页
        #    （见 ``ui/widgets/editors/AGENTS.md`` §4.5）。改控件时别删这两个方法。
        dict(desc='流体定义 FluDef', exts=['.fludef', '.xml', '.txt'], name='fludef',
             init=FluDef, widget_type=FludefEdit),
        dict(desc='Seepage文件', exts=['.seepage', '.xml', '.txt'], name='seepage',
             save=lambda data, name: data.save(name),
             load=lambda name: Seepage(path=name),
             init=lambda: Seepage(), widget_type=SeepageEdit),
    ]:
        try:
            gui.reg_file_type(**kwargs)
        except Exception as err:
            print(f"Error when reg_file_type({kwargs.get('name')}): {err}")


@execute_once(file=__file__)
def setup_actions():
    """在「帮助 → 其它 → 生成测试数据」下挂「造一份示例文件并打开」的条目.

    ⚠️ 菜单路径 2026-10-25 由「文件 → 生成测试数据」**下沉**到「帮助 → 其它 → 生成测试数据」：
    造示例数据是给开发者 / 试用者准备的调试入口，不是日常的文件操作，放在「文件」里
    会让普通用户以为它是主流程的一部分。⚠️ 菜单文字不改（仍是「生成测试数据」+ 文件名），
    只换挂载点 —— 外部脚本 / 文档里提到的是**菜单文字**，不受影响。

    ⚠️ 全部落在**工作路径**里（``os.path.abspath`` / 相对路径），所以菜单文字把文件名
    写全，用户点之前就知道会多出什么。

    ⚠️ 这两个菜单曾经是两个独立插件（``editors_menu`` / ``seepage_menu``，
    都声明 ``# ** enabled = False``），2026-10-22 合并进这一个插件 —— 它们做的事
    完全同类（造示例数据），分开放只会让用户在「设置 → 插件」里多勾一次。
    """
    import os

    from zmlx.exts import Interp1
    from zmlx.ui import gui
    from zmlx.ui.widgets.editors import NumpyAlgs

    menu = ['帮助', '其它', '生成测试数据']

    def test_data1():
        data = np.random.uniform(0, 2, size=[10, 3])
        fname = os.path.abspath('ArrayExample.npy')
        NumpyAlgs.save(data, fname)
        gui.open_numpy_array(fname)

    gui.add_action(menu=menu, text='ArrayExample.npy', slot=test_data1)

    def test_data2():
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        data = np.column_stack([x, y])
        fname = os.path.abspath('XY数据.npy')
        np.save(fname, data)
        gui.open_xy_data(fname)

    gui.add_action(menu=menu, text='XY数据.npy', slot=test_data2)

    def test_data3():
        x = np.linspace(-5, 5, 30)
        y = np.linspace(-5, 5, 30)
        x, y = np.meshgrid(x, y)
        z = np.sin(np.sqrt(x ** 2 + y ** 2))
        data = np.column_stack([x.flatten(), y.flatten(), z.flatten()])
        fname = os.path.abspath('XYZ数据.npy')
        np.save(fname, data)
        gui.open_xyz_data(fname)

    gui.add_action(menu=menu, text='XYZ数据.npy', slot=test_data3)

    def test_data4():
        x = np.linspace(0, 5, 20)
        y = np.sin(x)
        data = Interp1(x=x, y=y)
        fname = os.path.abspath('Example.interp1')
        data.save(fname)
        gui.open_interp1(fname)

    gui.add_action(menu=menu, text='Example.interp1', slot=test_data4)

    def test_data5():
        from zmlx.fluids import ch4
        f = ch4.create()
        f.den.save('Example.interp2')
        gui.open_interp2('Example.interp2')

    gui.add_action(menu=menu, text='Example.interp2', slot=test_data5)

    def test_data6():
        from zmlx.fluids import ch4

        fname = 'Example.fludef'
        f = ch4.create(name='Methane')
        f.save(fname)
        gui.open_fludef(fname)

    gui.add_action(menu=menu, text='流体定义: Example.fludef', slot=test_data6)


if __name__ == '__zml_plugin__':
    # 被插件机制执行（``__name__`` 是 ``'__zml_plugin__'``）：只注册，不开窗口
    setup_file_types()
    setup_actions()

if __name__ == '__main__':
    # 直接 ``python editors.py``：开一个界面自测（此时 ``__name__`` 是 ``__main__``）
    from zmlx.ui import gui

    def main():
        setup_file_types()
        setup_actions()

    gui.execute(main, close_after_done=False)
