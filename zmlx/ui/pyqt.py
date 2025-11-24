import sys

from zmlx.base.zml import app_data

qt_name = None

if qt_name is None:
    if 'PyQt6' in sys.modules:  # 之前已经导入了PyQt6 (直接使用)
        from PyQt6 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt6'
        print('PyQt6 is already imported.')

if qt_name is None:
    if 'PyQt5' in sys.modules:  # 之前已经导入了PyQt5 (直接使用)
        from PyQt5 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt5'
        print('PyQt5 is already imported.')

if qt_name is None:
    text = app_data.getenv(key='Qt_version', default='')
    if text == 'PyQt6':
        try:
            from PyQt6 import QtGui, QtCore, QtWidgets

            qt_name = 'PyQt6'
            print('User selected PyQt6.')
        except ImportError:
            print('User selected PyQt6 not Found.')
    elif text == 'PyQt5':
        try:
            from PyQt5 import QtGui, QtCore, QtWidgets

            qt_name = 'PyQt5'
            print('User selected PyQt5.')
        except ImportError:
            print('User selected PyQt5 not Found.')

if qt_name is None:
    try:
        from PyQt6 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt6'
        print('PyQt6 is imported.')
    except:
        pass

if qt_name is None:
    try:
        from PyQt5 import QtGui, QtCore, QtWidgets

        qt_name = 'PyQt5'
        print('PyQt5 is imported.')
    except:
        pass

if qt_name is None:
    qt_name = ''

is_pyqt5 = qt_name == 'PyQt5'
is_pyqt6 = qt_name == 'PyQt6'
assert is_pyqt5 or is_pyqt6, 'please make sure you have installed PyQt6 (Recommended) or PyQt5.'

# QWebEngineView需要在程序正式运行之前来导入
try:
    if is_pyqt6:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import QWebEngineSettings
    else:
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
except Exception as e:
    print(f'Error: {e}')
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
