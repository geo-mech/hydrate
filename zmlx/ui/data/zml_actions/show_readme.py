# ** on_toolbar = True
# ** icon = 'info.png'

import os

from PyQt5 import QtWidgets

import zml


def set_md(widget):
    assert isinstance(widget, QtWidgets.QTextBrowser)
    widget.setOpenLinks(True)
    widget.setOpenExternalLinks(True)
    path = os.path.join(os.path.dirname(zml.__file__), 'README.md')
    if os.path.isfile(path):
        widget.setMarkdown(zml.read_text(path=path, encoding='utf-8'))


zml.gui.get_widget(type=QtWidgets.QTextBrowser, caption='ReadMe',
                   on_top=True, oper=set_md)
