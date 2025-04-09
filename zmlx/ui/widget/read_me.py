import os

from zml import get_dir, read_text
from zmlx.ui.widget.text_browser import TextBrowser


class ReadMeBrowser(TextBrowser):
    def __init__(self, parent=None):
        super(ReadMeBrowser, self).__init__(parent)
        path = os.path.join(get_dir(), 'README.md')
        if os.path.isfile(path):
            self.setOpenLinks(True)
            self.setOpenExternalLinks(True)
            self.setMarkdown(read_text(path=path, encoding='utf-8'))
            self.set_status(path)

    @staticmethod
    def get_start_code():
        return """gui.trigger('readme')"""
