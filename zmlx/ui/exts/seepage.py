from zmlx import Seepage, gui
from zmlx.ui.pyqt import QtWidgets


class View(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self._init_ui()
        self.set_data(Seepage())

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.note_edit = QtWidgets.QTextEdit(self)
        self.note_edit.textChanged.connect(
            lambda: self.data.set_text('note', self.note_edit.toPlainText()))
        layout.addWidget(self.note_edit)
        self.summary_label = QtWidgets.QLabel(self)
        layout.addWidget(self.summary_label)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        self.note_edit.setPlainText(self.data.get_text('note'))
        self.summary_label.setText(
            f"cell_n={self.data.cell_number}, face_n={self.data.face_number}")


def setup_ui():
    gui.reg_file_type(
        'Seepage文件', ['.seepage', '.xml', '.txt'],
        name='seepage',
        save=lambda data, name: data.save(name),
        load=lambda name: Seepage(path=name),
        init=lambda: Seepage(),
        widget_type=View
    )


def main():
    from zmlx.alg.sys import first_execute
    if first_execute(__file__):
        gui.execute(func=setup_ui, keep_cwd=False, close_after_done=False)


if __name__ == '__main__':
    main()
