import sys


def get_preferred_qt_version():
    """
    获得用户设置的QT版本
    """
    from zml import app_data

    text = app_data.getenv(key='Qt_version', default='')
    if text == 'PyQt5' or text == 'PyQt6':
        return text

    if sys.version_info >= (3, 10):  # Python 版本大于 3.11
        return 'PyQt6'
    else:
        return 'PyQt5'


if __name__ == '__main__':
    print(get_preferred_qt_version())
