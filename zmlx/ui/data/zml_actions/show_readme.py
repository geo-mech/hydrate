# ** on_toolbar = True

import zml
from PyQt5 import QtWidgets
import os


def set_md(widget):
    path = os.path.join(os.path.dirname(zml.__file__), 'README.md')
    if os.path.isfile(path):
        widget.setMarkdown(zml.read_text(path=path, encoding='utf-8'))


zml.gui.get_widget(type=QtWidgets.QTextBrowser, caption='ReadMe',
                   on_top=True, oper=set_md)
