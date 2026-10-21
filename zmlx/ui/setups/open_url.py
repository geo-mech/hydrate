"""``gui.open_url`` —— 用内嵌网页（``QWebEngineView``）打开网址 / 本地 HTML 的标签页.

⚠️ **本文件 2026-10-31 新建**：原 `MainWindow.open_url` 的方法体**原样搬来**，
一字未改（`main.py` 里那段「显示一个html文件或者网址」的逻辑整体在这里）。

⚠️⚠️ **``gui.open_url`` 与 ``zmlx.ui.alg.open_url`` 是两回事，名字都不能改**
----------------------------------------------------------------------------

| 名字 | 在哪 | 干什么 |
|---|---|---|
| ``zmlx.ui.alg.open_url(url, ...)`` | ``ui/alg.py`` | **对外统一入口**：先判断 ``use_web_engine``、有没有界面，再决定「开标签页」还是**降级到系统浏览器** |
| ``gui.open_url(url, ...)`` | **本文件** | **GUI 标签页实现**：真的建一个 ``QWebEngineView`` 标签页 |

``ui/alg.py`` 在需要开标签页时调的就是本文件注册的命令::

    gui.open_url(url=url, caption=caption, on_top=on_top,
                 zoom_factor=zoom_factor, icon=icon)

所以**这个命令名一旦消失，``alg.open_url`` 开网页那条路就断了**（只剩系统浏览器）。
这也是把它搬来 ``setups/`` 的理由：它属于**必加载**的装配。

为什么在 ``setups/`` 而不是 ``tabs/`` 或插件
--------------------------------------------

判据是 ``setups/AGENTS.md`` §1 那条：**关掉它，软件还能不能正常用？**

- **不能** —— ``alg.open_url`` 是**全仓打开网址/本地 HTML 的统一入口**（``about.py`` 的
  「主页」按钮、``md_view.py`` 里点 Markdown 链接、``readme_browser.py``、
  ``ai_assistant`` 都走它），而它依赖本命令。
- 它也**不是一个控件**：``QWebEngineView`` 是 Qt 自带的类，这里只有「开一个标签页」的装配。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

行为契约（**搬迁前后完全一致**）
--------------------------------

=========================  ==================================================
情形                        行为
=========================  ==================================================
``url`` 不是 ``str``        直接 ``return``（什么都不做）
缺 ``QWebEngineView``       本地文件 → ``startfile``；否则 → 系统浏览器打开
有 WebEngine                开一个 ``QWebEngineView`` 标签页
``zoom_factor`` 未给        PyQt6 → ``1.0``；PyQt5 → ``1.5``
``icon`` 未给               ``'web'``
``gui_restore``            ``gui.open_url(**{url, caption, on_top, zoom_factor, icon})``
=========================  ==================================================

⚠️ **``gui_restore`` 里存的是 url 等参数的 repr**：重启时按原文重放，所以这几个
**参数名**也不能改。
"""

import os

from zmlx.system import execute_once
from zmlx.ui import gui
from zmlx.ui.pyqt import QtCore, QWebEngineView, is_pyqt6


def open_url(url, caption=None, on_top=None, zoom_factor=None, icon=None):
    """用内嵌网页打开一个网址或本地 HTML 文件（GUI 标签页形式）.

    显示一个 html 文件或者网址。

    Args:
        url: 网址，或本地 HTML 文件的路径。
        caption: 标签页标题。
        on_top: 是否置顶显示。
        zoom_factor: 缩放比例；``None`` 时 PyQt6 取 ``1.0``、PyQt5 取 ``1.5``。
        icon: 标签页图标名；``None`` 时用 ``'web'``。

    ⚠️ **没有 ``QWebEngineView`` 时自动降级**：本地文件交给 ``startfile``、
    网址交给系统浏览器 —— 这一步是原实现就有的，别删掉（缺 ``PyQt6-WebEngine``
    的机器全靠它）。
    """
    if not isinstance(url, str):
        return

    if QWebEngineView is None:
        if os.path.isfile(url):
            from zmlx.algs import startfile

            startfile(url)
        else:
            from webbrowser import open_new_tab

            open_new_tab(url)
        return

    kwds = dict(
        url=url, caption=caption, on_top=on_top, zoom_factor=zoom_factor, icon=icon
    )

    if zoom_factor is None:
        zoom_factor = 1.0 if is_pyqt6 else 1.5

    def oper(widget):
        widget.page().setZoomFactor(zoom_factor)
        if os.path.isfile(url):
            widget.load(QtCore.QUrl.fromLocalFile(url))
        else:
            widget.load(QtCore.QUrl(url))
        widget.gui_restore = f"""gui.open_url(**{kwds})"""

    if icon is None:
        icon = "web"

    gui.get_widget(
        QWebEngineView,
        caption=caption,
        on_top=on_top,
        oper=oper,
        icon=icon,
    )


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.open_url``（由 ``setups/__init__.py`` 调用）.

    ⚠️ **本文件不挂菜单项**：它由 ``zmlx.ui.alg.open_url`` 等**代码路径**调用，
    不是给用户直接点的入口（用户点的是各处的按钮 / 链接）。

    ⚠️ **命令名 ``open_url`` 不能改**：``ui/alg.py`` 里那句 ``gui.open_url(...)``
    是按名字调的真实调用。
    """
    gui.add_func('open_url', open_url)


if __name__ == '__main__':
    # 单独跑一下看看：``python -m zmlx.ui.setups.open_url <url>``
    import sys

    from zmlx.ui.pyqt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    from zmlx.ui.main import MainWindow

    win = MainWindow()
    gui.set(win.get_gui_api())
    setup_ui()
    open_url(sys.argv[1] if len(sys.argv) > 1 else 'https://gitee.com/geomech/hydrate')
    sys.exit(app.exec())
