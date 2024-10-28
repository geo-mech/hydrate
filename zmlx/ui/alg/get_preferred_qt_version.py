
def get_preferred_qt_version():
    """
    获得用户设置的QT版本
    """
    from zml import app_data

    text = app_data.getenv(key='Qt_version', default='')
    if text == 'PyQt5' or text == 'PyQt6':
        return text

    try:
        from PyQt6 import QtGui, QtCore, QtWidgets
        return 'PyQt6'
    except:
        pass

    try:
        from PyQt5 import QtGui, QtCore, QtWidgets
        return 'PyQt5'
    except:
        pass

    return 'PyQt6'
