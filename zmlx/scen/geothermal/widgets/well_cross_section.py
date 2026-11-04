"""井截面取热的**参数界面**（``WellCrossSectionWidget``）：填参数 → ``create`` → ``solve``.

`_well_cross_section.create` 有 9 个可选参数，直接改 ``cases/case_02.py`` 再跑不直观。
本控件把它们摆成一张表单，填完点「开始求解」就走与算例**完全相同**的路径：

.. code-block:: text

    create(**参数)  →  solve(model, jx, jz, time_max=..., folder=...)

界面上三组输入
--------------

1. **模型参数**：``create`` 的 10 个可选参数（含孔隙度 ``porosity``），
   留空即用 ``create`` 的默认值；
2. **求解时长**：单位是年，换算成秒后传给 ``solve(time_max=...)``；
3. **结果保存目录**：传给 ``solve(folder=...)``。默认取 ``os.getcwd()``，
   可直接改文字，也可点「浏览…」用**系统目录选择框**挑一个；清空表示不保存。

为什么不自己写一套求解
----------------------

控件只负责「收集参数 + 起任务」，**不复制任何物理逻辑** —— 建模、求解、功率统计、
绘图全部复用 :mod:`zmlx.scen.geothermal._well_cross_section`，与 ``cases/case_02.py``
是同一条路。这样控件永远不会与算例漂移。

空值 = 用默认
-------------

模型参数框留空就表示「不传这个参数」，由 ``create`` 自己取默认值 ——
所以界面上看到的是 ``create`` 的文档里那套默认值，而不是控件里另抄一份。
想显式传 ``None``（例如让 ``dt_max`` 保持不改动）就留空。

⚠️ **结果保存目录是个例外**：它有明确的默认值（当前工作目录），
所以「清空（全部用默认）」是把它**重置为** ``os.getcwd()``、而不是置空；
真要「不保存」就把那个框手动清掉。

⚠️ ``well_pos`` 是**二元组**（x, z），要填成 ``0, 0`` 这样；留空则用 ``(0, 0)``。

参数会记住
----------

关闭再打开时**不需要重新输入**：每次改动都把各框的**原始文本**存到
``app_data.temp('geothermal_widget.json')``，下次构造控件时读回来填上。
存的是文本而不是解析后的数值 —— 这样即使某个框暂时填得不合法，也原样保留、
下次打开还在，不会因为「解析失败」被悄悄清掉。

⚠️ 放在 ``app_data.temp`` 而不是当前工作目录：它是个**界面偏好**，
不该在用户的项目目录里留下文件（``quick_look`` 的控件存在 ``os.getcwd()``，
那是它的选择；这里按本包的习惯放缓存目录）。
"""

import math
import os

from zmlx.ui.pyqt import QtCore, QtWidgets

#: 状态文件里「求解时长」与「结果保存目录」用的键。
#: 双下划线前缀用来与 ``create`` 的参数名区分 —— 将来 ``create`` 真加了叫
#: ``time_max`` 的参数也不会撞车。
_KEY_TIME = '__time_max__'
_KEY_FOLDER = '__folder__'

#: 状态文件里另记一项「保存时的工作目录」，用来判断保存目录是不是当时的默认值。
_KEY_CWD = '__cwd__'

