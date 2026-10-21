"""
Quick Look 压力评估控件.

为 evaluate() 提供 GUI 参数输入界面：填写参数 → 点击运行 → 查看压力分布图。
所有参数修改自动序列化到当前工作目录下的 quick_look.json。
"""

import os

from zmlx.ui.pyqt import QtCore, QtWidgets

# ── 参数元数据 ──────────────────────────────────────────────────────
# type: float / int / tuple / text / code
PARAM_DEFS = {
    # ── 网格参数 ──
    'x_range': {
        'label': 'X 范围 (m)', 'type': 'tuple', 'default': (0, 400),
        'tip': '网格 x 方向范围 (x_min, x_max) [m]', 'group': '网格参数',
    },
    'y_range': {
        'label': 'Y 范围 (m)', 'type': 'tuple', 'default': (0, 400),
        'tip': '网格 y 方向范围 (y_min, y_max) [m]', 'group': '网格参数',
    },
    'dx': {
        'label': 'dx (m)', 'type': 'float', 'default': 10.0,
        'tip': 'x 方向网格尺寸 [m]。dx 或 dy 至少需提供一个，留空 = dy', 'group': '网格参数',
        'placeholder': '留空 = dy',
    },
    'dy': {
        'label': 'dy (m)', 'type': 'float', 'default': None,
        'tip': 'y 方向网格尺寸 [m]，留空 = dx', 'group': '网格参数',
        'placeholder': '留空 = dx',
    },

    # ── 物性参数 ──
    'p': {
        'label': '初始压力 (Pa)', 'type': 'code', 'default': '1e6',
        'tip': '初始孔隙压力场。可定义标量 p=1e6，或函数 def p(x,y,z): ...\n'
               '代码中需定义变量 p（标量或 (x,y,z) -> float 函数）', 'group': '物性参数',
    },
    'perm': {
        'label': '渗透率 (m^2)', 'type': 'float', 'default': 1e-14,
        'tip': '多孔介质渗透率 [m^2]', 'group': '物性参数',
    },
    'pore_modulus': {
        'label': '孔隙刚度 (Pa)', 'type': 'float', 'default': 100e6,
        'tip': '孔隙体积模量 [Pa]', 'group': '物性参数',
    },
    'viscosity': {
        'label': '流体粘度 (Pa·s)', 'type': 'float', 'default': 1e-3,
        'tip': '流体动力粘度 [Pa·s]', 'group': '物性参数',
    },

    # ── 模拟控制 ──
    'time_forward': {
        'label': '模拟时间 (s)', 'type': 'float', 'default': 3600 * 24,
        'tip': '总模拟时间 [s]，默认 86400 (1 天)', 'group': '模拟控制',
    },
    'step_max': {
        'label': '最大步数', 'type': 'int', 'default': 100,
        'tip': '最大迭代步数', 'group': '模拟控制',
    },
    'acc_factor': {
        'label': '加速因子', 'type': 'float', 'default': 1e6,
        'tip': 'porosity 和 pore_modulus 的放大倍数，用于加速收敛', 'group': '模拟控制',
    },

    # ── 高级 ──
    'control_p': {
        'label': '控压点', 'type': 'text', 'default': '',
        'tip': '定压边界点列表，格式: (x,y);(x,y)。例如: (0,0);(100,200)。'
               '每个点处的压力取 p 参数的当前值', 'group': '高级',
        'placeholder': '(x,y);(x,y) 或留空',
    },
    'frac_segs': {
        'label': '裂缝线段', 'type': 'text', 'default': '',
        'tip': '裂缝线段列表，格式: (x1,y1)-(x2,y2)-factor;...。例如: '
               '(0,200)-(400,200)-5。多条用分号分隔。factor 为面积放大倍率', 'group': '高级',
        'placeholder': '(x1,y1)-(x2,y2)-factor 或留空',
    },
}


def parse_tuple(text):
    """解析 "(x, y)" 或 "x, y" → (x, y)."""
    text = text.strip()
    if not text:
        raise ValueError('空输入')
    items = [float(v) for v in text.strip('()').split(',')]
    if len(items) != 2:
        raise ValueError(f'需要 2 个值，得到 {len(items)}')
    return tuple(items)


def parse_control_p(text):
    """解析 "(x,y);(x,y)" → [(x, y), ...]."""
    text = text.strip()
    if not text:
        return None
    points = []
    for part in text.split(';'):
        part = part.strip()
        if not part:
            continue
        x, y = part.strip('()').split(',')
        points.append((float(x), float(y)))
    return points


def parse_frac_segs(text):
    """解析 "(x1,y1)-(x2,y2)-factor;..." → [((x1,y1), (x2,y2), factor), ...]."""
    text = text.strip()
    if not text:
        return None
    segs = []
    for part in text.split(';'):
        part = part.strip()
        if not part:
            continue
        points_part, factor_str = part.rsplit('-', 1)
        p0_str, p1_str = points_part.split('-')
        p0 = tuple(float(v) for v in p0_str.strip('()').split(','))
        p1 = tuple(float(v) for v in p1_str.strip('()').split(','))
        segs.append((p0, p1, float(factor_str)))
    return segs


