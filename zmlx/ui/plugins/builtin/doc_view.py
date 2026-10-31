# ** name = '文档查看'
# ** desc = '「帮助 → 日志 / 路线图」：把包内 CHANGELOG.md 与 ROADMAP.md 显示成只读标签页（注册 gui.show_changelog / gui.show_roadmap）'
# ** enabled = True
"""「帮助 → 日志 / 路线图」：把随包发布的 Markdown 文档显示成标签页.

=======================  ========================================================
入口                      调用
=======================  ========================================================
GUI 命令                  ``gui.show_changelog()``（「关于」页的「日志」按钮 /
                          「帮助 → 关于」右键菜单的「日志」也调它）
GUI 命令                  ``gui.show_roadmap()``（同上，对应「路线图」）
=======================  ========================================================

⚠️ **2026-10-22：``MainWindow.show_changelog`` / ``show_roadmap`` / ``_show_md``
三个方法搬进本插件**。它们只是「读包内 md → 开一个 ``TextBrowser`` 标签页」，
与主窗口骨架无关，而且**只有「文档查看」这一类在用** —— 按
``plugins/AGENTS.md`` 的变化形态，跟插件走（「可关掉的功能，它的代码也应当能一起关掉」）。

⚠️ **命令名不能改**：``gui.show_changelog`` / ``gui.show_roadmap`` 被两处直接调用 ——
:mod:`zmlx.ui.tabs.about` 的「日志 / 路线图」按钮与右键菜单，以及**历史标签页**的
``gui_restore``（存的就是 ``gui.show_changelog()``）。所以 ``setup_ui`` 里
必须显式 ``gui.add_func``；插件默认**启用**，这两条命令开箱就有。

⚠️ **``restore`` 必须由公开入口传进来，不能在 ``_show_md`` 里写死**：``_show_md`` 不是
GUI 命令（名字以 ``_`` 开头，``list_member_functions`` 只注册公开方法），而
``gui_restore`` 会被存进标签页状态、重启时按原文用 ``gui.xxx(...)`` 重放 —— 写死
``gui._show_md(...)`` 会报 ``gui function <_show_md> not found``，标签页再也打不开。
理由与实现**原样**保留自搬过来的 ``MainWindow._show_md``。

⚠️ **文档只读包内 ``zmlx/data/`` 那一份**（``read_doc``）：仓库根目录已不留副本，
开发环境与 pip 安装环境读到的是同一个文件。

Created by DeepSeek, 2026-10-22: 由 ``MainWindow.show_changelog`` / ``show_roadmap`` /
    ``_show_md`` 搬出，命令名与行为保持不变
"""

from zmlx.system import execute_once


def show_changelog():
    """显示 CHANGELOG.md（同样是 GUI 命令 ``gui.show_changelog()``）."""
    _show_md("CHANGELOG.md", "修改记录", restore="gui.show_changelog()")


def show_roadmap():
    """显示 ROADMAP.md（同样是 GUI 命令 ``gui.show_roadmap()``）."""
    _show_md("ROADMAP.md", "未来工作", restore="gui.show_roadmap()")


def _show_md(filename, caption, restore=None):
    """加载并显示随包发布的 Markdown 文档.

    文档（README / CHANGELOG / ROADMAP）只存在于包内 `zmlx/data/` 目录：仓库根目录
    已不再保留副本，因此直接读包内那一份 —— pip 安装环境与开发环境读到的是同一个
    文件，不再需要任何同步步骤。

    Args:
        filename: 要显示的 md 文件名（如 ``CHANGELOG.md``）。
        caption: 标签页标题。
        restore: **公开入口**给出的「重启后如何还原这个标签页」的 GUI 命令
            （如 ``'gui.show_changelog()'``）。``None`` 表示不设。

    ⚠️ **恢复命令必须由公开入口传进来，不能在这里写死**：本函数**不是** GUI 命令
    （名字以 ``_`` 开头），而 ``gui_restore`` 会被存进标签页状态、重启时按原样用
    ``gui.xxx(...)`` 重放。这里若硬写 ``gui._show_md(...)``，重放时就会报
    ``gui function <_show_md> not found``（见 ``zmlx/ui/utils/gui_api.py`` 的
    ``GuiApi.__proc``），标签页再也打不开。

    ⚠️ 实现原样搬自 ``MainWindow._show_md``，只把 ``self.get_widget`` 换成
    ``gui.get_widget``（本函数可能在任意线程被调，``gui`` 会派发到 GUI 线程）。
    """
    from zmlx.data import get_path as data_path
    from zmlx.data import read_doc
    from zmlx.ui import gui
    from zmlx.ui.widgets import TextBrowser

    text = read_doc(filename)
    if text is None:
        print(f"未找到文件: {filename}")
        return
    path = data_path(filename)

    def oper(w: TextBrowser):
        if restore is not None:
            w.gui_restore = restore
        w.setOpenLinks(True)
        w.setOpenExternalLinks(True)
        w.setMarkdown(text)
        w.set_status(path)

    gui.get_widget(
        the_type=TextBrowser, caption=caption, on_top=True, icon="info", oper=oper
    )


@execute_once(file=__file__)
def setup_ui():
    """注册两条命令（插件被执行时调一次）.

    ⚠️ **``gui.add_func`` 那两行不是可有可无的**：这两个方法原先靠 ``MainWindow``
    的「所有公开方法自动注册」当上命令，搬到插件后必须自己补 —— 否则
    ``zmlx.ui.tabs.about`` 的「日志 / 路线图」按钮会报 ``not found``。
    """
    from zmlx.ui import gui

    gui.add_func('show_changelog', show_changelog)
    gui.add_func('show_roadmap', show_roadmap)


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**的这个分支里（``setups/*.py`` 则由
#    ``setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
#    插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``；直接 ``python doc_view.py``
#    时才是 ``'__main__'``（见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
