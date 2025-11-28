from zmlx import Seepage, gui
from zmlx.config import seepage
from zmlx.ui.alg import h_spacer
from zmlx.ui.widget.editors import *


class FludefEdit(QtWidgets.QWidget):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = Seepage.FluDef()

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
        if isinstance(data, Seepage.FluDef):
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
        self.data.specific_heat = float(self.c_edit.text())
        self.sig_changed.emit()
        print('更改了比热')

    @staticmethod
    def setup_ui():
        gui.reg_file_type(
            '流体定义 FluDef', ['.fludef', '.xml', '.txt'],
            name='fludef',
            init=Seepage.FluDef,
            widget_type=FludefEdit
        )

        fname = 'Example.fludef'

        def test_data():
            from zmlx.fluid import ch4
            f = ch4.create(name='Methane')
            f.save(fname)
            gui.open_fludef(fname)

        gui.add_action(menu=['帮助', '生成测试数据'],
                       text=f'流体定义: {fname}', slot=test_data)


class SeepageTextEdit(QtWidgets.QTextEdit):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, get_value=None, set_value=None):
        super().__init__(parent)
        self.data = None
        self.get_value = get_value

        if callable(set_value):
            def on_changed():
                if isinstance(self.data, Seepage):
                    set_value(self.data, self.toPlainText())
                    self.sig_changed.emit()

            self.textChanged.connect(on_changed)
        else:
            self.setReadOnly(True)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        if isinstance(self.data, Seepage):
            self.setPlainText(self.get_value(self.data))


class SeepageIntEdit(QtWidgets.QSpinBox):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, get_value=None, set_value=None, value_range=None):
        super().__init__(parent)
        self.data = None
        self.get_value = get_value

        if value_range is not None:
            self.setRange(*value_range)
        else:
            self.setRange(-999999999, 999999999)

        if callable(set_value):
            def on_changed():
                if isinstance(self.data, Seepage):
                    set_value(self.data, self.value())
                    self.sig_changed.emit()

            self.valueChanged.connect(on_changed)
        else:
            self.setReadOnly(True)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        if isinstance(self.data, Seepage):
            self.setValue(self.get_value(self.data))


class SeepageFloatEdit(QtWidgets.QDoubleSpinBox):
    sig_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None, *, get_value=None, set_value=None, value_range=None):
        super().__init__(parent)
        self.data = None
        self.get_value = get_value

        if value_range is not None:
            self.setRange(*value_range)
        else:
            self.setRange(-1e20, 1e20)

        if callable(set_value):
            def on_changed():
                if isinstance(self.data, Seepage):
                    set_value(self.data, self.value())
                    self.sig_changed.emit()

            self.valueChanged.connect(on_changed)
        else:
            self.setReadOnly(True)

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        if isinstance(self.data, Seepage):
            self.setValue(self.get_value(self.data))


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
            ('模型描述', SeepageTextEdit(
                self,
                get_value=lambda model: model.get_text('note'),
                set_value=lambda model, text: model.set_text('note', text)
            )),
            ('Cell数量', SeepageIntEdit(
                self,
                get_value=lambda model: model.cell_number
            )),
            ('Face数量', SeepageIntEdit(
                self,
                get_value=lambda model: model.face_number
            )),
            ('流体数量', SeepageIntEdit(
                self,
                get_value=lambda model: model.fludef_number
            )),
            ('流体结构', SeepageTextEdit(
                self,
                get_value=lambda model: str(seepage.list_fludefs(self.data)),
            )),
            ('反应数量', SeepageIntEdit(
                self,
                get_value=lambda model: model.reaction_number
            )),
            ('相渗数量', SeepageIntEdit(
                self,
                get_value=lambda model: model.kr_number
            )),
            ('当前步长 [秒]', SeepageFloatEdit(
                self,
                get_value=lambda model: seepage.get_dt(model),
                set_value=lambda model, value: seepage.set_dt(model, value)
            )),
            ('当前时间 [秒]', SeepageFloatEdit(
                self,
                get_value=lambda model: seepage.get_time(model),
                set_value=lambda model, value: seepage.set_time(model, value)
            )),
            ('时间步', SeepageIntEdit(
                self,
                get_value=lambda model: seepage.get_step(model),
                set_value=lambda model, value: seepage.set_step(model, value)
            )),
            ('CFL数', SeepageFloatEdit(
                self,
                get_value=lambda model: seepage.get_dv_relative(model),
                set_value=lambda model, value: seepage.set_dv_relative(model, value)
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
            if callable(set_value) and isinstance(self.data, Seepage):
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
        if callable(self.get_value) and isinstance(self.data, Seepage):
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
                    self, get_value=lambda model: model.get_kr(idx),
                    set_value=lambda model, value: model.set_kr(index=idx, kr=value)))
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

    @staticmethod
    def setup_ui():
        gui.reg_file_type(
            'Seepage文件', ['.seepage', '.xml', '.txt'],
            name='seepage',
            save=lambda data, name: data.save(name),
            load=lambda name: Seepage(path=name),
            init=lambda: Seepage(),
            widget_type=SeepageEdit
        )


def setup_ui():
    for obj in [FludefEdit, SeepageEdit]:
        try:
            obj.setup_ui()
        except Exception as e:
            print(e)


def main():
    from zmlx.alg.sys import first_execute
    if first_execute(__file__):
        gui.execute(func=setup_ui, keep_cwd=False, close_after_done=False)


if __name__ == '__main__':
    main()
