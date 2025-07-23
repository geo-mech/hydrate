from zml import app_data, get_hash
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets


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


def modify_file_exts(exts):
    """
    对文件扩展名进行处理
    """
    exts = [e.lower() for e in exts]
    for i in range(len(exts)):
        assert len(exts[i]) > 0, f'The file extension should not be empty'
        if exts[i][0] != '.':
            exts[i] = '.' + exts[i]
    return exts


def reg_file_type(desc, exts, name, save, load, init, widget_type):
    """
    注册一种文件类型，设置其保存、新建、打开等过程的行为.
    Args:
        desc: 文件类型的描述
        exts: 支持的扩展名列表
        name: 文件的名字. 和desc不同，这里的name必须是一个变量，从而用户注册 open_xxx这样的函数
        save: save(data, filename)，用于将数据存储到文件
        load: load(filename) 读取文件的函数
        init: init() 返回初始化之后的数据的函数
        widget_type: 编辑器控件类型。此类需要有set_data和get_data函数.
    Returns:
        None
    """
    if isinstance(exts, str):
        exts = [exts]

    exts = modify_file_exts(exts)

    if name is None:
        name = get_hash(desc)  # 默认，此时函数的名称将是乱码

    file_filter = desc
    file_filter += ' ('
    for ext in exts:
        file_filter += f'*{ext}; '
    file_filter += ')'

    def open_file(filename):
        import os
        def oper(x):
            if callable(load) and hasattr(x, 'set_data'):  # 只有此时，才能够导入数据
                try:
                    x.set_data(load(filename))
                except Exception as err:
                    print(err)

            if not hasattr(x, 'gui_restore'):  # 新添加的一个函数
                x.gui_restore = f"gui.open_{name}(r'{filename}')"

            if not hasattr(x, 'save_file'): # 尝试添加保存文件的操作
                if hasattr(x, 'get_data') and callable(save):
                    def save_file():
                        try:
                            save(x.get_data(), filename)
                            print(f'成功保存到:\n{filename}')
                        except Exception as e:
                            print(e)
                    x.save_file = save_file

            if not hasattr(x, 'export_data'):  # 尝试支持导出操作
                if hasattr(x, 'get_data') and callable(save):
                    def export_data():
                        name2, _ = QtWidgets.QFileDialog.getSaveFileName(
                            x, '导出文件', os.getcwd(), file_filter)
                        if name2:
                            try:
                                save(x.get_data(), name2)
                            except Exception as e:
                                print(e)
                    x.export_data = export_data

            if not hasattr(x, 'import_data'):  # 尝试支持导入操作
                if hasattr(x, 'set_data') and callable(load):
                    def import_data():
                        name2, _ = QtWidgets.QFileDialog.getOpenFileName(
                            x, '选取文件', os.getcwd(), file_filter)
                        if name2:
                            try:
                                x.set_data(load(name2))
                            except Exception as e:
                                print(e)
                    x.import_data = import_data

        gui.get_widget(widget_type, os.path.basename(filename), oper=oper)

    if callable(init):
        def new_file(filename):
            from zml import make_parent
            try:
                save(init(), make_parent(filename))
            except Exception as e:
                print(e)
    else:
        new_file = None  # 此时，将不支持“新建”操作

    gui.add_func(f'open_{name}', open_file)
    gui.add_file_handler(
        desc, exts,
        {'open_file': open_file, 'new_file': new_file})


def edit_in_tab(widget_type, set_data, get_data=None, caption=None):
    """
    在另外一个标签里面，使用给定的编辑器控件去编辑数据. 这个给定的控件，需要有get_data和set_data函数
    """
    def do_init(widget):
        layout = QtWidgets.QVBoxLayout(widget)
        widget.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        editor = widget_type(widget)
        if callable(get_data) and hasattr(editor, 'set_data'):
            try:
                editor.set_data(get_data())
            except Exception as err:
                print(err)
        layout.addWidget(editor)

        button_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(button_layout)

        def ok_clicked():
            try:
                if hasattr(editor, 'get_data') and callable(set_data):
                    set_data(editor.get_data())
            except Exception as e:
                print(e)
                QtWidgets.QMessageBox.information(
                    widget, '设置数据错误', str(e))
            gui.close_tab_object(widget)

        def cancel_clicked():
            gui.close_tab_object(widget)

        button_layout.addItem(h_spacer())

        button_ok = QtWidgets.QPushButton('确定')
        button_ok.clicked.connect(ok_clicked)
        button_layout.addWidget(button_ok)

        button_cancel = QtWidgets.QPushButton('取消')
        button_cancel.clicked.connect(cancel_clicked)
        button_layout.addWidget(button_cancel)

    if caption is None:
        caption = f'Edit Data(id={id(set_data)})'
    gui.get_widget(
        QtWidgets.QWidget, caption=caption,
        init=do_init, on_top=True)


