import os

from zml import app_data, read_text
from zmlx.ui.Qt import QtWidgets
from zmlx.ui.alg.code_config import code_config


class Script:
    def __init__(self, file):
        assert file is not None
        self.file = file
        self.config = code_config(path=file, encoding='utf-8')

    def __call__(self, win):
        if not os.path.isfile(self.file):
            return
        try:
            assert win is not None, 'Main window is not given when run script'
            if self.is_sys:
                exec(read_text(path=self.file, encoding='utf-8', default=''),
                     win.get_workspace())
                app_data.log(f'system run <{self.file}>')
            else:
                win.exec_file(self.file)
        except Exception as err:
            info = f'meet error when run <{self.file}>. \nInfo = \n {err}'
            print(info)
            app_data.log(info)

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
