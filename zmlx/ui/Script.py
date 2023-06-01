# -*- coding: utf-8 -*-


import os

from PyQt5 import QtWidgets

from zml import read_text, app_data


class Script:
    def __init__(self, file):
        self.file = file
        text = read_text(path=file, encoding='utf-8', default=None)
        self.config = {}
        if text is not None:
            for line in text.splitlines():
                if len(line) >= 4:
                    if line[0: 4] == '# **':
                        try:
                            exec(line[4:].strip(), None, self.config)
                        except Exception as err:
                            print(err)

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
                app_data.log(f'run <{self.file}>')
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
