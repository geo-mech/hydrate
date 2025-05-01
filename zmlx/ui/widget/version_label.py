from zml import core
from zmlx.ui.widget.my_label import Label


class VersionLabel(Label):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            text = core.time_compile.split(',')[0]
            self.setText(f'Version: {text}')
        except:
            self.setText('Version: ERROR')
        self.set_status('程序内核版本，双击显示详细内容')

    def mouseDoubleClickEvent(self, event):
        """
        在鼠标双击的时候，清除所有的内容
        """
        try:
            from zmlx.ui.main_window import get_window
            get_window().trigger('about')
        except Exception as e:
            print(e)
        super().mouseDoubleClickEvent(event)  # 调用父类的事件处理
