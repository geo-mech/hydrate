"""Seepage 模型编辑器（概览、相渗、流体定义的显示与编辑）.

结构自下而上：

- ``SeepageFormEdit`` / ``SeepageTabEdit``：**容器** —— 持有一组子编辑器，
  ``set_data(model)`` 逐个下发、``get_data()`` 返回模型本身，子控件的
  ``sig_changed`` 汇集成容器自己的 ``sig_changed``；
- ``SeepageSummary`` / ``SeepageKrEdit`` / ``SeepageInterp1Edit``：**组合编辑器**，
  用同目录 :mod:`zmlx.ui.widgets.editors.field_edit` 的行编辑器与
  :mod:`zmlx.ui.widgets.editors.interp_edit` 的插值编辑器拼成一屏；
- ``SeepageEdit`` / ``FludefEdit``：**顶层编辑器**，各自的文件类型（``gui.open_seepage`` /
  ``gui.open_fludef``）由插件 ``zmlx/ui/plugins/builtin/editors.py`` 注册。

⚠️ 与 ``ui/widgets/editors/`` 里其它模块一致：``set_data()`` 把数据交给控件，
``get_data()`` 取回（这里的“数据”是**模型对象本身**，控件只是它的视图 —— 改动直接
写在模型上）。

⚠️ **依赖方向**：本模块 import ``zmlx.tfc``（第 4 层），而它自己住在第 3 层的
``zmlx/ui`` —— 这是**已知的越界**（见 ``AGENTS.md`` §4.6）：用到的 ``list_fludefs`` /
``get_dt`` / ``set_dt`` 等 getter/setter 本属模型侧，将来若收敛到 ``exts`` / ``fluids``，
这里就能去掉。

⚠️ **文件类型注册不在这里**：类上没有 ``setup_ui``（2026-10-22 起），注册由插件
``zmlx/ui/plugins/builtin/editors.py`` 调 ``gui.reg_file_type`` 完成 —— 控件子包
导入必须保持轻量，不做挂界面的副作用。

Created by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-22: 注册移到插件里的装配代码，删掉未使用的 import
Modified by DeepSeek, 2026-10-22: 整模块搬进 ``zmlx/scen/editors/``
Modified by DeepSeek, 2026-10-22: ``scen/editors`` 删除，随 ``field_edit`` 搬回
    ``ui/widgets/editors/``；注册改由插件 ``plugins/builtin/editors.py`` 负责
Modified by DeepSeek, 2026-10-22: 按 ``widgets/AGENTS.md`` 补 ``test_1`` / 自测入口
"""

import os
import sys

if __name__ == '__main__' and __package__ in (None, ''):
    sys.path.insert(0, os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.pardir, os.pardir, os.pardir, os.pardir)))

from zmlx.exts import FluDef, Interp1, Seepage
from zmlx.tfc import seepage
from zmlx.ui.alg import h_spacer
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widgets.editors.field_edit import (
    FloatFieldEdit, IntFieldEdit, TextFieldEdit)
from zmlx.ui.widgets.editors.interp_edit import Interp1Edit, Interp2Edit


