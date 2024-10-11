import sys

import fitz  # PyMuPDF
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QScrollArea


class PDFViewer(QScrollArea):
    def __init__(self, pdf_path):
        super().__init__()
        # Widget to hold all pages

        self.setWidgetResizable(True)

        # Widget to hold all pages
        self.pdf_widget = QWidget()
        self.pdf_layout = QVBoxLayout(self.pdf_widget)
        self.load_pdf(pdf_path)
        self.setWidget(self.pdf_widget)

    def load_pdf(self, pdf_path):
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)

        # Iterate through each page
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)  # Load page
            pix = page.get_pixmap()  # Render page to image

            # Create QImage from the Pixmap
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            qpixmap = QPixmap.fromImage(img)  # Convert to QPixmap

            label = QLabel()  # Create label for image
            label.setPixmap(qpixmap)  # Set pixmap to label
            self.pdf_layout.addWidget(label)  # Add label to layout

        pdf_document.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PDFViewer("xxx.pdf")  # 替换为PDF文件路径
    viewer.show()
    sys.exit(app.exec_())
