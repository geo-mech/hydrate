import sys

qt_name = None

if qt_name is None:
    if "PyQt6" in sys.modules:  # 之前已经导入了PyQt6 (直接使用)
        from PyQt6 import QtCore, QtGui, QtWidgets

        qt_name = "PyQt6"
        print("PyQt6 is already imported.")

if qt_name is None:
    if "PyQt5" in sys.modules:  # 之前已经导入了PyQt5 (直接使用)
        from PyQt5 import QtCore, QtGui, QtWidgets

        qt_name = "PyQt5"
        print("PyQt5 is already imported.")

if qt_name is None:
    from zmlx.system import is_headless

    if is_headless():
        qt_name = ""
        print("Headless mode is enabled.")


if qt_name is None:
    from zmlx.system import app_data

    text = app_data.getenv(key="Qt_version", default="")
    if text == "PyQt6":
        try:
            from PyQt6 import QtCore, QtGui, QtWidgets

            qt_name = "PyQt6"
            print("User selected PyQt6.")
        except ImportError:
            print("User selected PyQt6 not Found.")
    elif text == "PyQt5":
        try:
            from PyQt5 import QtCore, QtGui, QtWidgets

            qt_name = "PyQt5"
            print("User selected PyQt5.")
        except ImportError:
            print("User selected PyQt5 not Found.")

if qt_name is None:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets

        qt_name = "PyQt6"
        print("PyQt6 is imported.")
    except:
        pass

if qt_name is None:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets

        qt_name = "PyQt5"
        print("PyQt5 is imported.")
    except:
        pass

if qt_name is None:
    qt_name = ""

is_pyqt5 = qt_name == "PyQt5"
is_pyqt6 = qt_name == "PyQt6"

# QWebEngineView需要在程序正式运行之前来导入
try:
    if is_pyqt6:
        from PyQt6.QtWebEngineCore import QWebEngineSettings
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    elif is_pyqt5:
        from PyQt5.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
    else:
        QWebEngineView = None
        QWebEngineSettings = None
except Exception as e:
    print(f"Error: {e}")
    QWebEngineView = None
    QWebEngineSettings = None

try:
    if is_pyqt6:
        from PyQt6.QtGui import QAction
    elif is_pyqt5:
        from PyQt5.QtWidgets import QAction
    else:
        QAction = None
except Exception as e:
    print(f"Error: {e}")
    QAction = None

try:
    if is_pyqt6:
        from PyQt6 import QtMultimedia
    elif is_pyqt5:
        from PyQt5 import QtMultimedia
    else:
        QtMultimedia = None
except Exception as e:
    print(f"Error: {e}")
    QtMultimedia = None

# 确保不会被PyCharm优化掉
_keep = [
    QtGui,
    QtCore,
    QtWidgets,
    is_pyqt5,
    is_pyqt6,
    QAction,
    QtMultimedia,
    QWebEngineView,
    QWebEngineSettings,
]
