from zml import app_data


def create_action(parent, text, icon=None, slot=None):
    from zmlx.ui.settings import load_icon
    from zmlx.ui.pyqt import QAction
    from zmlx.ui.gui_buffer import gui
    ac = QAction(text, parent)
    if icon is not None:
        ac.setIcon(load_icon(icon))
    else:
        ac.setIcon(load_icon('python'))
    if slot is not None:
        assert callable(slot), 'slot must be callable'
        def func():
            slot()
            gui.refresh()
        ac.triggered.connect(func)
    return ac


def add_code_history(fname):
    try:
        import os
        import shutil

        from zml import app_data
        from zmlx.alg.fsys import time_string
        if os.path.isfile(fname):
            t_str = time_string()
            shutil.copy(
                fname, app_data.root('console_history', f'{t_str}.py'))
            with open(app_data.root('console_history', f'{t_str}.txt'),
                      'w', encoding='utf-8') as file:  # 记录原文件的位置.
                file.write(fname)
    except Exception as err:
        print(f"Error (when add_code_history): {err}")


def add_exec_history(code):
    key = 'console_exec_history'
    history = app_data.get(key, [])
    if not isinstance(history, list):
        history = []
    history.append(code)
    app_data.put(key, history)


def get_last_exec_history():
    key = 'console_exec_history'
    history = app_data.get(key, [])
    if not isinstance(history, list):
        return None
    if len(history) > 0:
        return history[-1]
    else:
        return None


def paint_image(widget, pixmap):
    """
    显示图片代码参考：
    https://vimsky.com/examples/detail/python-ex-PyQt5.Qt-QPainter-drawPixmap-method.html
    """
    if pixmap is None or widget is None:
        return
    try:
        from zmlx.ui.pyqt import QtGui, QtCore
        width = widget.rect().width()
        height = widget.rect().height()
        if pixmap.width() / pixmap.height() > width / height:
            fig_h = width * pixmap.height() / pixmap.width()
            x = (widget.rect().width() - width) / 2
            y = (height - fig_h) / 2 + (widget.rect().height() - height) / 2
            target = QtCore.QRect(int(x), int(y), int(width), int(fig_h))
        else:
            fig_w = height * pixmap.width() / pixmap.height()
            x = (width - fig_w) / 2 + (widget.rect().width() - width) / 2
            y = (widget.rect().height() - height) / 2
            target = QtCore.QRect(int(x), int(y), int(fig_w), int(height))
        painter = QtGui.QPainter(widget)
        painter.setRenderHints(
            QtGui.QPainter.RenderHint.Antialiasing)
        try:
            dpr = widget.devicePixelRatioF()
        except AttributeError:
            dpr = widget.devicePixelRatio()
        pixmap_scaled = pixmap.scaled(
            target.size() * dpr,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation)
        pixmap_scaled.setDevicePixelRatio(dpr)
        painter.drawPixmap(target, pixmap_scaled)
        painter.end()
    except Exception as err:
        print(f"Error (when paint_image): {err}")


def get_current_screen_geometry(window):
    """获取窗口所在显示器的尺寸"""
    from zmlx.ui.pyqt import QtWidgets, is_pyqt6
    if is_pyqt6:
        screen = window.screen() if window else None
        if screen:
            return screen.availableGeometry()
        else:
            return None
    else:
        desktop = QtWidgets.QDesktopWidget()
        return desktop.availableGeometry(desktop.screenNumber(window))


def v_spacer():
    from zmlx.ui.pyqt import QtWidgets
    return QtWidgets.QSpacerItem(
        40, 20, QtWidgets.QSizePolicy.Policy.Minimum,
        QtWidgets.QSizePolicy.Policy.Expanding)


def h_spacer():
    from zmlx.ui.pyqt import QtWidgets
    return QtWidgets.QSpacerItem(
        40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
        QtWidgets.QSizePolicy.Policy.Minimum)


def open_url(url: str, caption=None, on_top=None, zoom_factor=None,
             use_web_engine=None, icon=None):
    """
    显示一个htm文件
    """
    import os
    from zmlx.ui.gui_buffer import gui
    from zmlx.ui.pyqt import QWebEngineView

    if not isinstance(url, str):
        return

    if use_web_engine is None:
        try:
            from zml import app_data
            use_web_engine = app_data.getenv(
                key='use_web_engine',
                default='Yes',
                ignore_empty=True) != 'No'
        except Exception as err:
            print(err)
            use_web_engine = False

    if use_web_engine is None:  # 确保其有一个默认的值
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
        gui.open_url(
            url=url, caption=caption, on_top=on_top,
            zoom_factor=zoom_factor, icon=icon)


def show_widget(widget, caption=None, use_gui=False, **kwargs):
    if use_gui:
        from zmlx.ui import gui

        def f():
            gui.get_widget(the_type=widget, type_kw=kwargs, caption=caption)

        gui.execute(f, keep_cwd=False,
                    close_after_done=False)
    else:
        import sys
        from zmlx.ui.pyqt import QtWidgets
        app = QtWidgets.QApplication(sys.argv)
        w = widget(**kwargs)
        w.show()
        sys.exit(app.exec())
