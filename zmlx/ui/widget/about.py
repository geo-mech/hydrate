"""关于对话框（版本信息、更新日志、操作按钮）.

Modified by Claude, 2026-08-12
"""

from zmlx.ui.alg import open_url
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets, qt_name, QWebEngineView


def _get_pyproject_version():
    """从 pyproject.toml 读取版本号，失败时返回 None.

    Added by DeepSeek, 2026-08-19
    """
    import os
    import re
    from zmlx import get_path
    from zmlx.system import read_text

    try:
        path = get_path('..', 'pyproject.toml')
        if not os.path.isfile(path):
            return None
        text = read_text(path=path, encoding='utf-8')
        if not text:
            return None
        m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        return m.group(1) if m else None
    except Exception:
        return None


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
            is_admin = 'Yes' if lic.is_admin else 'No'
        except Exception:
            lic_desc = '未授权'
            is_admin = '未知'
        ver = _get_pyproject_version()
        data = [
            ['安装路径', f'{get_dir()}'],
            ['当前版本', f'{core.time_compile}; {core.compiler}'],
            ['版本号', f'{core.version} (zmlx {ver})' if ver else f'{core.version}'],
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
            ['管理员权限', is_admin],
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
            elif label == '版本号':
                btn = QtWidgets.QPushButton('日志')
                btn.clicked.connect(self._show_changelog)
            elif label == '授权情况':
                btn = QtWidgets.QPushButton('注册')
                btn.clicked.connect(lambda: gui.show_reg_tool())
            elif label == '网址':
                btn = QtWidgets.QPushButton('打开')
                btn.clicked.connect(
                    lambda checked, u=value: open_url(u))
            elif label == '单位':
                btn = QtWidgets.QPushButton('打开')
                btn.clicked.connect(
                    lambda checked: open_url('http://www.igg.cas.cn/'))
            if btn is not None:
                self.setCellWidget(i_row, 2, btn)

    @staticmethod
    def _show_changelog():
        """在新的标签页中显示修改日志."""
        from zmlx import get_path
        from zmlx.ui.widget import TextBrowser
        import os

        path = get_path('..', 'CHANGELOG.md')
        if os.path.isfile(path):
            from zmlx.system import read_text
            text = read_text(path=path, encoding='utf-8')

            def oper(w):
                w.setOpenLinks(True)
                w.setOpenExternalLinks(True)
                w.setMarkdown(text)

            gui.get_widget(
                the_type=TextBrowser, caption='修改日志',
                on_top=True, icon='info', oper=oper)

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

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction('ReadMe', gui.show_readme)
        menu.addAction('更新', self._check_update)
        menu.addAction('日志', self._show_changelog)
        menu.addAction('路线图', self._show_roadmap)
        menu.addAction('注册', gui.show_reg_tool)
        menu.addAction('打开IGG-Hydrate主页',
                       lambda: open_url('https://gitee.com/geomech/hydrate'))
        menu.addAction('打开中科院地质与地球物理研究所主页',
                       lambda: open_url('http://www.igg.cas.cn/'))
        menu.popup(event.globalPos())

    @staticmethod
    def _show_roadmap():
        from zmlx import get_path
        from zmlx.ui.widget import TextBrowser
        from zmlx.system import read_text
        import os
        path = get_path('..', 'ROADMAP.md')
        if os.path.isfile(path):
            text = read_text(path=path, encoding='utf-8')

            def oper(w):
                w.setOpenLinks(True)
                w.setOpenExternalLinks(True)
                w.setMarkdown(text)

            gui.get_widget(
                the_type=TextBrowser, caption='路线图',
                on_top=True, icon='info', oper=oper)


def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = About()
    w.resize(600, 480)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
