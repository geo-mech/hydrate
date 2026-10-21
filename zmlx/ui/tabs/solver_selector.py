"""默认求解器配置面板.

左侧: 求解器列表（名称 + 简要说明）
右侧: 当前选中求解器的详细说明 + 参数输入 + 操作按钮

外部依赖:
    - zmlx.exts: set_default_solver, get_default_solver
    - zmlx.exts._sol: 各求解器类 (ConjugateGradientSolver 等)
    - zmlx.exts.scipy_sol: SciPySolver (可选)
    - zmlx.exts.pardiso: PARDISOSolver (可选)
"""

from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets


# ── 求解器元数据 ──────────────────────────────────────────────────────

SOLVER_META = [
    {
        'id': 'cg', 'name': 'CG (共轭梯度)',
        'desc': '共轭梯度迭代法。仅适用于对称正定 (SPD) 矩阵。\n'
                '每次迭代代价低（一次矩阵-向量乘），\n'
                '收敛速度取决于条件数。\n\n'
                '典型应用: 压力泊松方程、热传导、扩散方程。',
        'params': ['tolerance'],
        'factory': lambda: None,  # deferred
    },
    {
        'id': 'iccg', 'name': 'ICCG (预条件 CG)',
        'desc': '不完全 Cholesky 预条件共轭梯度。\n'
                '比普通 CG 收敛快 5-50 倍，用于病态 SPD 矩阵。\n\n'
                '原理: A ≈ LL^T → 用 L^{-1} A L^{-T} 改善条件数。\n'
                'shift 控制正则化强度，分解失败时尝试增大。\n\n'
                '典型应用: FEM 刚度矩阵、强非均质渗流。',
        'params': ['tolerance', 'shift'],
        'factory': lambda: None,
    },
    {
        'id': 'lu', 'name': 'SparseLU',
        'desc': 'Eigen 稀疏 LU 直接分解求解器。\n'
                '结果精确到机器精度，不依赖迭代收敛。\n'
                '适用于任意方阵，不要求对称或正定。\n\n'
                '限制: 小到中等规模 (n < 1e4)，大规模 fill-in 严重。',
        'params': [],
        'factory': lambda: None,
    },
    {
        'id': 'ldlt', 'name': 'SimplicialLDLT',
        'desc': 'Eigen 稀疏 Cholesky (LDL^T) 直接分解。\n'
                '比 SparseLU 快 2-5 倍，但仅适用于 SPD 矩阵。\n\n'
                '典型应用: FEM 刚度矩阵 (Ku=f)、渗流压力泊松方程。\n'
                '限制: n < 1e4，大规模 fill-in 严重。',
        'params': [],
        'factory': lambda: None,
    },
    {
        'id': 'bicgstab', 'name': 'BiCGSTAB',
        'desc': '双共轭梯度稳定化迭代法。\n'
                '适用于一般非对称方阵，CG 不收敛时的备选。\n\n'
                '与 CG 对比: CG 仅 SPD 且更快；BiCGSTAB 通用但每次迭代代价更高。',
        'params': ['tolerance'],
        'factory': lambda: None,
    },
    {
        'id': 'ilub', 'name': 'ILU-BiCGSTAB',
        'desc': '不完全 LU 预条件 BiCGSTAB。\n'
                '比普通 BiCGSTAB 收敛快 5-50 倍。\n\n'
                '- droptol: ILU 丢弃容差，控制预条件器稀疏度\n'
                '- fillfactor: ILU 填充因子，控制内存占用\n\n'
                '典型应用: 对流主导的输运问题。',
        'params': ['tolerance', 'droptol', 'fillfactor'],
        'factory': lambda: None,
    },
    {
        'id': 'scipy', 'name': 'SciPy (SuperLU)',
        'desc': '基于 scipy.sparse.linalg.spsolve 的直接求解器。\n'
                '纯 Python 实现，零编译。\n'
                '适用于中小规模一般稀疏矩阵 (n < 5e4)。',
        'params': [],
        'factory': lambda: None,
        'optional': True,
    },
    {
        'id': 'pardiso', 'name': 'PARDISO (Intel MKL)',
        'desc': 'Intel MKL 稀疏直接求解器。\n'
                'LDL^T 分解 (SPD) 或 LU 分解 (一般)。\n'
                '并行 METIS 重排 + 多线程分解，百万级未知量。\n\n'
                '需要: Intel MKL 运行时 (pip install mkl mkl-devel)\n'
                '需要: 编译 pardiso.dll',
        'params': ['mtype'],
        'factory': lambda: None,
        'optional': True,
    },
]