class FludefEdit(QtWidgets.QWidget):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = FluDef()

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        layout1 = QtWidgets.QHBoxLayout(self)
        layout.addLayout(layout1)

        self.den_view = Interp2Edit(
            self, title='密度 (kg/m^3)', xlabel='压力 (Pa)', ylabel='温度 (K)',
            zlabel='密度',
            view_init={'elev': 30, 'azim': -120},
        )
        layout1.addWidget(self.den_view)

        self.vis_view = Interp2Edit(
            self, title='粘性 (Pa.s)', xlabel='压力 (Pa)', ylabel='温度 (K)',
            zlabel='粘性',
            view_init={'elev': 30, 'azim': -120},
        )
        layout1.addWidget(self.vis_view)

        layout2 = QtWidgets.QHBoxLayout(self)
        layout.addLayout(layout2)

        layout2.addItem(h_spacer())
        layout2.addWidget(QtWidgets.QLabel('流体名字: '))
        self.name_edit = QtWidgets.QLineEdit(self)
        layout2.addWidget(self.name_edit)
        layout2.addWidget(QtWidgets.QLabel('比热: '))
        self.c_edit = QtWidgets.QLineEdit(self)
        layout2.addWidget(self.c_edit)

        self.den_view.sig_changed.connect(self._den_changed)
        self.vis_view.sig_changed.connect(self._vis_changed)
        self.name_edit.editingFinished.connect(self._name_changed)
        self.c_edit.editingFinished.connect(self._specific_heat_changed)

    def set_data(self, data):
        if isinstance(data, FluDef):
            self.data = data
            self.name_edit.setText(self.data.name)
            self.den_view.set_data(self.data.den)
            self.vis_view.set_data(self.data.vis)
            self.c_edit.setText(f'{self.data.specific_heat:.2f}')

    def get_data(self):
        return self.data

    def _den_changed(self):
        self.data.den.clone(self.den_view.get_data())
        self.sig_changed.emit()
        print('更新了密度数据')

    def _vis_changed(self):
        self.data.vis.clone(self.vis_view.get_data())
        self.sig_changed.emit()
        print('更新了粘度数据')

    def _name_changed(self):
        self.data.name = self.name_edit.text()
        self.sig_changed.emit()
        print('更改了名字')

    def _specific_heat_changed(self):
        # ⚠️ 必须兜住 ValueError：c_edit 是普通 QLineEdit（没有 validator），
        #    而 editingFinished 在**回车/失焦**时对任意文本都会触发 —— 用户
        #    随手敲进 "abc" 就会让 float() 抛异常。异常从槽里逃出去时 PyQt 会
        #    调 qFatal() **直接终止进程**（实测退出码 0xC0000409），既没有
        #    Python 异常可捕获，也没有任何提示。
        try:
            value = float(self.c_edit.text())
        except ValueError:
            print(f'比热无效（应为数字）: {self.c_edit.text()!r}')
            return
        self.data.specific_heat = value
        self.sig_changed.emit()
        print('更改了比热')


class SeepageFormEdit(QtWidgets.QScrollArea):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, items=None):
        super().__init__(parent)
        self.editors = []
        self.data = None
        self.setWidgetResizable(True)
        self.set_items(items)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        for edit in self.editors:
            edit.set_data(self.data)

    def set_items(self, items):
        # 清除现有的编辑器和布局
        self._clear_ui()

        if items is None or len(items) == 0:
            return

        # 创建新的内容和布局
        content = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(content)
        self.setWidget(content)

        # 添加新的元素
        for desc, widget in items:
            form_layout.addRow(desc, widget)
            self.editors.append(widget)
            if hasattr(widget, 'sig_changed'):
                widget.sig_changed.connect(self.sig_changed.emit)

        # 如果已经有数据，设置到新控件中
        if self.data is not None:
            self.set_data(self.data)

    def _clear_ui(self):
        """清除现有的UI元素"""
        # 清除编辑器列表
        self.editors.clear()

        # 清除现有的widget和布局
        old_widget = self.takeWidget()
        if old_widget is not None:
            old_widget.deleteLater()


class SeepageTabEdit(QtWidgets.QTabWidget):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, items=None):
        super().__init__(parent)
        self.editors = []
        self.data = None
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.set_items(items)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        for edit in self.editors:
            edit.set_data(self.data)

    def set_items(self, items):
        # 清除现有的标签页
        self._clear_ui()

        if items is None or len(items) == 0:
            return

        # 添加新的标签页
        for desc, widget in items:
            self.addTab(widget, desc)
            self.editors.append(widget)
            if hasattr(widget, 'sig_changed'):
                widget.sig_changed.connect(self.sig_changed.emit)

        # 如果已经有数据，设置到新控件中
        if self.data is not None:
            self.set_data(self.data)

    def _clear_ui(self):
        """清除现有的UI元素"""
        # 清除所有标签页
        while self.count() > 0:
            widget = self.widget(0)
            if widget is not None:
                widget.deleteLater()
            self.removeTab(0)

        # 清除编辑器列表
        self.editors.clear()


