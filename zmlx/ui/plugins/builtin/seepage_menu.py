# ** name = 'Seepage 示例数据'
# ** desc = '在「文件 → 生成测试数据」下生成一份 Example.fludef（甲烷流体定义）并用编辑器打开（默认不加载）'
# ** enabled = False
"""把「Seepage 模型编辑器」的示例数据入口挂成菜单（插件，默认不加载）.

本文件只管**装配**，控件本体一直在 :mod:`zmlx.ui.widgets.seepage` —— 那是
**控件模块**（``FludefEdit`` / ``SeepageEdit``），**不能**搬进插件。

它原来挂在「帮助 → 加载 → Seepage功能」：先点一下才生成「文件 → 生成测试数据」
下的那一条。作为插件，这一层「加载」被去掉 —— **插件被执行，菜单就当场出现**
（2026-10-18）。

为什么默认不加载
----------------

这条菜单的全部作用是「**造一份示例 .fludef 再用编辑器打开**」（会真的往工作路径
写文件），日常建模用不上。它仍然随包分发 —— 想要就去「设置 → 插件」里勾上，
重启后出现。

⚠️ **本插件只装配菜单，不注册任何 ``gui.open_xxx`` 命令**：``open_fludef`` /
``open_seepage`` 由 ``FludefEdit.setup_ui()`` / ``SeepageEdit.setup_ui()`` 自己
``reg_file_type`` 时注册（见 ``extra_setups/__init__.py`` 那次调用）。所以就算本
插件被禁用，**「打开已有 .seepage / .fludef 文件」照常能用**，只是少了造示例的入口。

⚠️ 作为插件，顶层**必须自己调** ``setup_ui()``（见文件末尾）—— 没有谁会替它调。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-18: 从 ``widgets/seepage.py`` 抽出菜单装配，改为插件；
    去掉「帮助 → 加载 → Seepage功能」中间层，菜单归到「文件 → 生成测试数据」，
    并默认不加载
"""

from zmlx.system import execute_once


@execute_once(file=__file__)
def _register_file_types():
    """让两个编辑器各自注册「文件类型」与 ``gui.open_xxx`` 命令.

    ⚠️ 这就是原来 ``widgets/seepage.py`` 的 ``setup_ui()`` 做的事。**它由
    ``extra_setups/__init__.py`` 常驻调用**，与本插件是否启用无关 —— 这里再调一次
    只是为了「单独运行本文件时也能用」，``@execute_once`` 保证不会重复注册。
    """
    from zmlx.ui.widgets.seepage import FludefEdit, SeepageEdit

    for obj in [FludefEdit, SeepageEdit]:
        try:
            obj.setup_ui()
        except Exception as err:
            print(err)


def _make_actions():
    """在「文件 → 生成测试数据」下挂「造一份 Example.fludef 并打开」.

    ⚠️ 文件落在**工作路径**里（相对路径，与原来一致），所以菜单文字把文件名
    写全，用户点之前就知道会多出什么。
    """
    from zmlx.ui import gui

    def test_data():
        from zmlx.fluids import ch4

        fname = 'Example.fludef'
        f = ch4.create(name='Methane')
        f.save(fname)
        gui.open_fludef(fname)

    gui.add_action(menu=['文件', '生成测试数据'],
                   text='流体定义: Example.fludef', slot=test_data)


@execute_once(file=__file__)
def setup_ui():
    """注册文件类型、挂上示例数据条目（插件被执行时调一次）."""
    _register_file_types()
    _make_actions()


# ⚠️ 插件路径：由 run_setup exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**（``extra_setups/*.py`` 则由 ``extra_setups/__init__.py``
#    统一调用 —— 这是两者唯一的区别）。插件机制执行时 ``__name__`` 是
#    ``'__zml_plugin__'``；直接 ``python seepage_menu.py`` 时才是 ``'__main__'``
#    （见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
