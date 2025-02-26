from zmlx.ui.alg.get_preferred_qt_version import get_preferred_qt_version

__text = get_preferred_qt_version()
QtName = None

if QtName is None:
    if __text == 'PyQt6':
        try:
            from PyQt6 import QtGui, QtCore, QtWidgets
            QtName = 'PyQt6'
        except:
            pass

if QtName is None:
    if __text == 'PyQt5':
        try:
            from PyQt5 import QtGui, QtCore, QtWidgets
            QtName = 'PyQt5'
        except:
            pass

if QtName is None:
    try:
        from PyQt6 import QtGui, QtCore, QtWidgets
        QtName = 'PyQt6'
    except:
        pass

if QtName is None:
    try:
        from PyQt5 import QtGui, QtCore, QtWidgets
        QtName = 'PyQt5'
    except:
        pass

if QtName is None:
    QtName = ''

is_PyQt5 = QtName == 'PyQt5'
is_PyQt6 = QtName == 'PyQt6'

__all__ = ['QtGui', 'QtCore', 'QtWidgets', 'is_PyQt5', 'is_PyQt6', 'QtName']

