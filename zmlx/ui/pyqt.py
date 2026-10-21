"""PyQt 版本自动适配。

按优先级检测：已导入的 PyQt6/PyQt5 → 用户环境变量 Qt_version →
尝试 PyQt6 → 尝试 PyQt5。无头模式下跳过 Qt 导入。
同时导出 QtCore、QtGui、QtWidgets、QAction、QtMultimedia、QWebEngineView 等常用模块。

选定绑定后会设置 QT_API / FORCE_QT_API，强制 qtpy 以及所有依赖它的库
（pyvistaqt、pyqtribbon 等）跟随同一绑定，避免两套绑定混用导致原生崩溃。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-09-14
"""

import os
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
    except Exception:
        pass

if qt_name is None:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets

        qt_name = "PyQt5"
        print("PyQt5 is imported.")
    except Exception:
        pass

if qt_name is None:
    qt_name = ""

is_pyqt5 = qt_name == "PyQt5"
is_pyqt6 = qt_name == "PyQt6"

# 无头模式（或绑定导入失败）时，上面并没有导入任何 Qt 模块。
# 显式置空，保证这些模块级的名字始终存在，避免下游 import 时抛 NameError。
if not (is_pyqt5 or is_pyqt6):
    QtCore = QtGui = QtWidgets = None

# 把选定的绑定钉死，让后续所有 qtpy 使用者强制跟随本程序的选择。
# qtpy 的规则是：默认 PyQt5，且"已导入者获胜"、而 PyQt5 又排在 PyQt6 之前；
# 它一旦选到与实际不同的绑定，两套绑定混用会直接导致原生崩溃 (0xC0000409)，
# 且 Python 层无法捕获。FORCE_QT_API 用于关闭 qtpy 的"已导入优先"规则。
if is_pyqt5 or is_pyqt6:
    os.environ['QT_API'] = 'pyqt5' if is_pyqt5 else 'pyqt6'
    os.environ['FORCE_QT_API'] = '1'
    if 'qtpy' in sys.modules:
        print('Warning: qtpy was imported before the Qt binding was pinned; '
              'the already-imported binding takes precedence.')

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
