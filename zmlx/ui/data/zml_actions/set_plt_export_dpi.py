text = '设置导出plt图的DPI'
menu = '设置'


def slot():
    from zmlx.io.env import plt_export_dpi
    from zmlx.ui.pyqt import QtWidgets
    from zmlx.ui.main_window import get_window

    number, ok = QtWidgets.QInputDialog.getDouble(
        get_window(),
        '设置导出图的DPI',
        'DPI',
        plt_export_dpi.get_value(), 50, 3000)
    if ok:
        plt_export_dpi.set_value(number)
