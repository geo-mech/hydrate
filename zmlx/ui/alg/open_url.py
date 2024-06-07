from zmlx.ui.Qt import QWebEngineView, QtCore
from zmlx.ui.GuiBuffer import gui
import os


def open_url(url: str, caption=None, on_top=None, zoom_factor=2, use_web_engine=None):
    """
    显示一个htm文件
    """
    if not isinstance(url, str):
        return

    if use_web_engine is None:
        try:
            from zml import app_data
            use_web_engine = app_data.getenv(key='use_web_engine', default='False') == 'True'
        except:
            use_web_engine = False

    if use_web_engine is None:   # 确保其有一个默认的值
        use_web_engine = False

    if QWebEngineView is None:
        use_web_engine = False

    if not gui.exists():
        use_web_engine = False

    if not use_web_engine:
        if os.path.isfile(url):
            os.startfile(url)
        else:
            from webbrowser import open_new_tab
            open_new_tab(url)
    else:
        def f(widget):
            widget.page().setZoomFactor(zoom_factor)
            if os.path.isfile(url):
                widget.load(QtCore.QUrl.fromLocalFile(url))
            else:
                widget.load(QtCore.QUrl(url))

        gui.get_widget(type=QWebEngineView, caption=caption, on_top=on_top, oper=f)


if __name__ == '__main__':
    gui.execute(lambda: open_url('https://gitee.com/geomech/hydrate'),
                close_after_done=False)
