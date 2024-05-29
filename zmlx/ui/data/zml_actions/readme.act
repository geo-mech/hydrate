# ** on_toolbar = True
# ** icon = 'info.png'
# ** text = 'ReadMe'
# ** is_sys = True

import os

import zml
from zmlx.ui.GuiBuffer import gui
from zmlx.ui.Qt import QtWidgets


def set_md(widget):
    assert isinstance(widget, QtWidgets.QTextBrowser)
    widget.setOpenLinks(True)
    widget.setOpenExternalLinks(True)
    path = os.path.join(os.path.dirname(zml.__file__), 'README.md')
    if os.path.isfile(path):
        widget.setMarkdown(zml.read_text(path=path, encoding='utf-8'))


gui.get_widget(type=QtWidgets.QTextBrowser, caption='ReadMe',
               on_top=True, oper=set_md, icon='info.png')
