# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets


def v_spacer():
    return QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)


def h_spacer():
    return QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
