from zmlx.ui.alg import open_url
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtWidgets, qt_name, QWebEngineView


class About(QtWidgets.QTableWidget):

    def __init__(self, parent=None):
        super(About, self).__init__(parent)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.setup()

    def setup(self):
        from zmlx import core, get_dir
        import sys
        try:
            from zmlx.exts import lic
            lic_desc = lic.desc
        except:
            lic_desc = '未授权'
        data = [
            ['安装路径', f'{get_dir()}'],
            ['当前版本', f'{core.time_compile}; {core.compiler}'],
            ['版本号', f'{core.version}'],
            ['并行库', f'{core.parallel_impl}'],
            ['DLL函数数量', f'{len(core.get_dll_funcs())}'],
            ['授权情况', f'{lic_desc}'],
            ['Python解释器', sys.executable],
            ['Python版本', sys.version],
            ['Qt版本', qt_name],
            ['QWebEngineView已安装',
             'Yes' if QWebEngineView is not None else 'No'],
            ['网址', 'https://gitee.com/geomech/hydrate'],
            ['通讯作者', '张召彬'],
            ['单位', '中国科学院地质与地球物理研究所'],
            ['联系邮箱', 'zhangzhaobin@mail.iggcas.ac.cn'],
            ['管理员权限', 'Yes' if lic.is_admin else 'No'],
            ['硬件码', f'{lic.usb_serial}'],
        ]
        self.setRowCount(len(data))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['项目', '值', ''])

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 60)

        for i_row in range(len(data)):
            label, value = data[i_row]
            self.setItem(i_row, 0, QtWidgets.QTableWidgetItem(label))
            self.setItem(i_row, 1, QtWidgets.QTableWidgetItem(value))

            # 操作按钮
            btn = None
            if label == '安装路径':
                btn = QtWidgets.QPushButton('ReadMe')
                btn.clicked.connect(lambda: gui.show_readme())
            elif label == '当前版本':
                btn = QtWidgets.QPushButton('更新')
                btn.clicked.connect(self._check_update)
            elif label == '授权情况':
                btn = QtWidgets.QPushButton('注册')
                btn.clicked.connect(lambda: gui.show_reg_tool())
            elif label == '网址':
                btn = QtWidgets.QPushButton('打开')
                btn.clicked.connect(
                    lambda checked, u=value: open_url(u))
            elif label == '硬件码':
                btn = QtWidgets.QPushButton('拷贝')
                btn.clicked.connect(
                    lambda checked, u=value: QtWidgets.QApplication.clipboard().setText(u))
            if btn is not None:
                self.setCellWidget(i_row, 2, btn)

    @staticmethod
    def _check_update():
        """在后台线程中执行 git 更新检查。"""
        from zmlx import get_path

        def task():
            from zmlx.alg import update_by_git
            repo_root = get_path('..')
            print('正在检查更新...')
            ok, msg = update_by_git(cwd=repo_root)
            if ok:
                print(f'更新: {msg}')
            else:
                print(f'更新失败: {msg}')
        gui.start_func(task, add_history=False)


def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = About()
    w.resize(600, 480)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
