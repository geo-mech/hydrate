import sys


def pyqt6_imported():
    return 'PyQt6' in sys.modules


def pyqt5_imported():
    return 'PyQt5' in sys.modules


qt_name = None

if qt_name is None:
    if pyqt6_imported():  # 之前已经导入了PyQt6
        from PyQt6 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt6'

if qt_name is None:
    if pyqt5_imported():
        from PyQt5 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt5'

if qt_name is None:
    try:
        from PyQt6 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt6'
    except:
        pass

if qt_name is None:
    try:
        from PyQt5 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt5'
    except:
        pass

if qt_name is None:
    qt_name = ''

is_pyqt5 = qt_name == 'PyQt5'
is_pyqt6 = qt_name == 'PyQt6'

# QWebEngineView需要在程序正式运行之前来导入
try:
    if is_pyqt6:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import QWebEngineSettings
    else:
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
except Exception as e:
    print(f'Error when import QWebEngineView: {e}')
    QWebEngineView = None
    QWebEngineSettings = None

if is_pyqt6:
    from PyQt6.QtGui import QAction
else:
    from PyQt5.QtWidgets import QAction

try:
    if is_pyqt6:
        from PyQt6 import QtMultimedia
    else:
        from PyQt5 import QtMultimedia
except:
    QtMultimedia = None

# 所有导出的变量
__all__ = ['QtGui', 'QtCore', 'QtWidgets', 'is_pyqt5', 'is_pyqt6', 'qt_name',
           'QWebEngineView', 'QWebEngineSettings', 'QAction', 'QtMultimedia']