#: 表单定义：``(参数名, 标签, 单位, 提示, 解析器)``.
#:
#: ⚠️ 名字必须与 :func:`zmlx.scen.geothermal._well_cross_section.create` 的
#: 关键字参数**逐字一致** —— 这里只是把它们摆出来，不做任何转换或重命名。
#: ``parser=None`` 表示该参数是**二元组**（``xr`` / ``zr`` / ``well_pos``）。
#:
#: ⚠️ **单位与标签分开写**：单位不进标签文字，而是作为输入框内的**只读后缀**
#: 显示（见 :func:`_add_unit`）。这样左边一列整齐、输入框里仍看得到这是什么单位，
#: 而且 ``text()`` 里只有数值，不会把单位混进要解析的字符串。
#: 无量纲或本身就是数量的（网格数、孔隙度），单位留空。
_PARAMS = (
    ('jx', 'x 方向网格数', '', 'int，默认 100', int),
    ('jz', 'z 方向网格数', '', 'int，默认 100', int),
    ('xr', 'x 方向范围', 'm', '二元组 (x_min, x_max)，如 "-50, 50"；留空用 (-50, 50)', None),
    ('zr', 'z 方向范围', 'm', '二元组 (z_min, z_max)，如 "-50, 50"；留空用 (-50, 50)', None),
    ('well_pos', '井的位置', 'm', '二元组 (x, z)，如 "0, 0"；留空用 (0, 0)', None),
    ('well_d', '井筒直径', 'm', 'float，默认 0.2', float),
    ('rock_density', '岩石密度', 'kg/m³', 'float，默认 2650（花岗岩）', float),
    ('rock_heat_capacity', '岩石比热', 'J/(kg·K)', 'float，默认 790（花岗岩）', float),
    ('rock_heat_cond', '岩石热导率', 'W/(m·K)', 'float，默认 3.0（花岗岩）', float),
    ('perm', '渗透率', 'm²', 'float，默认 1e-12（约 1 Darcy）', float),
    ('porosity', '孔隙度', '', '0~1 的小数，默认 0.2', float),
    ('dt_max', '最大时间步', 's', 'float，默认不改动；如 604800 表示 7 天', float),
)

#: ``solve`` 自己的参数（不属于 create）：求解时长。
#: 单位是**年**（显示在输入框内），按 ``3600*24*365`` 换成秒后传给 ``solve(time_max=...)``。
_TIME_LABEL = '求解时长'
_TIME_UNIT = '年'
_TIME_TIP = 'float，默认 10 年；也可填 0.1 这类小数'
_SECONDS_PER_YEAR = 3600 * 24 * 365

#: ``solve`` 自己的参数（不属于 create）：结果保存目录。
#: 传给 ``tfc.solve(folder=...)``，模型快照与单元数据会写到该目录下的
#: ``models/`` / ``cells/`` 等子目录。
_FOLDER_LABEL = '结果保存目录'
_FOLDER_TIP = ('模型快照与单元数据写到这里；默认是当前工作目录（os.getcwd()）。'
               '清空则不保存，只在内存里算。')


def _default_folder():
    """输出目录输入框的**默认值**：当前工作目录.

    Returns:
        str: ``os.getcwd()`` 的结果。每次调用都重新取 —— 用户如果在主界面换了
        工作目录，新建的控件会跟着用新目录。
    """
    return os.getcwd()


def _add_unit(edit, unit):
    """在输入框**内部右侧**显示一个只读的单位后缀.

    用 ``QLineEdit.addAction`` 放一个不可用的 ``QAction``：它显示在输入框内、
    不占正文，``text()`` 里仍然只有数值 —— 比把单位写进标签（``岩石密度 (kg/m³)``）
    更紧凑，标签那一列也因此能对齐。

    Args:
        edit: 要加单位的 ``QLineEdit``。
        unit: 单位文字，如 ``'kg/m³'``。空字符串表示无量纲，什么都不加。
    """
    if len(unit) == 0:
        return
    from zmlx.ui.pyqt import QtGui

    action = QtGui.QAction(unit, edit)
    action.setEnabled(False)  # 只当标签用：置灰才不会像「可点的按钮」
    edit.addAction(action, QtWidgets.QLineEdit.ActionPosition.TrailingPosition)


def _state_path():
    """参数记忆文件的位置：``app_data.temp('geothermal_widget.json')``.

    Returns:
        str: 绝对路径（父目录会自动创建）。

    ⚠️ 用 ``app_data.temp`` 而不是当前工作目录：这是**界面偏好**，
    不该在用户的项目目录里留文件。
    """
    from zmlx.system import app_data

    return app_data.temp('geothermal_widget.json')