class SeepageSummary(SeepageFormEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        items = [
            ('模型描述', TextFieldEdit(
                self,
                get_value=lambda model: model.get_text('note'),
                set_value=lambda model, text: model.set_text('note', text)
            )),
            ('Cell数量', IntFieldEdit(
                self,
                get_value=lambda model: model.cell_number
            )),
            ('Face数量', IntFieldEdit(
                self,
                get_value=lambda model: model.face_number
            )),
            ('流体数量', IntFieldEdit(
                self,
                get_value=lambda model: model.fludef_number
            )),
            ('流体结构', TextFieldEdit(
                self,
                get_value=lambda model: str(seepage.list_fludefs(self.data)),
            )),
            ('反应数量', IntFieldEdit(
                self,
                get_value=lambda model: model.reaction_number
            )),
            ('相渗数量', IntFieldEdit(
                self,
                get_value=lambda model: model.kr_number
            )),
            ('当前步长 [秒]', FloatFieldEdit(
                self,
                get_value=lambda model: seepage.get_dt(model),
                set_value=lambda model, value: seepage.set_dt(model, value)
            )),
            ('当前时间 [秒]', FloatFieldEdit(
                self,
                get_value=lambda model: seepage.get_time(model),
                set_value=lambda model, value: seepage.set_time(model, value)
            )),
            ('时间步', IntFieldEdit(
                self,
                get_value=lambda model: seepage.get_step(model),
                set_value=lambda model, value: seepage.set_step(model, value)
            )),
            ('CFL数', FloatFieldEdit(
                self,
                get_value=lambda model: seepage.get_cfl(model),
                set_value=lambda model, value: seepage.set_cfl(model, value)
            )),
        ]
        self.set_items(items)


class SeepageInterp1Edit(QtWidgets.QWidget):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, get_value=None, set_value=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = Interp1Edit(self)
        layout.addWidget(self.edit)
        self.get_value = get_value
        self.data = None
        self.setMinimumSize(200, 300)

        def do_set():
            # 判据是「模型已设入」而不是 ``isinstance(..., Seepage)``：与模型类型无关，
            # 只要回调可调即可（理由见 ``field_edit.py`` 的模块文档）。
            if callable(set_value) and self.data is not None:
                c = self.edit.get_data()
                if isinstance(c, Interp1):
                    set_value(self.data, c.get_copy())
                    self.sig_changed.emit()

        if callable(set_value):
            self.edit.sig_changed.connect(do_set)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        if callable(self.get_value) and self.data is not None:
            c = self.get_value(self.data)
            if isinstance(c, Interp1):
                self.edit.set_data(c.get_copy())


class SeepageKrEdit(QtWidgets.QWidget):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.form = SeepageFormEdit(self)
        self.form.sig_changed.connect(self.sig_changed.emit)
        layout.addWidget(self.form)

        layout2 = QtWidgets.QHBoxLayout()
        layout2.addItem(h_spacer())
        button = QtWidgets.QPushButton('添加')
        button.clicked.connect(self._add)
        layout2.addWidget(button)

        button = QtWidgets.QPushButton('移除')
        button.clicked.connect(self._remove)
        layout2.addWidget(button)

        layout.addLayout(layout2)

    def _add(self):
        data = self.get_data()
        if isinstance(data, Seepage):
            data.kr_number += 1
            self.set_data(data)
            self.sig_changed.emit()

    def _remove(self):
        data = self.get_data()
        if isinstance(data, Seepage):
            if data.kr_number > 0:
                data.kr_number -= 1
                self.set_data(data)
                self.sig_changed.emit()

    def get_data(self):
        return self.form.get_data()

    def set_data(self, data: Seepage):
        items = [
            ('默认相渗', SeepageInterp1Edit(
                self, get_value=lambda model: model.get_kr(),
                set_value=lambda model, value: model.set_default_kr(value)))
        ]
        count = min(10, data.kr_number)
        for idx in range(count):
            items.append(
                (f'相渗{idx}', SeepageInterp1Edit(
                    self, get_value=lambda model, idx=idx: model.get_kr(idx),
                    set_value=lambda model, value, idx=idx: model.set_kr(index=idx, kr=value)))
            )

        self.form.set_items(items)
        self.form.set_data(data)


class SeepageEdit(SeepageTabEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        items = [
            ('概览', SeepageSummary(self)),
            ('相渗', SeepageKrEdit(self)),
        ]
        self.set_items(items)


def test_1():
    """直接运行本文件时的自测：造一个空模型，看看两个顶层编辑器能否正常显示."""
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QTabWidget()

    # ⚠️ 模型对象可能**建不出来**（``zmlx.exts`` 只在装了 zml-dll 的环境里可用），
    #    那时就开一个空编辑器 —— 自测的目的是「控件能不能构造、布局对不对」，不是别的。
    try:
        seepage_data, fludef_data = Seepage(), FluDef()
    except Exception as err:
        print(f'造模型失败（{err}），改为空编辑器自测')
        seepage_data, fludef_data = None, None

    edit = SeepageEdit(window)
    if seepage_data is not None:
        edit.set_data(seepage_data)
    window.addTab(edit, 'SeepageEdit')

    fludef = FludefEdit(window)
    if fludef_data is not None:
        fludef.set_data(fludef_data)
    window.addTab(fludef, 'FludefEdit')

    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
