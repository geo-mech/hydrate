import subprocess
import sys

from zmlx.ui.pyqt import QtWidgets, QtCore, QtGui


class InstallThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(int)

    def __init__(self, package_name, row):
        super().__init__()
        self.package_name = package_name
        self.row = row

    def run(self):
        try:
            # 创建子进程并捕获输出
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", self.package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            # 实时读取输出
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                print(f"[{self.package_name}]", line.strip())

            # 等待进程结束并检查返回码
            proc.wait()
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, proc.args)

        except subprocess.CalledProcessError as e:
            print(f"安装失败: {e}")
        finally:
            self.finished.emit(self.row)


class PackageTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None, packages=None):
        super().__init__(parent)
        self.setup_ui()
        self.threads = []
        if packages is not None:
            self.set_packages(*packages)

    def setup_ui(self):
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["包名", "状态", "操作"])
        self.horizontalHeader().setSectionResizeMode(0,
                                                     QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

    def set_packages(self, *packages):
        self.clearContents()
        self.setRowCount(len(packages))

        for row, pkg in enumerate(packages):
            # 包名称列
            name_item = QtWidgets.QTableWidgetItem(pkg["package_name"])
            name_item.setData(QtCore.Qt.ItemDataRole.UserRole, pkg)
            self.setItem(row, 0, name_item)

            # 状态列
            status_item = QtWidgets.QTableWidgetItem()
            self.setItem(row, 1, status_item)

            # 操作列
            button = QtWidgets.QPushButton("安装")
            button.setCursor(
                QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            self.setCellWidget(row, 2, button)

            self.update_row_status(row)

    def update_row_status(self, row):
        pkg_data = self.item(row, 0).data(QtCore.Qt.ItemDataRole.UserRole)
        import_name = pkg_data["import_name"]
        button = self.cellWidget(row, 2)

        if self.check_installation(import_name):
            self.item(row, 1).setText("已安装")
            button.setEnabled(False)
            button.setText("已安装")
            button.setStyleSheet("color: #666; background-color: #eee")
        else:
            self.item(row, 1).setText("尚未安装")
            button.setEnabled(True)
            button.setText("安装")
            button.setStyleSheet("")
            button.clicked.connect(lambda: self.start_installation(row))

    def check_installation(self, import_name):
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False

    def start_installation(self, row):
        pkg_data = self.item(row, 0).data(QtCore.Qt.ItemDataRole.UserRole)
        package_name = pkg_data["package_name"]

        # 更新界面状态
        self.item(row, 1).setText("安装中...")
        button = self.cellWidget(row, 2)
        button.setEnabled(False)

        # 创建并启动安装线程
        thread = InstallThread(package_name, row)
        thread.finished.connect(self.handle_install_result)
        self.threads.append(thread)
        thread.start()

    def handle_install_result(self, row):
        self.update_row_status(row)
        # 移除已完成线程
        self.threads = [t for t in self.threads if t.isRunning()]

    @staticmethod
    def get_start_code():
        return """gui.trigger('install_dep')"""


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    table = PackageTable(packages=(
        {"package_name": "numpy", "import_name": "numpy"},
        {"package_name": "scipy", "import_name": "scipy"},
        {"package_name": "pillow", "import_name": "PIL"},
    ))
    table.resize(600, 400)
    table.show()

    sys.exit(app.exec())