def _read_state():
    """读出上次保存的参数文本.

    Returns:
        dict: ``{键: 文本}``。文件不存在、读不出、或内容不是 JSON 对象时返回空字典
        （**不抛异常** —— 记忆功能失败不该影响打开控件）。
    """
    import json

    try:
        path = _state_path()
        if not os.path.isfile(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        # 只保留字符串值：手改过文件时不至于把控件喂坏
        return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}
    except Exception:
        return {}


def _write_state(data):
    """把参数文本写回记忆文件（尽力而为，失败静默）.

    Args:
        data: ``{键: 文本}``。
    """
    import json

    try:
        with open(_state_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # 存偏好失败不该打断用户操作


class WellCrossSectionWidget(QtWidgets.QWidget):
    """「地热 → 井截面取热」的参数界面.

    上半部分是参数表单（``_PARAMS`` + 求解时长），下半部分是按钮；
    点「开始求解」后在**控制台线程**里依次执行 ``create`` 与 ``solve``。
    """

    CAPTION = '井截面取热'

    def __init__(self, parent=None):
        """摆出表单：模型参数、求解时长、结果保存目录，以及按钮行.

        Args:
            parent: Qt 父控件（通常由 ``gui.get_widget`` 传入标签容器）。
        """
        super().__init__(parent)
        self._edits = {}

        # 外层上下两个：上半是「左表单 + 右示意图」，下半是提示行。
        outer = QtWidgets.QVBoxLayout(self)

        split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        outer.addWidget(split, stretch=1)

        # ── 左：参数表单 + 输出 + 按钮 ──────────────────────────────
        left = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(left)

        # ── 参数表单 ────────────────────────────────────────────────
        box = QtWidgets.QGroupBox('模型参数（留空则用 create() 的默认值）')
        form = QtWidgets.QFormLayout(box)
        for name, label, unit, tip, _parser in _PARAMS:
            edit = QtWidgets.QLineEdit()
            edit.setToolTip(tip)
            # ⚠️ 占位符里不再重复写单位 —— 单位已经显示在输入框右侧了
            edit.setPlaceholderText(tip)
            _add_unit(edit, unit)
            form.addRow(label, edit)
            self._edits[name] = edit

        self._time_edit = QtWidgets.QLineEdit()
        self._time_edit.setToolTip(_TIME_TIP)
        self._time_edit.setPlaceholderText(_TIME_TIP)
        _add_unit(self._time_edit, _TIME_UNIT)
        form.addRow(_TIME_LABEL, self._time_edit)

        layout.addWidget(box)

        # ── 输出目录 ────────────────────────────────────────────────
        out_box = QtWidgets.QGroupBox('输出')
        out_form = QtWidgets.QFormLayout(out_box)
        path_row = QtWidgets.QHBoxLayout()
        self._folder_edit = QtWidgets.QLineEdit()
        self._folder_edit.setToolTip(_FOLDER_TIP)
        self._folder_edit.setText(_default_folder())
        browse_btn = QtWidgets.QPushButton('浏览…')
        browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(self._folder_edit, stretch=1)
        path_row.addWidget(browse_btn)
        out_form.addRow(_FOLDER_LABEL, path_row)
        layout.addWidget(out_box)

        # ── 按钮 ────────────────────────────────────────────────────
        row = QtWidgets.QHBoxLayout()
        self._run_btn = QtWidgets.QPushButton('开始求解')
        self._run_btn.clicked.connect(self._on_run)
        clear_btn = QtWidgets.QPushButton('清空（全部用默认）')
        clear_btn.clicked.connect(self._clear)
        row.addWidget(self._run_btn)
        row.addWidget(clear_btn)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()

        split.addWidget(left)

        # ── 右：模型示意图（实时跟着参数动）────────────────────────────
        right_box = QtWidgets.QGroupBox('模型示意（随参数实时更新）')
        right_layout = QtWidgets.QVBoxLayout(right_box)
        from zmlx.scen.geothermal.widgets.well_cross_section_sketch import (
            WellCrossSectionSketch)

        self._sketch = WellCrossSectionSketch()
        right_layout.addWidget(self._sketch)
        split.addWidget(right_box)

        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)

        self._hint = QtWidgets.QLabel('')
        self._hint.setWordWrap(True)
        outer.addWidget(self._hint)

        # ── 参数记忆 ────────────────────────────────────────────────
        # 先把上次的值读回来，**再**接信号 —— 否则恢复过程中每填一个框都会触发
        # 一次保存，白白多写几次盘（内容虽相同，但没必要）。
        self._restore()
        self._connect_autosave()

        # 恢复完再画第一版示意图，避免先画默认值、再画恢复值的两帧闪烁
        self._update_sketch()

    # ── 参数记忆 ────────────────────────────────────────────────────

    def _all_edits(self):
        """返回所有需要记忆的输入框：``{键: QLineEdit}``.

        Returns:
            dict: 键是 ``_PARAMS`` 里的参数名，外加 ``'__time_max__'``（求解时长）
            与 ``'__folder__'``（结果保存目录）。用双下划线前缀是为了与参数名分开，
            将来 ``create`` 真加了叫 ``time_max`` 的参数也不会撞车。
        """
        edits = dict(self._edits)
        edits[_KEY_TIME] = self._time_edit
        edits[_KEY_FOLDER] = self._folder_edit
        return edits

    def _restore(self):
        """把上次保存的文本填回各输入框（没有记录时保持构造时的默认值）.

        「结果保存目录」有一处特别处理：记忆里的值与**当前** ``os.getcwd()`` 相同时，
        仍用当前 ``os.getcwd()`` —— 这样用户换过工作目录后，默认目录会跟着变，
        而不是永远停在上次存下的那条路径上。
        """
        data = _read_state()
        if len(data) == 0:
            return
        for key, edit in self._all_edits().items():
            if key not in data:
                continue
            text = data[key]
            if key == _KEY_FOLDER and os.path.normpath(text) == self._saved_cwd():
                continue  # 上回存的就是「当时的默认值」，交给当前 cwd
            edit.setText(text)

    @staticmethod
    def _saved_cwd():
        """上次保存时的工作目录（记在状态文件里，用来判断保存目录是不是「默认值」）.

        Returns:
            str: 上次的 ``os.getcwd()``；没有记录时返回空串。
        """
        return _read_state().get(_KEY_CWD, '')

    def _connect_autosave(self):
        """给每个输入框接上 ``textChanged``：改动后延迟 400 ms 存一次.

        ⚠️ **防抖**（用单次 ``QTimer``）：用户输入一个路径会逐字符触发
        ``textChanged``，不防抖就是每敲一个键写一次盘。
        """
        self._save_timer = QtCore.QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._save)

        # 示意图的重画也防抖，但**间隔更短**（120 ms）：用户希望「改完就看到图」，
        # 而重画一帧 matplotlib 比写一个 json 贵得多，不能每敲一键就重画。
        self._sketch_timer = QtCore.QTimer(self)
        self._sketch_timer.setSingleShot(True)
        self._sketch_timer.setInterval(120)
        self._sketch_timer.timeout.connect(self._update_sketch)

        for edit in self._all_edits().values():
            edit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, _text):
        """任一输入框内容变化：重启防抖计时器（写盘与重画都在计时器里做）."""
        self._save_timer.start()
        self._sketch_timer.start()

    def _update_sketch(self):
        """把当前参数（已解析）交给示意图重画.

        ⚠️ **用 :meth:`_collect` 的解析结果**，而不是把原始文本丢给示意图 ——
        两边各写一套解析必然漂移（``"0, 0"`` 到底怎么切分？）。这里复用同一套
        ``_parse_pair`` / ``int`` / ``float``。

        ⚠️ 解析失败时**不画错、也不弹窗**：把这一项从字典里去掉，示意图会用默认值
        并在图上标出是哪一项没解析 —— 用户还在输入途中（例如刚敲了 ``-``），
        这时弹「参数错误」是打扰。
        """
        params = {}
        for name, _label, _unit, _tip, parser in _PARAMS:
            if name not in ('jx', 'jz', 'xr', 'zr', 'well_pos', 'well_d'):
                continue  # 示意图只画这几项
            text = self._edits[name].text().strip()
            if len(text) == 0:
                continue  # 留空 → 示意图用默认值（**不算错误**）
            try:
                params[name] = (self._parse_pair(text, name) if parser is None
                                else parser(text))
            except ValueError:
                # ⚠️ 不能填 None 表示「填错了」：示意图那边把 None 当「没给值、
                #    用默认、不算错误」。这里原样给那个文本，它解析不了才会被标出来。
                params[name] = text
        self._sketch.set_params(params)

    def _save(self):
        """把所有输入框的**原始文本**连同当前工作目录写进状态文件.

        ⚠️ 存**文本**而不是解析后的值：某个框暂时填得不合法时也原样保留，
        下次打开还在 —— 不会因为解析失败被悄悄清掉。
        """
        data = {key: edit.text() for key, edit in self._all_edits().items()}
        data[_KEY_CWD] = os.getcwd()
        _write_state(data)

    # ── 参数收集 ────────────────────────────────────────────────────

    def _collect(self):
        """从表单读出参数.

        Returns:
            tuple: ``(params, time_max_seconds, folder)``。

            - ``params``：只含**填了值**的项，空着的键直接不出现 ——
              于是 ``create(**params)`` 会用它的默认值；
            - ``time_max_seconds``：求解时长（秒）；
            - ``folder``：结果保存目录；**清空则为 ``None``**（只在内存里算）。

        Raises:
            ValueError: 某个框里的内容无法解析成要求的类型（消息里带参数名与原值）。
            ValueError: 井的位置不是两个数。
            ValueError: 求解时长不是正数。
        """
        params = {}
        for name, label, _unit, _tip, parser in _PARAMS:
            text = self._edits[name].text().strip()
            if len(text) == 0:
                continue  # 留空 = 不传，用 create 的默认值
            if parser is None:  # 二元组：xr / zr / well_pos
                params[name] = self._parse_pair(text, label)
            else:
                try:
                    params[name] = parser(text)
                except ValueError:
                    raise ValueError(
                        '{0} 无法解析为 {1}：{2!r}'.format(
                            label, parser.__name__, text)) from None

        text = self._time_edit.text().strip()
        if len(text) == 0:
            # 留空 = 与 solve 的默认值一致（10 年）。⚠️ 直接写 10 * _SECONDS_PER_YEAR，
            # 不要再乘 3600*24 —— _SECONDS_PER_YEAR 本身已含一天。
            time_max = 10 * _SECONDS_PER_YEAR
        else:
            try:
                years = float(text)
            except ValueError:
                raise ValueError(
                    '{0} 无法解析为 float：{1!r}'.format(_TIME_LABEL, text)) from None
            if not years > 0:
                raise ValueError('{0} 必须大于 0，当前为 {1}'.format(_TIME_LABEL, years))
            time_max = years * _SECONDS_PER_YEAR

        # 目录：清空 = 不保存（tfc.solve 的 folder=None）；非空则去掉首尾空白，
        # 不做路径校验 —— 目录不存在时 tfc.solve 会自己建，真要填错也会在那边报错。
        folder = self._folder_edit.text().strip()
        if len(folder) == 0:
            folder = None
        return params, time_max, folder

    @staticmethod
    def _parse_pair(text, label):
        """把 ``"0, 0"`` / ``"0 0"`` 这类文本解析成二元组 ``(float, float)``.

        Args:
            text: 输入框内容，两个数之间可用逗号、空格或分号分隔。
            label: 出错时写进消息里的参数名。

        Returns:
            tuple[float, float]: 解析出的两个数。

        Raises:
            ValueError: 不是两个数。
        """
        parts = text.replace(';', ',').replace('，', ',').replace(',', ' ').split()
        if len(parts) != 2:
            raise ValueError('{0} 需要两个数（如 "0, 0"），当前为 {1!r}'.format(label, text))
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            raise ValueError('{0} 需要两个数（如 "0, 0"），当前为 {1!r}'.format(label, text)) from None

    def _browse_folder(self):
        """「浏览…」按钮的槽：弹目录选择框，选中后填进输入框.

        起始目录取输入框里已有的路径（存在时），否则退回 ``os.getcwd()``。
        用户取消时**不改动**输入框。
        """
        current = self._folder_edit.text().strip()
        start = current if (len(current) > 0 and os.path.isdir(current)) else _default_folder()
        path = QtWidgets.QFileDialog.getExistingDirectory(self, '选择结果保存目录', start)
        if len(path) > 0:
            self._folder_edit.setText(os.path.normpath(path))

    def _clear(self):
        """清空参数输入框（= 全部用默认值），并把输出目录**重置**为当前工作目录.

        ⚠️ 输出目录不清空：它有一个明确的默认值（``os.getcwd()``），
        「清空」后仍应落在这个默认目录，而不是变成「不保存」。
        想要不保存，就手动把该框清掉。
        """
        for edit in self._edits.values():
            edit.clear()
        self._time_edit.clear()
        self._folder_edit.setText(_default_folder())
        self._hint.setText(
            '已重置：参数使用默认值，结果保存到当前工作目录。')
        # 重置也是一次有意义的改动，立即写盘（不等防抖）：用户很可能接下来就关掉。
        self._save()

    # ── 运行 ────────────────────────────────────────────────────────

    def _on_run(self):
        """「开始求解」按钮的槽：校验参数 → 派发到控制台线程."""
        try:
            params, time_max, folder = self._collect()
        except ValueError as err:
            QtWidgets.QMessageBox.warning(self, '参数错误', str(err))
            return

        from zmlx.ui import gui

        # ⚠️ 先判忙再禁用按钮：控制台忙时 gui.start 会丢弃请求、post_task 永不触发，
        #    而按钮的恢复只发生在 post_task 里 —— 先把按钮置灰就会永久灰掉。
        if gui.exists() and gui.is_running():
            QtWidgets.QMessageBox.information(
                self, '控制台正忙', '控制台正在执行其它任务，请等它结束后再试。')
            return

        self._run_btn.setEnabled(False)
        if folder is None:
            self._hint.setText('求解中（结果不保存）……可在工具栏用「暂停 / 停止」中断。')
        else:
            self._hint.setText(
                '求解中，结果保存到 {0} ……可在工具栏用「暂停 / 停止」中断。'.format(folder))
        gui.start(
            lambda: self._run(params, time_max, folder),
            text_beg='开始求解：井截面取热（参数来自界面）',
            text_end='求解结束：井截面取热',
            post_task=self._on_finished,
        )

    def _on_finished(self):
        """``gui.start`` 的收尾回调（GUI 线程，任务失败也会执行）：恢复按钮."""
        self._run_btn.setEnabled(True)
        self._hint.setText('求解结束。')

    def _run(self, params, time_max, folder):
        """在**控制台线程**里执行：``create(**params)`` → ``solve(...)``.

        ⚠️ 这里不碰任何控件（``self._hint`` 由 :meth:`_on_finished` 在 GUI 线程改）。
        进度与图都由 ``solve`` 内部的 ``tfc.solve`` / ``plt`` 自己输出。

        Args:
            params: 传给 :func:`zmlx.scen.geothermal._well_cross_section.create` 的关键字参数。
            time_max: 传给 ``solve`` 的最大求解时间（秒）。
            folder: 传给 ``solve`` 的结果保存目录；``None`` 表示不保存。
        """
        from zmlx.scen.geothermal._well_cross_section import create, solve

        model = create(**params)
        jx = params.get('jx', 100)
        jz = params.get('jz', 100)
        # ⚠️ jx / jz 必须与建网时一致：solve 用它们把单元数据重塑成 [jx, jz] 作图。
        solve(model, jx, jz, time_max=time_max, folder=folder)

    def refresh(self):
        """切回来时刷新（本控件没有可刷新的外部状态，保留方法名只为符合控件约定）."""
        return None

    def console_exec(self):
        """支持系统菜单「操作 → 运行」：等价于点「开始求解」."""
        self._on_run()