# 参数定义
PARAM_DEFS = {
    'tolerance':  {'label': '收敛容差',    'type': 'float',  'default': 1e-10,
                   'range': (1e-16, 0.1), 'decimals': 12, 'step': 1e-2,
                   'tip': '残差范数阈值，越小精度越高但迭代次数越多'},
    'shift':      {'label': 'IC 正则化参数', 'type': 'float', 'default': 1e-3,
                   'range': (0.0, 10.0),  'decimals': 6, 'step': 1e-3,
                   'tip': '分解失败时尝试增大 (正值增加稳定性)'},
    'droptol':    {'label': 'ILU 丢弃容差',  'type': 'float', 'default': 1e-3,
                   'range': (0.0, 1.0),   'decimals': 6, 'step': 1e-3,
                   'tip': '控制预条件器稀疏度，典型值 1e-2 ~ 1e-4'},
    'fillfactor': {'label': 'ILU 填充因子',  'type': 'int',   'default': 5,
                   'range': (1, 100),      'step': 1,
                   'tip': '控制预条件器内存占用，典型值 3~10'},
    'mtype':      {'label': '矩阵类型',     'type': 'choice', 'default': 2,
                   'choices': [(-2, '-2: 对称满矩阵'), (2, '2: SPD (下三角)'),
                               (11, '11: 一般非对称')],
                   'tip': 'PARDISO 矩阵存储模式'},
}


# ── 求解器工厂函数 ────────────────────────────────────────────────────

def _make_solver(meta, params):
    """根据元数据和参数创建求解器实例."""
    mid = meta['id']
    if mid == 'cg':
        from zmlx.exts._sol import ConjugateGradientSolver
        return ConjugateGradientSolver(tolerance=params.get('tolerance'))
    elif mid == 'iccg':
        from zmlx.exts._sol import ICCGSolver
        return ICCGSolver(tolerance=params.get('tolerance'),
                          shift=params.get('shift'))
    elif mid == 'lu':
        from zmlx.exts._sol import SparseLUSolver
        return SparseLUSolver()
    elif mid == 'ldlt':
        from zmlx.exts._sol import SimplicialLDLTSolver
        return SimplicialLDLTSolver()
    elif mid == 'bicgstab':
        from zmlx.exts._sol import BiCGSTABSolver
        return BiCGSTABSolver(tolerance=params.get('tolerance'))
    elif mid == 'ilub':
        from zmlx.exts._sol import ILUBiCGSTABSolver
        return ILUBiCGSTABSolver(tolerance=params.get('tolerance'),
                                 droptol=params.get('droptol'),
                                 fillfactor=params.get('fillfactor'))
    elif mid == 'scipy':
        from zmlx.exts.scipy_sol import SciPySolver
        return SciPySolver()
    elif mid == 'pardiso':
        from zmlx.exts.pardiso import PARDISOSolver
        return PARDISOSolver(mtype=params.get('mtype', -2))
    raise ValueError(f'Unknown solver: {mid}')


# ── 控件 ──────────────────────────────────────────────────────────────

