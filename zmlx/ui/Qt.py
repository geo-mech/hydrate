try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except:
    QWebEngineView = None

from PyQt5 import QtGui, QtCore, QtWidgets

try:
    from PyQt5 import QtMultimedia
except:
    QtMultimedia = None

__all__ = ['QtGui', 'QtCore', 'QtWidgets', 'QtMultimedia', 'QWebEngineView']
