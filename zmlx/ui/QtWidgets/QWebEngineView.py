from zmlx.ui.Qt import is_PyQt6

try:
    if is_PyQt6:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    else:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
except:
    QWebEngineView = None
