from zmlx.ui.alg.get_preferred_qt_version import get_preferred_qt_version

_version_text = get_preferred_qt_version()
_version = None

if _version is None:
    if _version_text == 'PyQt6':
        try:
            from PyQt6 import QtGui, QtCore, QtWidgets

            _version = 6
        except:
            pass

if _version is None:
    if _version_text == 'PyQt5':
        try:
            from PyQt5 import QtGui, QtCore, QtWidgets

            _version = 5
        except:
            pass

if _version is None:
    try:
        from PyQt6 import QtGui, QtCore, QtWidgets

        _version = 6
    except:
        pass

if _version is None:
    try:
        from PyQt5 import QtGui, QtCore, QtWidgets

        _version = 5
    except:
        pass

assert _version == 5 or _version == 6
has_PyQt6 = _version == 6

try:
    if has_PyQt6:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6 import QtWebEngineWidgets
    else:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5 import QtWebEngineWidgets
except:
    QWebEngineView = None
    QtWebEngineWidgets = None

try:
    if has_PyQt6:
        from PyQt6 import QtMultimedia
    else:
        from PyQt5 import QtMultimedia
except:
    QtMultimedia = None

if has_PyQt6:
    from PyQt6.QtGui import QAction
else:
    from PyQt5.QtWidgets import QAction

if has_PyQt6:
    def screen_size():
        return QtWidgets.QApplication.primaryScreen().availableGeometry()
else:
    def screen_size():
        return QtWidgets.QDesktopWidget().availableGeometry()

__all__ = ['QtGui', 'QtCore', 'QtWidgets', 'QtMultimedia', 'QWebEngineView', 'has_PyQt6',
           'QAction', 'screen_size']
