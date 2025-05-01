from zml import write_text, app_data
from zmlx.ui.alg import create_action
from zmlx.ui.qt import QtWidgets


class TextBrowser(QtWidgets.QTextBrowser):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = None

    def contextMenuEvent(self, event):
        # 创建菜单并添加清除动作
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = super().createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(create_action(self, "清除内容", 'clean', self.clear))
        return menu

    def set_status(self, text):
        self._status = text

    def enterEvent(self, event):
        if self._status is not None:
            window = app_data.get('main_window')
            if window is not None:
                window.cmd_status(self._status, 3000)
        super().enterEvent(event)

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(self, '导出文本',
                                                         '',
                                                         f'文本文件 (*.txt)')
        if len(fpath) > 0:
            write_text(path=fpath, text=self.toPlainText(), encoding='utf-8')
