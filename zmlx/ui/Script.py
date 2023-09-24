import os

from zml import app_data, read_text
from zmlx.ui.Qt import QtWidgets
from zmlx.ui.alg.code_config import code_config


class Script:
    def __init__(self, file):
        self.file = file
        self.config = code_config(path=file, encoding='utf-8')

    def __call__(self, win):
        assert win is not None
        if not os.path.isfile(self.file):
            return

        def show_err(e):
            info = f'Meet error when run <{self.file}>. \nInfo = \n {e}'
            print(info)
            QtWidgets.QMessageBox.information(win, 'Error', info)

        if self.is_sys:
            try:
                app_data.log(f'system run <{self.file}>')
                exec(read_text(path=self.file, encoding='utf-8', default=''),
                     win.console_widget.workspace)
            except Exception as err:
                show_err(err)
        else:
            try:
                win.console_widget.exec_file(self.file)
            except Exception as err:
                show_err(err)

    @property
    def enabled(self):
        try:
            exec(self.config.get('dependency', ''))
            return True
        except:
            return False

    @property
    def is_sys(self):
        return self.config.get('is_sys', False)

    @property
    def text(self):
        return self.config.get('text', os.path.basename(self.file))

    @property
    def name(self):
        return self.config.get('name', None)

    @property
    def icon(self):
        return self.config.get('icon', None)

    @property
    def on_toolbar(self):
        return self.config.get('on_toolbar', False)

    @property
    def tooltip(self):
        return self.config.get('tooltip', None)

    @property
    def menu(self):
        return self.config.get('menu', None)
