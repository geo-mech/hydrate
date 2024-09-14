try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except Exception as e:
    print(f'Error import QWebEngineView: {e}')
    QWebEngineView = None

from PyQt5 import QtGui, QtCore, QtWidgets

try:
    from PyQt5 import QtMultimedia
except Exception as e:
    print(f'Error import QtMultimedia: {e}')
    QtMultimedia = None

__all__ = ['QtGui', 'QtCore', 'QtWidgets', 'QtMultimedia', 'QWebEngineView']