class SolverSelector(QtWidgets.QWidget):
    """求解器配置面板。

    左侧: 求解器列表
    右侧: 详情 + 参数 + 按钮
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._meta_list = []       # 可用求解器元数据
        self._param_widgets = {}   # 当前参数输入控件
        self._current_meta = None

        self._build_ui()
        self._populate_list()

    def _build_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── 分割器 ──
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # 左侧: 列表
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._list = QtWidgets.QListWidget()
        self._list.currentRowChanged.connect(self._on_select)
        left_layout.addWidget(self._list)

        splitter.addWidget(left)

        # 右侧: 详情 + 参数 + 按钮
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(8, 4, 8, 4)

        # 描述
        self._desc_label = QtWidgets.QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setMargin(8)
        self._desc_label.setFrameShape(QtWidgets.QFrame.Shape.Box)
        right_layout.addWidget(self._desc_label)

        # 参数区域
        param_group = QtWidgets.QGroupBox('求解器参数')
        self._param_layout = QtWidgets.QFormLayout(param_group)
        self._param_layout.setContentsMargins(8, 12, 8, 8)
        self._param_layout.setSpacing(6)
        right_layout.addWidget(param_group)

        # 当前默认求解器信息
        self._status_label = QtWidgets.QLabel()
        right_layout.addWidget(self._status_label)

        # 按钮行
        btn_row = QtWidgets.QHBoxLayout()

        self._btn_apply = QtWidgets.QPushButton('设为默认求解器')
        self._btn_apply.setMinimumHeight(32)
        self._btn_apply.clicked.connect(self._apply)
        btn_row.addWidget(self._btn_apply)

        self._btn_test = QtWidgets.QPushButton('快速测试')
        self._btn_test.setMinimumHeight(32)
        self._btn_test.clicked.connect(self._test)
        btn_row.addWidget(self._btn_test)

        self._btn_reset = QtWidgets.QPushButton('恢复默认')
        self._btn_reset.setMinimumHeight(32)
        self._btn_reset.clicked.connect(self._reset_defaults)
        btn_row.addWidget(self._btn_reset)

        btn_row.addWidget(QtWidgets.QLabel('  测试矩阵:'))

        self._test_size = QtWidgets.QComboBox()
        self._test_size.addItem('2×2', 2)
        self._test_size.addItem('5×5', 5)
        self._test_size.addItem('10×10', 10)
        self._test_size.addItem('20×20', 20)
        self._test_size.addItem('50×50', 50)
        self._test_size.addItem('100×100', 100)
        btn_row.addWidget(self._test_size)

        right_layout.addLayout(btn_row)

        # ── 矩阵显示区 ──
        self._matrix_view = QtWidgets.QPlainTextEdit()
        self._matrix_view.setReadOnly(True)
        self._matrix_view.setMaximumHeight(300)
        font = self._matrix_view.font()
        font.setFamily('Consolas')
        self._matrix_view.setFont(font)
        self._matrix_view.setPlaceholderText('矩阵 ≤10×10 时显示内容')
        right_layout.addWidget(self._matrix_view)

        note = QtWidgets.QLabel(
            '注意：此设置仅修改内存中的默认求解器，不写入磁盘。\n'
            '软件重启后将恢复为原始的 CG 默认设置。')
        note.setWordWrap(True)
        right_layout.addWidget(note)

        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # 刷新状态
        self._update_status()

    def _populate_list(self):
        """构建可用求解器列表."""
        self._list.clear()
        self._meta_list = []

        for meta in SOLVER_META:
            if meta.get('optional'):
                # 检查依赖
                mid = meta['id']
                if mid == 'scipy':
                    try:
                        import scipy.sparse.linalg  # noqa: F401
                    except ImportError:
                        continue
                elif mid == 'pardiso':
                    try:
                        from zmlx.exts.pardiso import PARDISOSolver  # noqa: F401
                    except ImportError:
                        continue
            self._meta_list.append(meta)

            item = QtWidgets.QListWidgetItem(meta['name'])
            item.setToolTip(meta['desc'].split('\n')[0])
            self._list.addItem(item)

    def _on_select(self, row):
        if row < 0 or row >= len(self._meta_list):
            return
        meta = self._meta_list[row]
        self._current_meta = meta
        self._desc_label.setText(meta['desc'])
        self._build_params(meta)

    def _build_params(self, meta):
        """根据选中求解器动态生成参数输入控件."""
        # 清除旧控件
        while self._param_layout.rowCount() > 0:
            self._param_layout.removeRow(0)
        self._param_widgets.clear()

        for pname in meta.get('params', []):
            pdef = PARAM_DEFS.get(pname)
            if not pdef:
                continue
            label_text = pdef['label']

            if pdef['type'] == 'float':
                w = QtWidgets.QLineEdit()
                w.setText(str(pdef['default']))
                lo, hi = pdef.get('range', (0, 1))
                w.setValidator(QtGui.QDoubleValidator(lo, hi, 16, w))
                w.setToolTip(pdef.get('tip', ''))

            elif pdef['type'] == 'int':
                w = QtWidgets.QSpinBox()
                lo, hi = pdef.get('range', (1, 100))
                w.setRange(lo, hi)
                w.setSingleStep(pdef.get('step', 1))
                w.setValue(pdef['default'])
                w.setToolTip(pdef.get('tip', ''))

            elif pdef['type'] == 'choice':
                w = QtWidgets.QComboBox()
                for val, text in pdef.get('choices', []):
                    w.addItem(text, val)
                default = pdef['default']
                for i in range(w.count()):
                    if w.itemData(i) == default:
                        w.setCurrentIndex(i)
                        break
                w.setToolTip(pdef.get('tip', ''))

            else:
                w = QtWidgets.QLineEdit()
                w.setText(str(pdef['default']))

            self._param_layout.addRow(f'{label_text}:', w)
            self._param_widgets[pname] = w

    def _get_params(self):
        """读取当前参数值."""
        params = {}
        for pname, w in self._param_widgets.items():
            pdef = PARAM_DEFS.get(pname, {})
            if pdef.get('type') == 'float':
                try:
                    params[pname] = float(w.text())
                except ValueError:
                    params[pname] = pdef['default']
            elif pdef.get('type') == 'int':
                params[pname] = w.value()
            elif pdef.get('type') == 'choice':
                params[pname] = w.currentData()
            else:
                params[pname] = w.text()
        return params

    def _get_code(self):
        """根据当前选中的求解器和参数生成代码字符串 (exec 格式, 自包含 import)."""
        meta = self._current_meta if self._current_meta else {'id': 'cg'}
        mid = meta['id']
        params = self._get_params()
        def expr(cls, *args):
            return f'from zmlx.exts._sol import {cls}\nsolver = {cls}({", ".join(args)})'
        if mid == 'cg':
            return expr('ConjugateGradientSolver', f"tolerance={params.get('tolerance', 1e-10)}")
        elif mid == 'iccg':
            return expr('ICCGSolver', f"tolerance={params.get('tolerance', 1e-10)}", f"shift={params.get('shift', 1e-3)}")
        elif mid == 'lu':
            return expr('SparseLUSolver')
        elif mid == 'ldlt':
            return expr('SimplicialLDLTSolver')
        elif mid == 'bicgstab':
            return expr('BiCGSTABSolver', f"tolerance={params.get('tolerance', 1e-8)}")
        elif mid == 'ilub':
            return expr('ILUBiCGSTABSolver', f"tolerance={params.get('tolerance', 1e-8)}", f"droptol={params.get('droptol', 1e-3)}", f"fillfactor={params.get('fillfactor', 5)}")
        elif mid == 'scipy':
            return 'from zmlx.exts.scipy_sol import SciPySolver\nsolver = SciPySolver()'
        elif mid == 'pardiso':
            return f'from zmlx.exts.pardiso import PARDISOSolver\nsolver = PARDISOSolver(mtype={params.get("mtype", -2)})'
        return expr('ConjugateGradientSolver', 'tolerance=1e-20')

    def _make_current_solver(self):
        if self._current_meta is None:
            return None
        return _make_solver(self._current_meta, self._get_params())

    def _apply(self):
        from zmlx.exts import set_default_solver_code
        code = self._get_code()
        set_default_solver_code(code)
        self._update_status()
        name = self._current_meta['name'] if self._current_meta else '?'
        print(f'\n默认求解器 → {name}\n{code}\n')

    def _test(self):
        """验证: 用当前求解器求解选中的 Poisson 矩阵."""
        solver = self._make_current_solver()
        if solver is None:
            return

        from ctypes import c_double, c_int
        import time

        n = self._test_size.currentData()  # matrix size
        # 1D Poisson (tridiagonal SPD): diag=4, off-diag=-1
        triplets = [(i, i, 4.0) for i in range(n)]
        for i in range(n - 1):
            triplets.append((i, i + 1, -1.0))
            triplets.append((i + 1, i, -1.0))
        nnz = len(triplets)
        rows = (c_int * nnz)()
        cols = (c_int * nnz)()
        vals = (c_double * nnz)()
        for idx, (r, c, v) in enumerate(triplets):
            rows[idx] = r; cols[idx] = c; vals[idx] = v
        x = (c_double * n)()
        b = (c_double * n)()
        for i in range(n):
            b[i] = float(i + 1)

        t0 = time.perf_counter()
        err = solver.solve(rows, cols, vals, x, b)
        dt = time.perf_counter() - t0

        from datetime import datetime
        t = datetime.now().strftime('%H:%M:%S')
        if err == 0:
            print(f'\n[{t}] {self._current_meta["name"]} n={n} 测试通过: '
                  f'x[0]={x[0]:.6f} 耗时={dt*1000:.2f}ms\n')
        else:
            print(f'\n[{t}] {self._current_meta["name"]} 测试失败: 错误码={err}\n')

        # 显示矩阵（小矩阵）
        if n <= 100:
            lines = [f'A ({n}×{n}), b ({n}×1) → x ({n}×1):', '']
            # 显示 A 的非零元
            rp = [0] * (n + 1)
            for r in rows:
                rp[r] += 1
            for i in range(1, n + 1):
                rp[i] += rp[i - 1]
            dense = [[0.0] * n for _ in range(n)]
            for idx in range(nnz):
                dense[rows[idx]][cols[idx]] = vals[idx]
            # 只显示前 10 行
            limit = min(n, 10)
            for i in range(limit):
                row_str = ' '.join(f'{dense[i][j]:6.1f}' for j in range(limit))
                lines.append(f'  [{row_str}  ...]' if n > 10 else f'  [{row_str}]')
            if n > 10:
                lines.append(f'  ... ({n-10} more rows)')
            lines.append('')
            lines.append(f'b = [{", ".join(f"{b[i]:.2f}" for i in range(min(n, 10)))}'
                         f'{", ..." if n > 10 else ""}]')
            lines.append(f'x = [{", ".join(f"{x[i]:.6f}" for i in range(min(n, 10)))}'
                         f'{", ..." if n > 10 else ""}]')
            self._matrix_view.setPlainText('\n'.join(lines))

    def _reset_defaults(self):
        """恢复为默认 CG 求解器."""
        from zmlx.exts import set_default_solver_code
        set_default_solver_code(
            'from zmlx.exts._sol import ConjugateGradientSolver\n'
            'solver = ConjugateGradientSolver(tolerance=1e-20)')
        self._update_status()
        print(f'\n默认求解器 → 恢复为 CG (tolerance=1e-20)\n')

    def _update_status(self):
        from zmlx.exts import get_default_solver_code
        code = get_default_solver_code()
        self._status_label.setText(f'当前默认: {code}')

        # 高亮当前默认求解器
        for i, meta in enumerate(self._meta_list):
            if meta['id'] in code or meta['name'].split(' ')[0] in code:
                self._list.setCurrentRow(i)
                break

    def refresh(self):
        """刷新求解器列表."""
        self._populate_list()
        self._update_status()

    @staticmethod
    def test():
        import sys
        app = QtWidgets.QApplication(sys.argv)
        w = SolverSelector()
        w.resize(900, 600)
        w.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    SolverSelector.test()
