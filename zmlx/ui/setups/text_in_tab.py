"""``gui.show_text_in_tab`` —— 把一段纯文本丢进一个标签页显示.

⚠️ **本文件 2026-10-31 新建**：原 `MainWindow.show_text_in_tab` 的方法体**原样搬来**，
逻辑一字未改。

⚠️ **本文件只管「开标签页」，不管控件本体**：真正显示文本的是
:class:`zmlx.ui.widgets.text_browser.TextBrowser`（底层控件，留在 ``widgets/``）。
这是 ``setups/AGENTS.md`` §2 第 4 条的要求 —— 装配层只做「注册 + 开页面」。

为什么在 ``setups/`` 而不是 ``tabs/`` 或插件
--------------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- **不能** —— 它与 :mod:`zmlx.ui.setups.string_table` 是**同一类东西**：一个
  「把一段内容丢进窗口看」的**通用出口**，被**插件**与 **scen** 直接按命令名调用
  （``scen/ai_assistant/action.py`` 用它显示回答的正文）。
  做成插件的话，那些调用方在插件关掉时就会「找不到命令」。
- 它**不是一个控件**：``QTextBrowser``（此处是 ``TextBrowser``）是现成的底层控件，
  这里只有「开一个标签页 + 填内容」的装配。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

行为契约（**搬迁前后完全一致**）
--------------------------------

=========================  ==================================================
项                          值
=========================  ==================================================
命令                        ``gui.show_text_in_tab(text, caption=None, on_top=None)``
标签页                      标题 = ``caption``（未给时由 ``get_widget`` 决定）
内容                        ``TextBrowser.setPlainText(text)`` —— **纯文本**，不渲染 HTML
``gui_restore``             ``gui.show_text_in_tab(**{text, caption, on_top})``
=========================  ==================================================

⚠️ **``gui_restore`` 存的是参数的 repr**：重启时按原文重放，所以这三个**参数名**也不能改。
⚠️ **``text`` 会进 ``gui_restore``**：这一点与 :mod:`zmlx.ui.setups.string_table` 一致 ——
重启后内容照旧。若将来它变得很大需要瘦身，改动要在这里和 CHANGELOG 里同时说明。

⚠️ **纯文本不是 Markdown/HTML**：用的是 ``setPlainText``。要渲染 Markdown 请用
:class:`zmlx.ui.widgets.md_view.MarkdownView`（``setups/readme_browser.py`` 就是这么做的）。
"""

from zmlx.system import execute_once
from zmlx.ui import gui
from zmlx.ui.widgets.text_browser import TextBrowser


def show_text_in_tab(text, caption=None, on_top=None):
    """在一个标签页中显示文本。

    Args:
        text: 要显示的文本（**纯文本**，按 ``setPlainText`` 设置）。
        caption: 标签页的标题。
        on_top: 是否将标签页置顶。

    Returns:
        None

    ⚠️ 由 ``MainWindow.show_text_in_tab`` **原样搬来**（2026-10-31）：那段代码靠「主窗口的
    公开方法被自动注册成 ``gui.xxx``」提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('show_text_in_tab', ...)`` **显式补上**。
    """
    opts = dict(text=text, caption=caption, on_top=on_top)

    def oper(w: TextBrowser):
        w.gui_restore = f"""gui.show_text_in_tab(**{opts})"""
        w.setPlainText(text)

    gui.get_widget(TextBrowser, caption=caption, on_top=on_top, oper=oper)


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.show_text_in_tab``（由 ``setups/__init__.py`` 调用）.

    ⚠️ **本文件不挂菜单项**：它是给插件 / scen / 脚本用的**通用出口**，
    由调用方自己决定什么时候弹这个文本页（``ai_assistant`` 就是一个典型调用方）。
    """
    gui.add_func('show_text_in_tab', show_text_in_tab)


if __name__ == '__main__':
    # 单独跑一下看看：``python -m zmlx.ui.setups.text_in_tab [caption]``
    import sys

    from zmlx.ui.pyqt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    from zmlx.ui.main import MainWindow

    win = MainWindow()
    gui.set(win.get_gui_api())
    setup_ui()
    show_text_in_tab(
        '这是一段示例文本。\n\n由 setups/text_in_tab.py 直接运行显示。',
        caption=sys.argv[1] if len(sys.argv) > 1 else '文本示例',
    )
    sys.exit(app.exec())
