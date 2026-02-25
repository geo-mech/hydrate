from zml import core
from zmlx.ui.gui_buffer import gui
from zmlx.ui.widget.label import Label


class ConsoleStateLabel(Label):
    def __init__(self, parent=None):
        super().__init__(parent)

        try:
            text = core.time_compile.split(',')[0]
            self.default_text = f'Version: {text}'
        except:
            self.default_text = 'Version: ERROR'

        self.setText('')
        self.set_status('双击显示程序内核的详细内容')
        self.sig_double_clicked.connect(lambda: gui.show_about())

    def setText(self, a0):
        if len(a0) == 0:
            a0 = self.default_text
        super().setText(a0)
