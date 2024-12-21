from zmlx.ui.Config import *
from zmlx.ui.Qt import QAction


class ActionX(QAction):
    def __init__(self, parent, file=None):
        super().__init__(parent)
        self._window = parent
        self._file = None
        self._data = {}
        self._err = None
        if file is not None:
            self._load_setting(file)

    def get(self, name, value=None):
        return self._data.get(name, value)

    def _load_setting(self, file):
        """
        从文件中读取设置
        """
        self._file = file
        if isinstance(file, str):
            text = read_text(path=file, encoding='utf-8',
                             default=None)
            try:
                exec(text, {'__name__': ''}, self._data)
            except Exception as err:
                self._err = err

        iconname = self._data.get('icon', None)
        if iconname is not None:
            self.setIcon(load_icon(iconname))
        else:
            self.setIcon(load_icon('python.jpg'))

        tooltip = self._data.get('tooltip', None)
        if tooltip is not None:
            self.setToolTip(get_text(tooltip))

        text = self._data.get('text', None)
        if text is not None:
            self.setText(get_text(text))

        def slot():
            try:
                self._data.get('slot')()
                app_data.log(f'run <{self._file}>')
                self._window.refresh()  # since 2024-10-11
            except Exception as e2:
                info = f'meet error when run <{self._file}>. \nInfo = \n {e2}'
                print(info)
                app_data.log(info)

        self.triggered.connect(slot)

    def update_view(self):
        enabled = self._is_enabled()
        self.setEnabled(enabled)
        if self._always_show():
            self.setVisible(True)
        else:
            self.setVisible(enabled)

    def _is_enabled(self):
        if self._err is not None:  # 解析文件的时候出现错误，直接不可用
            return False

        try:
            exec(self._data.get('dependency', ''), {})
        except:
            return False  # 依赖项错误，则直接不可用

        value = self._data.get('enabled')

        if value is None:  # 没有定义，则默认可用
            return True

        if hasattr(value, '__call__'):
            try:
                res = value()
                return False if res is None else res
            except Exception as err:
                print(err)
                return False
        else:
            return value

    def _always_show(self):
        """
        即便在没有激活的情况下也显示
        """
        value = self._data.get('always_show')
        if value is None:
            return False

        if hasattr(value, '__call__'):
            try:
                res = value()
                return False if res is None else res
            except Exception as err:
                print(err)
                return False  # 出错，则不显示
        else:
            return value