class QuickLookWidget(QtWidgets.QWidget):
    """evaluate() 的参数输入与结果显示控件."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._param_widgets = {}  # param name → input widget
        self._control_p = None
        self._frac_segs = None
        self._saving = False  # 防止 load→save 回路
        self._last_result = None  # 最近一次计算结果

        # 防抖定时器：用户停止输入 500ms 后才写入文件
        self._save_timer = QtCore.QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save)

        self._build_ui()
        self._connect_save()
        if not self._load():
            self._load_defaults()

    # ── UI 构建 ──────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 左右分栏：左 = 参数输入，右 = 结果
        split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # ── 左侧：参数输入区（分组滚动）──
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        for group in ['网格参数', '物性参数', '模拟控制', '高级']:
            box = QtWidgets.QGroupBox(group)
            form = QtWidgets.QFormLayout(box)
            for name, pdef in PARAM_DEFS.items():
                if pdef.get('group') != group:
                    continue
                widget = self._create_param_widget(pdef)
                self._param_widgets[name] = widget
                label = QtWidgets.QLabel(pdef['label'])
                label.setToolTip(pdef['tip'])
                form.addRow(label, widget)
            content_layout.addWidget(box)
        content_layout.addStretch()
        scroll.setWidget(content)
        split.addWidget(scroll)

        # ── 右侧：结果区（初始隐藏）──
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        try:
            from zmlx.ui.widgets.plt import MatplotWidget
            self._plot = MatplotWidget(right)
        except Exception:
            self._plot = None
        if self._plot is not None:
            right_layout.addWidget(self._plot, stretch=1)
            self._plot.setVisible(False)
        self._summary = QtWidgets.QLabel('')
        self._summary.setVisible(False)
        right_layout.addWidget(self._summary)
        split.addWidget(right)

        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        layout.addWidget(split, stretch=1)

        # 按钮行
        run_btn = QtWidgets.QPushButton('运行 (Evaluate)')
        run_btn.clicked.connect(self._on_run)
        self._run_btn = run_btn
        reset_btn = QtWidgets.QPushButton('重置默认值')
        reset_btn.clicked.connect(self._load_defaults)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(run_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _create_param_widget(self, pdef):
        """按 type 创建输入控件."""
        ptype = pdef['type']
        tip = pdef['tip']
        if ptype == 'code':
            # 优先使用项目专用的代码编辑器控件（语法高亮）；失败时退回 QTextEdit
            try:
                from zmlx.ui.widgets.code_edit import CodeEdit
                w = CodeEdit()
            except Exception:
                w = QtWidgets.QTextEdit()
            w.setToolTip(tip)
            w.setFixedHeight(72)  # 约 3-4 行
            return w
        if ptype == 'float':
            w = QtWidgets.QLineEdit()
            w.setToolTip(tip)
            if 'placeholder' in pdef:
                w.setPlaceholderText(pdef['placeholder'])
            return w
        if ptype == 'int':
            w = QtWidgets.QLineEdit()
            w.setToolTip(tip)
            return w
        if ptype == 'tuple':
            w = QtWidgets.QLineEdit()
            w.setToolTip(tip)
            return w
        if ptype == 'text':
            w = QtWidgets.QLineEdit()
            w.setToolTip(tip)
            if 'placeholder' in pdef:
                w.setPlaceholderText(pdef['placeholder'])
            return w
        raise ValueError(f'unknown param type: {ptype}')

    def _load_defaults(self):
        """用默认值填充所有输入框."""
        self._saving = True
        for name, pdef in PARAM_DEFS.items():
            w = self._param_widgets.get(name)
            if w is None:
                continue
            default = pdef.get('default')
            if pdef['type'] == 'tuple':
                w.setText(f'{default[0]}, {default[1]}')
            else:
                # QLineEdit / CodeEdit / QTextEdit 均支持 setText
                w.setText('' if default is None else str(default))
        self._saving = False

    # ── 自动序列化 ────────────────────────────────────────────────────

    def _connect_save(self):
        """连接所有控件的变更信号 → 防抖保存."""
        for w in self._param_widgets.values():
            if hasattr(w, 'textChanged'):
                w.textChanged.connect(self._on_param_changed)

    def _on_param_changed(self, *_):
        """用户修改参数 → 重置防抖定时器."""
        if not self._saving:
            self._save_timer.start()

    @staticmethod
    def _state_path():
        return os.path.join(os.getcwd(), 'quick_look.json')

    def _save(self):
        """将所有参数文本写入 JSON 文件."""
        data = {}
        for name, w in self._param_widgets.items():
            if isinstance(w, QtWidgets.QLineEdit):
                data[name] = w.text()
            elif hasattr(w, 'get_text'):
                data[name] = w.get_text()
            else:
                data[name] = w.toPlainText()
        try:
            import json
            with open(self._state_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 序列化失败不应影响主流程

    def _load(self):
        """从 JSON 文件恢复参数值。成功返回 True，否则 False."""
        try:
            import json
            fpath = self._state_path()
            if not os.path.isfile(fpath):
                return False
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._saving = True
            for name, text in data.items():
                w = self._param_widgets.get(name)
                if w is not None and isinstance(text, str):
                    w.setText(text)
            self._saving = False
            return True
        except Exception:
            self._saving = False
            return False

    # ── 参数读取 ──────────────────────────────────────────────────────

    def _get_params(self):
        """读取所有输入框的值 → evaluate 参数字典."""
        params = {}
        self._control_p = None
        self._frac_segs = None
        for name, pdef in PARAM_DEFS.items():
            w = self._param_widgets.get(name)
            if w is None:
                continue
            ptype = pdef['type']
            if isinstance(w, QtWidgets.QLineEdit):
                text = w.text().strip()
            elif hasattr(w, 'get_text'):
                text = w.get_text().strip()  # CodeEdit
            else:
                text = w.toPlainText().strip()
            if ptype == 'code':
                if not text:
                    params[name] = None
                else:
                    ns = {}
                    exec(text, ns)
                    if 'p' in ns:
                        params[name] = ns['p']
                    else:
                        # 无 p 变量，则尝试作为表达式求值（如 '1e6'）
                        try:
                            params[name] = eval(text, ns)
                        except Exception:
                            raise ValueError(
                                '代码中需定义变量 p（标量或 (x,y,z) -> float 函数），'
                                '或输入合法表达式（如 1e6）')
            elif ptype == 'float':
                params[name] = None if not text else float(text)
            elif ptype == 'int':
                params[name] = None if not text else int(text)
            elif ptype == 'tuple':
                params[name] = pdef['default'] if not text else parse_tuple(text)
            elif ptype == 'text':
                if name == 'control_p':
                    self._control_p = parse_control_p(text)
                    params[name] = self._control_p
                elif name == 'frac_segs':
                    self._frac_segs = parse_frac_segs(text)
                    params[name] = self._frac_segs
        return params

    # ── 运行与结果显示 ────────────────────────────────────────────────

    def _on_run(self):
        try:
            params = self._get_params()
        except Exception as err:
            QtWidgets.QMessageBox.warning(self, '参数错误', str(err))
            return

        from zmlx.ui import gui

        # ⚠️ **先确认内核空闲，再禁用按钮**：``Console.start_func`` 在内核已经在
        #    跑的时候会直接 ``return``（只响一声错误音），此时 ``post_task``
        #    永远不会被调用 —— 而按钮已经置灰，``_on_finished`` 又正是唯一把它
        #    恢复的地方，于是按钮**永久灰掉**，用户只能重开这个页面。
        if gui.exists() and gui.is_running():
            QtWidgets.QMessageBox.information(
                self, '内核忙', '内核正在运行，请等它结束后再试。')
            return

        self._run_btn.setEnabled(False)
        self._last_result = None
        gui.start_func(
            lambda: self._compute(params),
            post_task=self._on_finished,
        )

    def console_exec(self):
        """
        支持系统菜单-运行
        """
        self._on_run()

    def _compute(self, params):
        """在后台线程中执行 evaluate()."""
        from zmlx.scen.quick_look import evaluate
        self._last_result = evaluate(**params)

    def _on_finished(self):
        """计算完成（post_task 在主线程回调）."""
        self._run_btn.setEnabled(True)
        if self._last_result is not None:
            self._show_result(self._last_result)

    def _show_result(self, result):
        import numpy as np
        if self._plot is None:
            self._summary.setText(f'步数: {result["n_step"]}')
            self._summary.setVisible(True)
            return
        self._plot.figure.clear()
        self._plot.plot_on_figure(lambda fig: self._on_figure(fig, result))
        self._plot.setVisible(True)
        x, y, p = result['x'], result['y'], result['p']
        n_cell = len(p)
        nx = len(np.unique(x))
        ny = len(np.unique(y))
        self._summary.setText(
            f'步数: {result["n_step"]} | 网格: {nx} × {ny} | Cell: {n_cell} | '
            f'压力范围: {p.min() * 1e-6:.4f} – {p.max() * 1e-6:.4f} MPa')
        self._summary.setVisible(True)

    def _on_figure(self, fig, result):
        import numpy as np
        from zmlx.plt.on_axes import add_tricontourf
        ax = fig.subplots()
        x, y, p = result['x'], result['y'], result['p']
        p_mpa = np.asarray(p) * 1e-6
        add_tricontourf(ax, x, y, p_mpa,
                        cbar={'label': '压力 (MPa)'},
                        cmap='jet')
        # 叠加控压点
        if self._control_p is not None:
            cp = np.array(self._control_p)
            ax.scatter(cp[:, 0], cp[:, 1], c='white', marker='o',
                       edgecolors='black', s=60, zorder=5, label='控压点')
            ax.legend()
        # 叠加裂缝线段
        if self._frac_segs is not None:
            for p0, p1, _ in self._frac_segs:
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]], 'r-',
                        linewidth=2, zorder=4)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_aspect('equal')
        ax.set_title('孔隙压力分布 (MPa)')
