from zml import write_text
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets, QAction


class TextBrowser(QtWidgets.QTextBrowser):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = None
        self.context_actions = [create_action(self, "清除内容", icon='clean', slot=self.clear)]

    def contextMenuEvent(self, event):
        # 创建菜单并添加清除动作
        self.get_context_menu().exec(event.globalPos())

    def get_context_menu(self):
        menu = super().createStandardContextMenu()
        menu.addSeparator()
        for action in self.context_actions:
            if isinstance(action, QAction):
                menu.addAction(action)
            else:
                menu.addSeparator()
        return menu

    def set_status(self, text):
        self._status = text

    def enterEvent(self, event):
        if self._status is not None:
            gui.status(self._status, 3000)
        super().enterEvent(event)

    def export_data(self):
        fpath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '导出文本',
            '',
            f'文本文件 (*.txt)')
        if len(fpath) > 0:
            write_text(
                path=fpath, text=self.toPlainText(),
                encoding='utf-8')
