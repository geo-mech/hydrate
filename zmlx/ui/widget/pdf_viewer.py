import os.path

from zmlx.ui.qt import is_PyQt6, QWebEngineView, QWebEngineSettings, QtCore


class PDFViewer(QWebEngineView):
    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        # 启用PDF支持
        if is_PyQt6:
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            self.settings().setAttribute(
                QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        else:
            self.settings().setAttribute(QWebEngineSettings.PluginsEnabled,
                                         True)
        if file_path is not None:
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        """直接加载本地PDF文件"""
        if not file_path.startswith("file://"):
            file_path = os.path.abspath(file_path)
            file_path = QtCore.QUrl.fromLocalFile(file_path).toString()
        self.load(QtCore.QUrl(file_path))
