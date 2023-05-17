# -*- coding: utf-8 -*-

import sys

from PyQt5 import QtWidgets


def show_widget(widget, width=800, height=600, *args, **kwargs):
    app = QtWidgets.QApplication(sys.argv)
    w = widget(*args, **kwargs)
    w.show()
    w.resize(width, height)
    sys.exit(app.exec_())
