# ** name = 'PDF 查看'
# ** desc = '用内置浏览器（QtWebEngine）打开 PDF：注册 gui.open_pdf 命令与 .pdf 文件类型（需要安装 PyQt6-WebEngine）'
# ** enabled = True
"""PDF 查看插件：注册 ``gui.open_pdf`` 命令 + ``.pdf`` 文件类型.

⚠️ **它是插件（可关闭），不是核心功能**（2026-10-22）：PDF 查看依赖**可选库**
``QWebEngineView``（``PyQt6-WebEngine``）。这个能力原先以 ``MainWindow.open_pdf``
的形式常驻在界面骨架里 —— 那意味着**一个可选依赖的能力占着核心代码**，也让它无法被关闭。
现在整体搬到这里：没装 WebEngine 的环境不受影响，不想用它的人可以在「设置 → 插件」里关掉。

**默认启用**（``# ** enabled = True``）：它是常规能力 —— 「文件 → 打开」选到 ``.pdf``
就该能看。⚠️ 若环境里没有 ``QWebEngineView``，本插件**照样注册**（命令与文件类型都在），
只是点开时给一句明确的提示，而不是让整个插件加载失败。

注册了什么
----------

| 注册物 | 内容 | 用途 |
|---|---|---|
| ``gui.open_pdf`` | :func:`open_pdf` | 命令（脚本 / 控制台可直接调） |
| 文件类型 | ``desc='PDF文件'``、``exts=['.pdf']`` | 「文件 → 打开」按扩展名分发到本插件 |

⚠️ **为什么不用 `gui.reg_file_type(...)`**：那个接口的 ``widget_type`` 必须成对实现
``set_data`` / ``get_data``（见 ``ui/widgets/editors/AGENTS.md`` §4.5），而 PDF 查看器
是 ``QWebEngineView``，没有也不该有这两个方法。``reg_file_type`` 内部做的其实就是
「``gui.add_func('open_xxx')`` + ``gui.add_file_handler(...)``」，所以这里**直接做这两步**
—— 得到的东西完全一样，还不会因为缺 ``set_data`` 而静默降级成空标签页。

⚠️ **命令名``open_pdf`` 不能改**：历史标签页的 ``gui_restore`` 里存着
``gui.open_pdf(fname=..., caption=..., on_top=...)``，重启时按原文重放。
本插件的 :func:`open_pdf` **保持与原来 ``MainWindow.open_pdf`` 完全相同的签名与
``gui_restore`` 格式**，所以老标签页仍能恢复。

Created by DeepSeek, 2026-10-22: 由 ``MainWindow.open_pdf`` 搬来并改成插件
"""

from zmlx.system import execute_once


def open_pdf(fname, caption=None, on_top=True):
    """用内置浏览器（QtWebEngine）打开一个 PDF 文件.

    Args:
        fname: PDF 路径，``str``。也接受 ``file://`` 形式的 URL。
        caption: 标签页标题；``None`` 时用文件名。
        on_top: 是否把它切到前面。

    ⚠️ **同名标题只会有一个标签页**（``TabWidget.get_widget`` 按「类型 + 标题」匹配），
    重复调用只是切到前面。

    ⚠️ 缺少可选库 ``PyQt6-WebEngine`` 时**不抛异常**，只打印一句可操作的提示并返回 ——
    这样菜单项 / 命令都还在，用户知道发生了什么。
    """
    import os

    from zmlx.ui import gui
    from zmlx.ui.pyqt import QtCore, QWebEngineSettings, QWebEngineView

    if not isinstance(fname, str):
        print(f'The given fname is not a string: {fname}')
        return None
    if not os.path.isfile(fname) and not fname.startswith('file://'):
        print(f'File not exist: {fname}')
        return None
    if QWebEngineView is None or QWebEngineSettings is None:
        print('QWebEngineView is not installed. '
              '请先执行 `pip install PyQt6-WebEngine` 并重启本程序。')
        return None

    def oper(w):
        # ★ 历史标签页的重放代码 —— 格式与 ``MainWindow.open_pdf`` 时期**必须一致**。
        kwds = dict(fname=fname, caption=caption, on_top=on_top)
        w.gui_restore = f"""gui.open_pdf(**{kwds})"""

        # ⚠️⚠️ **``settings()``，不是 ``_settings()``**（2026-10-22 实测修）：
        #    ``_settings`` 是 **PyQt5** 才有的私有方法；**PyQt6 下 ``QWebEngineView`` 上
        #    没有这个名字**，调用会抛
        #    ``AttributeError: 'QWebEngineView' object has no attribute '_settings'``，
        #    结果是「点了 PDF 什么都没打开」。
        #    公开方法 ``settings()`` 两种绑定都有，返回的 ``QWebEngineSettings`` 也都有
        #    ``setAttribute`` —— 所以**统一用它**，不要再写 ``_settings``。
        #    ⚠️ 原来的 ``MainWindow.open_pdf`` 写的就是 ``_settings``，那是**旧代码里
        #    一直存在的 bug**（PyQt6 下 PDF 从来打不开），只是随本次搬迁才暴露出来。
        ws = w.settings()
        ws.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

        if fname.startswith('file://'):
            w.load(QtCore.QUrl(fname))
        else:
            w.load(QtCore.QUrl(
                QtCore.QUrl.fromLocalFile(os.path.abspath(fname)).toString()))

    if caption is None:
        caption = os.path.basename(fname)

    # ⚠️ 走 ``gui.get_widget``（由 GUI 线程执行），不要在插件里直接造控件。
    return gui.get_widget(the_type=QWebEngineView, caption=caption,
                          on_top=on_top, oper=oper)


@execute_once(file=__file__)
def setup_ui():
    """注册 ``gui.open_pdf`` 命令与 ``.pdf`` 文件类型（插件被执行时调一次）."""
    from zmlx.ui import gui

    gui.add_func('open_pdf', open_pdf)
    gui.add_file_handler('PDF文件', ['.pdf'], {'open_file': open_pdf})


# ⚠️ 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以本文件
#    把调用写在**模块顶层**的这个分支里（``setups/*.py`` 则由
#    ``setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
#    插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``；直接 ``python pdf_view.py``
#    时才是 ``'__main__'``（见 plugins/__init__.py 的说明）。
if __name__ == '__zml_plugin__':
    setup_ui()
