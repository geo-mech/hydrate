import os

from zml import read_text
from zmlx.ui.alg import create_action
from zmlx.ui.gui_buffer import gui
from zmlx.ui.widget.text_browser import TextBrowser


class ReadMeBrowser(TextBrowser):
    def __init__(self, parent=None):
        super(ReadMeBrowser, self).__init__(parent)
        self._load()
        self.context_actions.append(create_action(self, "重新导入并显示ReadMe", slot=self._load))
        self.context_actions.append(create_action(self, "关于", slot=gui.show_about))
        self.context_actions.append(create_action(self, "注册", slot=gui.show_reg_tool))

    def _load(self):
        from zmlx import get_path
        path = get_path('..', 'README.md')
        if os.path.isfile(path):
            self.setOpenLinks(True)
            self.setOpenExternalLinks(True)
            self.setMarkdown(read_text(path=path, encoding='utf-8'))
            self.set_status(path)
