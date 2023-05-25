# -*- coding: utf-8 -*-


import os

from zml import gui, app_data


def code_is_in_editing(fname):
    """
    查找Python文件是否在界面中正在被编辑
    """
    if not gui.exists():
        return False

    def samefile(x, y):
        try:
            return os.path.samefile(x, y)
        except:
            return False

    window = gui.window()

    if samefile(fname, window.console_widget.get_fname()):
        return True

    from zmlx.ui.CodeEdit import CodeEdit
    for i in range(window.tab_widget.count()):
        widget = window.tab_widget.widget(i)
        if isinstance(widget, CodeEdit):
            if samefile(fname, widget.get_fname()):
                return True

    return False


def edit_code(fname, warning=True):
    if not gui.exists() or not isinstance(fname, str):
        return
    if len(fname) > 0:
        if code_is_in_editing(fname):
            if warning:
                gui.information('Warning', f'文件已在编辑: {fname}')
        else:
            from zmlx.ui.CodeEdit import CodeEdit
            widget = gui.get_widget(type=CodeEdit, caption=os.path.basename(fname),
                                    on_top=True,
                                    oper=lambda x: x.open(fname))
            tag = 'tip_shown_when_edit_code'
            if widget.get_fname() == fname and not app_data.has_tag_today(tag):
                gui.about('成功', '文件已打开，请点击工具栏上的<执行>按钮以执行')
                app_data.add_tag_today(tag)


def open_edit_code():
    if not gui.exists():
        return
    fname = gui.get_open_file_name(caption='打开现有的.py脚本', directory=os.getcwd(),
                                   filter='Python File (*.py);;')
    edit_code(fname)


def new_edit_code():
    if not gui.exists():
        return
    fname = gui.get_save_file_name(caption='新建.py脚本', directory=os.getcwd(),
                                   filter='Python File (*.py);;')
    edit_code(fname)


def exec_code_in_editing():
    if not gui.exists():
        return
    current = gui.window().tab_widget.currentWidget()
    from zmlx.ui.CodeEdit import CodeEdit
    if isinstance(current, CodeEdit):
        current.save()
        gui.window().console_widget.exec_file(current.get_fname())
    else:
        gui.information('失败', '请首先定位到脚本页面')
