import sys


def pyqt6_imported():
    return 'PyQt6' in sys.modules


def pyqt5_imported():
    return 'PyQt5' in sys.modules


QtName = None

if QtName is None:
    if pyqt6_imported():  # 之前已经导入了PyQt6
        from PyQt6 import QtGui, QtCore, QtWidgets

        QtName = 'PyQt6'

if QtName is None:
    if pyqt5_imported():
        from PyQt5 import QtGui, QtCore, QtWidgets

        QtName = 'PyQt5'

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

# QWebEngineView需要在程序正式运行之前来导入
try:
    if is_PyQt6:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import QWebEngineSettings
    else:
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
except Exception as e:
    print(f'Error when import QWebEngineView: {e}')
    QWebEngineView = None
    QWebEngineSettings = None

# 所有导出的变量
__all__ = ['QtGui', 'QtCore', 'QtWidgets', 'is_PyQt5', 'is_PyQt6', 'QtName',
           'QWebEngineView', 'QWebEngineSettings']
