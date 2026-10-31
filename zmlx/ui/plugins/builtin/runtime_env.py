# ** name = '运行环境'
# ** desc = '「设置 → 运行环境」：检查 zmlx 依赖的第三方包是否已安装，缺失的可一键安装（默认不加载）'
# ** enabled = False
"""运行环境检测（列出 zmlx 的第三方依赖是否已安装，并支持一键安装）.

为什么需要它
------------
``zmlx`` 依赖不少第三方库（numpy / scipy / matplotlib / PyQt6 / vtk ...，
见 ``zmlx/data/dep.py``），而缺依赖时的报错往往出现在很深的地方
（例如 ``ModuleNotFoundError: No module named 'vtk'``），用户很难一眼看出
到底缺什么、该怎么补。本控件把这些依赖集中列出来，标明「已安装 / 未安装」；
未安装的那一行旁边直接给一个「安装」按钮，点一下就在后台线程里装好。

依赖清单来自哪里
----------------
- **必需**：直接读 ``zmlx.data.dep`` 的 ``package_names`` / ``import_names``，
  因此永远与命令行入口 ``zmlx.algs.sys.install_dep`` 保持一致；
  （``pypiwin32`` 被剔除：它是 ``pywin32`` 的废弃别名，装了 pywin32 就有
  ``win32com``，单列一行只会造成「明明装了却显示未安装」的误会。）
- **可选**：**扫描 ``zmlx`` 全部源码里的 import** 得到的第三方库
  （用 AST 脚本扫出，见 :data:`OPTIONAL_DEPENDENCIES`），缺失时只影响某一块
  功能，所以单独成组、并且**不**被「一键安装」按钮牵连。

线程模型（重要）
----------------
检测与安装都**不在 GUI 线程里执行**（安装尤其不能：一次 pip 可能几分钟）：

- :class:`EnvCheckThread`：逐个探测依赖（``importlib.metadata`` 查版本 +
  ``importlib.util.find_spec`` 查可导入性），结果用信号发回主线程再填表；
- :class:`InstallThread`：用 ``subprocess`` 起 pip / conda，逐行读输出并用
  信号发回主线程显示。

⚠️ 子线程里**绝不碰任何控件**；信号是跨线程自动排队投递的，接收槽一定跑在
GUI 线程里。

⚠️ 线程对象**不设 parent**、并且登记在模块级 :data:`_THREADS` 里：``QThread``
在运行中被 GC 会让进程直接崩（"QThread: Destroyed while thread is still
running"，本项目真踩过，参见 ``zmlx/ui/widget/demo_view.py``）。控件若已销毁，
Qt 会自动断开信号连接，迟到的结果被安全丢弃。

安装后端的选择
--------------
与 ``zmlx.algs.sys.install_dep`` 的策略一致：**conda 环境优先 conda
（conda-forge），失败回退 pip**；非 conda 环境直接用 pip。

Created by DeepSeek, 2026-10-06
"""

import subprocess
import sys
import time

from zmlx.system import execute_once
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

#: 标签页的标题（同时也是 ``gui.get_widget`` 的 caption）。
CAPTION = '运行环境'

#: 距上次检测不到这么多秒时，:meth:`RuntimeEnvView.refresh` 直接跳过。
#:
#: ``MainWindow.refresh`` 会在**每次切换标签页**时 duck-typing 地调用当前页面的
#: ``refresh()``，没有这个闸门就会反复去探测十多个包（``find_spec`` 虽快，但
#: 几个 Qt 子模块会触发父包导入）。
RESCAN_INTERVAL = 10.0

#: 正在运行的线程（模块级强引用，防止 QThread 运行中被 GC 掉）。
_THREADS = []


def _keep(thread):
    """登记线程以防被 GC；线程结束后自动摘除（主线程调用）。

    Args:
        thread: 刚创建、尚未 ``start()`` 的 ``QThread``。
    """
    _THREADS.append(thread)

    def _forget(*args):
        try:
            _THREADS.remove(thread)
        except ValueError:
            pass

    thread.finished.connect(_forget)


# =============================================================================
# 依赖清单
# =============================================================================

#: 可选依赖：扫描 ``zmlx`` 源码里全部 ``import`` 得到的第三方库。
#:
#: 这些库缺失时只会让**对应的那一块功能**不可用（例如没有 CoolProp 就换回
#: 内置的流体物性），因此单独成组。``package`` 是 pip 上的发行包名，``name``
#: 是导入名，``note`` 说明它被谁用、缺了会怎样。
OPTIONAL_DEPENDENCIES = [
    dict(package='CoolProp', name='CoolProp',
         note='流体物性引擎（zmlx.fluids.cp），缺了会换回内置物性'),
    dict(package='reaktoro', name='reaktoro',
         note='Reaktoro 流体物性（zmlx.fluids.rkt）'),
    dict(package='reaktplot', name='reaktplot',
         note='Reaktoro 的绘图后端（zmlx.scen.rkt）'),
    dict(package='numba', name='numba',
         note='计算加速（pyproject 的 accelerate extra）'),
    dict(package='cupy', name='cupy',
         note='CUDA 线性求解（zmlx.exts.cuda_sol）'),
    dict(package='opencv-python', name='cv2',
         note='图像处理（zmlx.algs.image）'),
    dict(package='markdown', name='markdown',
         note='Markdown 渲染（zmlx.ui.widgets.md_view）'),
    dict(package='iapws', name='iapws',
         note='水/蒸汽物性（zmlx.scen.geothermal_helium）'),
    dict(package='pyXSteam', name='pyXSteam',
         note='水/蒸汽物性（zmlx.fluids.conf.gas_density.h2o）'),
    dict(package='chemicals', name='chemicals',
         note='液体密度（zmlx.fluids.conf.liqu_density）'),
    dict(package='pygit2', name='pygit2',
         note='程序更新（zmlx.algs._update_by_git）'),
    dict(package='pyqtribbon', name='pyqtribbon',
         note='Ribbon 界面（zmlx.ui.tests.ribbon_demo）'),
]

#: :func:`core_dependencies` 读取 ``zmlx.data.dep`` 失败时的兜底清单。
#:
#: 正常情况下用不到（``zmlx.data.dep`` 是纯常量模块）；只在包被裁过、或
#: 单独把这个文件拷出去跑的时候才会走到这里。
FALLBACK_PACKAGES = [
    'numpy', 'scipy', 'matplotlib', 'pyqtgraph',
    'PyQt6', 'PyQt6-WebEngine', 'pyqt6-qscintilla',
    'PyOpenGL', 'dulwich',
    'pillow', 'pyvista', 'pyvistaqt', 'vtk', 'pandas', 'openpyxl',
]


def core_dependencies():
    """返回**必需**依赖清单（与 ``zmlx.data.dep`` 保持同步）。

    Returns:
        list: ``[dict(package=..., name=..., group='必需'), ...]``。
    """
    try:
        from zmlx.data.dep import import_names, package_names
    except Exception as err:
        print(f'读取 zmlx.data.dep 失败，使用内置兜底清单: {err}')
        package_names = list(FALLBACK_PACKAGES)
        if sys.platform.startswith('win'):
            package_names.append('pywin32')
        import_names = {}

    deps = []
    for package in package_names:
        if package == 'pypiwin32':
            continue  # pywin32 的废弃别名，见模块文档
        deps.append(dict(
            package=package,
            name=import_names.get(package, None),
            group='必需',
            note='zmlx 的核心依赖',
        ))
    return deps


def dependency_list():
    """返回控件要展示的完整依赖清单（必需在前，可选在后）。

    Returns:
        list: :func:`core_dependencies` 的结果，后面接
        :data:`OPTIONAL_DEPENDENCIES`（按包名去重）。
    """
    deps = core_dependencies()
    known = {dep['package'].lower() for dep in deps}
    for item in OPTIONAL_DEPENDENCIES:
        if item['package'].lower() in known:
            continue
        known.add(item['package'].lower())
        deps.append(dict(item, group='可选'))
    return deps


# =============================================================================
# 检测（纯计算，可在任意线程调用）
# =============================================================================

def _dist_version(package):
    """返回发行包 ``package`` 的版本号；查不到（没装）返回 ``None``。

    ⚠️ 走的是 ``importlib.metadata``（**不导入目标模块**），因此可以安全地
    在后台线程里对 vtk / pyvista 这类重库调用。
    """
    try:
        from importlib.metadata import version
    except Exception:
        return None
    try:
        return str(version(package))
    except Exception:
        return None


def _can_import(name):
    """返回导入名 ``name`` 是否可用；``name`` 为空时返回 ``None``（未知）。

    ⚠️ ``find_spec`` 对**子模块**（如 ``PyQt6.Qsci``）会先导入它的父包，
    但不会导入目标模块本身，因此开销可以接受；这一步放在后台线程里做。
    """
    if not isinstance(name, str) or len(name) == 0:
        return None
    try:
        import importlib.util

        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def check_dependency(dep):
    """检测单个依赖是否已安装（纯计算，不碰界面）。

    判定规则：

    - 有导入名时以「能否 import」为准（这才是运行时真正关心的）；
      ``importlib.metadata`` 只用来取版本号；
    - 没有导入名时退化为「``importlib.metadata`` 里有没有这个发行包」。

    Args:
        dep: 依赖描述（见 :func:`dependency_list`）。

    Returns:
        dict: ``dep`` 的副本，另加：

        - ``installed`` (bool)：是否可用；
        - ``version`` (str | None)：发行包版本号；
        - ``detail`` (str)：给用户看的补充说明（放进单元格 tooltip）。
    """
    package = dep['package']
    name = dep.get('name', None)
    version = _dist_version(package)
    imported = _can_import(name)

    if imported is True:
        installed = True
    elif imported is False:
        installed = False
    else:  # 没有导入名，只能看发行包在不在
        installed = version is not None

    if installed and version is not None:
        detail = f'已安装 {package} {version}'
    elif installed:
        detail = f'已安装 {package}（pip 元数据里查不到版本号）'
    elif imported is False and version is not None:
        detail = f'{package} 已安装({version})，但 import {name} 失败'
    else:
        detail = f'未安装 {package}'

    if dep.get('note'):
        detail = f'{detail}\n{dep["note"]}'
    if name:
        detail = f'{detail}\n导入名: {name}'

    result = dict(dep)
    result['installed'] = bool(installed)
    result['version'] = version
    result['detail'] = detail
    return result


def check_all(deps=None):
    """逐个检测依赖（纯计算，可在任意线程调用）。

    Args:
        deps: 依赖清单；``None`` 表示 :func:`dependency_list`。

    Returns:
        list: :func:`check_dependency` 的结果列表。
    """
    if deps is None:
        deps = dependency_list()
    return [check_dependency(dep) for dep in deps]


# =============================================================================
# 后台线程
# =============================================================================

class EnvCheckThread(QtCore.QThread):
    """在后台线程里检测全部依赖（**绝不碰界面**）。

    结果经 :attr:`sig_result` 发回主线程；异常绝不允许逃出 :meth:`run`：
    真逃出去线程会静默死掉、信号永不发出，界面就会永远停在「检测中...」。

    Attributes:
        sig_result: 信号，携带 :func:`check_all` 的返回值。
    """

    sig_result = QtCore.pyqtSignal(list)

    def __init__(self, deps=None, parent=None):
        """初始化。

        Args:
            deps: 要检测的依赖清单；``None`` 表示 :func:`dependency_list`。
            parent: Qt 父对象（**留空**，见模块文档里 ``_THREADS`` 的说明）。
        """
        super().__init__(parent)
        self.setObjectName('EnvCheckThread')
        self.deps = dependency_list() if deps is None else list(deps)

    def run(self):
        """线程体：检测依赖并把结果发回主线程。"""
        try:
            data = check_all(self.deps)
        except Exception as err:  # 防御性：正常路径不会触发
            print(f'Error (when check runtime env): {err}')
            data = []
        self.sig_result.emit(data)


class InstallThread(QtCore.QThread):
    """在后台线程里用 pip / conda 安装若干 Python 包（**绝不碰界面**）。

    每个包的安装过程会**逐行**读出来，经 :attr:`sig_output` 发到主线程显示；
    每个包结束时发一次 :attr:`sig_done`。

    ⚠️ ``install`` 是**真正的慢活**（一次 pip 可能几分钟），这正是它必须待在
    子线程里的原因 —— 否则整个界面会假死。

    ⚠️ 异常绝不允许逃出 :meth:`run`，否则线程静默死掉、界面永远停在
    「安装中...」。

    Attributes:
        sig_output: 信号，携带一行安装日志。
        sig_done: 信号，携带 ``(包名, 是否成功)``。
    """

    sig_output = QtCore.pyqtSignal(str)
    sig_done = QtCore.pyqtSignal(str, bool)

    def __init__(self, dep_list, parent=None):
        """初始化。

        Args:
            dep_list: 要安装的依赖描述列表（每项至少要有 ``package``）。
            parent: Qt 父对象（**留空**，见模块文档里 ``_THREADS`` 的说明）。
        """
        super().__init__(parent)
        self.setObjectName('RuntimeEnvInstallThread')
        self.dep_list = list(dep_list)

    @staticmethod
    def _use_conda():
        """当前是否应该优先用 conda 安装（与 ``install_dep`` 的策略一致）。"""
        try:
            from zmlx.algs.sys import is_conda_env

            return bool(is_conda_env())
        except Exception:
            return False

    @staticmethod
    def _conda_command(package):
        """构造 conda 安装命令。"""
        from zmlx.algs.sys import _find_conda_exe

        return [_find_conda_exe(), 'install', '-y', '-c', 'conda-forge', package]

    @staticmethod
    def _pip_command(package):
        """构造 pip 安装命令。

        用 ``sys.executable -m pip`` 而不是裸 ``pip``：这样装的**一定是当前
        解释器**那个环境，不受 PATH 上其它 pip 的影响。
        """
        return [sys.executable, '-m', 'pip', 'install', package]

    def _run_command(self, cmd, package):
        """执行一条安装命令，把输出逐行发出去。

        Args:
            cmd: 命令行参数列表。
            package: 包名（只用于日志）。

        Returns:
            bool: 子进程返回码为 0 时返回 True。
        """
        self.sig_output.emit(f'[安装] {package}')
        self.sig_output.emit(f'$ {" ".join(cmd)}')
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, encoding='utf-8', errors='replace')
        except Exception as err:
            self.sig_output.emit(f'[安装] 启动安装进程失败: {err}')
            return False
        try:
            with proc.stdout:  # 显式关闭管道，否则会漏一个文件对象
                for line in proc.stdout:
                    self.sig_output.emit(line.rstrip())
            proc.wait()
        except Exception as err:
            self.sig_output.emit(f'[安装] 读取安装输出失败: {err}')
            try:
                proc.kill()
            except Exception:
                pass
            return False
        return proc.returncode == 0

    def _install_one(self, package):
        """安装单个包：conda 环境先试 conda，失败回退 pip。

        Args:
            package: pip / conda 上的发行包名。

        Returns:
            bool: 是否成功。
        """
        if self._use_conda():
            try:
                if self._run_command(self._conda_command(package), package):
                    return True
            except Exception as err:
                self.sig_output.emit(f'[conda:{package}] 失败: {err}')
            self.sig_output.emit(f'[conda:{package}] 失败，回退 pip')
        return self._run_command(self._pip_command(package), package)

    def run(self):
        """线程体：依次安装，每个包结束后发一次完成信号。"""
        try:
            for dep in self.dep_list:
                package = dep.get('package')
                if not package:
                    continue
                try:
                    ok = self._install_one(package)
                except Exception as err:  # 防御性：单个包失败不影响后面的
                    self.sig_output.emit(f'[安装] {package} 出现异常: {err}')
                    ok = False
                self.sig_output.emit(
                    f'[安装] {package} {"成功" if ok else "失败"}')
                self.sig_done.emit(package, bool(ok))
        except Exception as err:  # 防御性：异常绝不能逃出 run()
            self.sig_output.emit(f'[安装] 安装线程异常: {err}')


# =============================================================================
# 控件
# =============================================================================

#: 表格的列标题。
COLUMNS = ['依赖包', '导入名', '分组', '状态', '版本', '操作']

#: 各种状态下的文字颜色。
COLOR_OK = '#1a7f37'        # 已安装（绿）
COLOR_MISSING = '#c0392b'   # 必需依赖缺失（红）
COLOR_OPTIONAL = '#b9770e'  # 可选依赖缺失（橙）


class RuntimeEnvView(QtWidgets.QWidget):
    """运行环境检测控件：列出依赖、标出是否安装、缺失的可一键安装。

    布局从上到下：工具条（重新检测 / 一键安装 / 只看缺失）→ 依赖表格 →
    安装日志。

    ⚠️ **检测与安装都在后台线程里跑**（:class:`EnvCheckThread` /
    :class:`InstallThread`），界面从不被阻塞；子线程只发信号，不碰控件。

    ⚠️ :meth:`refresh` 只做「要不要起线程」的判断（微秒级），满足主窗口对
    ``refresh()`` 必须快的硬性要求（见 ``zmlx/ui/widget/AGENTS.md``）。
    """

    def __init__(self, parent=None):
        """初始化控件（不立刻检测，只排一个延后的自检）。"""
        super().__init__(parent)

        # 数据与状态
        self._deps = dependency_list()  # 依赖清单（检测结果另存）
        self._result = []               # 最近一次检测的结果（没测过就是空）
        self._buttons = {}              # {包名: 安装按钮}
        self._checked_at = 0.0          # 上次检测完成的 time.monotonic()
        self._check_thread = None       # 在飞的检测线程（持有引用，防被 GC）
        self._install_thread = None     # 在飞的安装线程（同上）

        self._setup_widgets()
        self._fill_table(self._deps)    # 先按「清单」铺好表（状态未知）
        self._set_status('尚未检测。')

        # 延后一拍再起线程：构造期间窗口还没画出来，此时起线程会让「打开这个
        # 标签页」这件事变得不可预期（DemoView 同样的取舍）
        QtCore.QTimer.singleShot(0, self.refresh)

    # ------------------------------------------------------------------ 界面

    def _setup_widgets(self):
        """搭建界面（与数据无关，只做一次）。"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ---- 工具条 ----
        bar = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel(self)
        bar.addWidget(self.status_label)
        bar.addStretch(1)

        self.only_missing = QtWidgets.QCheckBox('只显示未安装', self)
        self.only_missing.setToolTip('勾选后隐藏已经安装的依赖，剩下的就是需要补的')
        self.only_missing.toggled.connect(self._apply_filter)
        bar.addWidget(self.only_missing)

        self.button_check = QtWidgets.QPushButton('重新检测', self)
        self.button_check.setToolTip('在后台线程里重新检测一遍（不会卡住界面）')
        self.button_check.clicked.connect(self.start_check)
        bar.addWidget(self.button_check)

        self.button_install_all = QtWidgets.QPushButton('一键安装缺失(必需)', self)
        self.button_install_all.setToolTip(
            '安装所有缺失的必需依赖。可选依赖请按行点击「安装」。')
        self.button_install_all.setEnabled(False)  # 检测出缺失的必需依赖后才可用
        self.button_install_all.clicked.connect(self.install_missing_required)
        bar.addWidget(self.button_install_all)

        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setMinimumWidth(160)
        bar.addWidget(self.progress)
        layout.addLayout(bar)

        # ---- 表格 ----
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(5, 90)
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        # ---- 安装日志 ----
        self.log = QtWidgets.QPlainTextEdit(self)
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setFont(QtGui.QFont('Courier New'))
        self.log.setPlaceholderText('安装日志（pip / conda 的完整输出）')
        self.log.setMinimumHeight(120)
        layout.addWidget(self.log, 0)

    def _fill_table(self, data):
        """按检测结果重建表格。

        Args:
            data: 依赖描述列表（可以带 ``installed`` / ``version`` /
                ``detail``，也可以只有清单本身 —— 那时状态显示「检测中...」）。
        """
        self._buttons = {}
        table = self.table
        table.clearSpans()  # setRowCount(0) 不会清 span，必须显式清
        table.setRowCount(len(data))

        for i_row, dep in enumerate(data):
            package = dep.get('package', '')
            installed = dep.get('installed', None)
            version = dep.get('version', None)
            detail = dep.get('detail', '') or ''

            cell_pkg = QtWidgets.QTableWidgetItem(package)
            cell_pkg.setToolTip(detail or package)
            table.setItem(i_row, 0, cell_pkg)

            table.setItem(i_row, 1, QtWidgets.QTableWidgetItem(
                dep.get('name') or '-'))
            table.setItem(i_row, 2, QtWidgets.QTableWidgetItem(
                dep.get('group', '')))

            if installed is None:
                text, color = '检测中...', None
            elif installed:
                text, color = '已安装', COLOR_OK
            else:
                text = '未安装'
                color = (COLOR_MISSING if dep.get('group') == '必需'
                         else COLOR_OPTIONAL)
            cell_state = QtWidgets.QTableWidgetItem(text)
            cell_state.setToolTip(detail)
            if color is not None:
                cell_state.setForeground(QtGui.QColor(color))
            table.setItem(i_row, 3, cell_state)

            table.setItem(i_row, 4, QtWidgets.QTableWidgetItem(version or '-'))

            if installed is False:  # 未安装 → 给一个安装按钮
                button = QtWidgets.QPushButton('安装', table)
                button.setToolTip(f'在后台线程里安装 {package}')
                button.clicked.connect(
                    lambda checked=False, pkg=package: self.start_install(pkg))
                table.setCellWidget(i_row, 5, button)
                self._buttons[package] = button

        self._apply_filter()

    def _apply_filter(self):
        """按「只显示未安装」复选框隐藏已完成的行（纯界面操作）。"""
        only_missing = self.only_missing.isChecked()
        for i_row in range(self.table.rowCount()):
            hide = False
            if only_missing:
                item = self.table.item(i_row, 3)
                hide = item is not None and item.text() == '已安装'
            self.table.setRowHidden(i_row, hide)

    def _set_status(self, text):
        """更新工具条上的状态文字。"""
        self.status_label.setText(text)

    # ------------------------------------------------------------------ 检测

    def refresh(self, force=False):
        """按需启动一次后台检测（**立即返回，从不阻塞界面**）。

        这是主窗口 duck-typing 调用的通用刷新接口（切标签页、「操作 → 刷新」
        都会进来），所以必须快：这里只做「要不要起线程」的判断。

        Args:
            force: 忽略 :data:`RESCAN_INTERVAL` 闸门，强制重新检测一遍。
        """
        if self._check_thread is not None or self._install_thread is not None:
            return  # 有活正在后台跑，不叠加
        if not force and self._checked_at > 0.0:
            if time.monotonic() - self._checked_at < RESCAN_INTERVAL:
                return
        self.start_check()

    def start_check(self):
        """启动后台检测线程（主线程调用）。

        ⚠️ 检测中**不重建表格**（否则会把用户正在看的滚动位置、以及可能已经
        点下的「安装」按钮冲掉），只在状态栏显示「检测中...」。
        """
        if self._check_thread is not None:
            return
        self._set_status('检测中...')
        self.button_check.setEnabled(False)

        thread = EnvCheckThread(self._deps)
        thread.sig_result.connect(self._on_check_result)
        thread.finished.connect(self._on_check_finished)
        _keep(thread)
        self._check_thread = thread
        thread.start()

    def _on_check_finished(self):
        """检测线程结束（主线程调用）：释放引用。"""
        self._check_thread = None
        self.button_check.setEnabled(True)

    def _on_check_result(self, data):
        """检测结果回来了（主线程调用）：重建表格。

        Args:
            data: :func:`check_all` 的返回值。
        """
        if not isinstance(data, list) or len(data) == 0:
            self._set_status('检测失败，未取得任何结果（详见控制台输出）')
            return
        self._checked_at = time.monotonic()
        self._result = data
        self._fill_table(data)
        self._update_summary(data)

    def _update_summary(self, data):
        """按检测结果更新状态栏文字和「一键安装」按钮的可用性。"""
        missing = [dep for dep in data if not dep.get('installed')]
        missing_required = [
            dep for dep in missing if dep.get('group') == '必需']
        text = f'共 {len(data)} 项，未安装 {len(missing)} 项'
        if len(missing_required) > 0:
            text += f'（其中必需 {len(missing_required)} 项）'
        else:
            text += '（必需依赖已全部就绪）'
        self._set_status(text)
        self.button_install_all.setEnabled(len(missing_required) > 0)

    # ------------------------------------------------------------------ 安装

    def install_missing_required(self):
        """安装当前所有缺失的**必需**依赖（主线程调用）。"""
        if self._install_thread is not None:
            self._set_status('已有安装任务正在运行，请等待它结束。')
            return
        missing = [
            dep for dep in self._result
            if not dep.get('installed') and dep.get('group') == '必需']
        if len(missing) == 0:
            self._set_status('没有检测到缺失的必需依赖。')
            return
        self._start_install_thread(missing)

    def start_install(self, package):
        """安装单个包（主线程调用；「安装」按钮的槽）。

        Args:
            package: 依赖清单里的包名。
        """
        for dep in self._deps:
            if dep.get('package') == package:
                self._start_install_thread([dep])
                return
        print(f'未知的依赖: {package}')

    def _start_install_thread(self, dep_list):
        """启动安装线程（主线程调用）。

        Args:
            dep_list: 要安装的依赖描述列表。
        """
        if self._install_thread is not None:
            self._set_status('已有安装任务正在运行，请等待它结束。')
            return

        self._set_status(f'正在安装 {len(dep_list)} 个包 ...')
        self.log.appendPlainText(
            f'===== 开始安装 {len(dep_list)} 个包 '
            f'({time.strftime("%Y-%m-%d %H:%M:%S")}) =====')

        self.progress.setRange(0, len(dep_list))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.button_check.setEnabled(False)
        self.button_install_all.setEnabled(False)

        # 正在安装的包，按钮变成「安装中...」并且禁用，避免重复点击
        for dep in dep_list:
            button = self._buttons.get(dep['package'], None)
            if button is not None:
                button.setEnabled(False)
                button.setText('安装中')

        thread = InstallThread(dep_list)
        thread.sig_output.connect(self._on_install_output)
        thread.sig_done.connect(self._on_install_done)
        thread.finished.connect(self._on_install_finished)
        _keep(thread)
        self._install_thread = thread
        thread.start()

    def _on_install_output(self, text):
        """安装输出（主线程调用）：追加到日志。

        ⚠️ 输出量可能很大（pip 下载日志），日志控件已经设了
        ``setMaximumBlockCount``，不会无限增长。
        """
        self.log.appendPlainText(text)

    def _on_install_done(self, package, ok):
        """一个包装完（主线程调用）：记录结果。

        Args:
            package: 包名。
            ok: 是否成功。
        """
        button = self._buttons.get(package, None)
        if button is not None and not ok:
            button.setEnabled(True)
            button.setText('重试')
        count = self.progress.value() + 1
        self.progress.setValue(count)
        self._set_status(f'已处理 {count}/{self.progress.maximum()} 个包 ...')

    def _on_install_finished(self):
        """安装线程结束（主线程调用）：收尾并重新检测一次。

        ⚠️ 必须重新检测：装完之后状态、版本号都变了，而且**成功的行要撤掉
        「安装」按钮**。
        """
        self._install_thread = None
        self.button_check.setEnabled(True)
        self.progress.setVisible(False)
        self.log.appendPlainText('===== 安装结束，重新检测依赖 ... =====')
        self.start_check()

    # ------------------------------------------------------------------ 其它

    def contextMenuEvent(self, event):
        """右键菜单：重新检测 / 复制依赖清单 / 清空日志。"""
        menu = QtWidgets.QMenu(self)
        menu.addAction('重新检测', lambda: self.refresh(force=True))
        menu.addAction('一键安装缺失(必需)', self.install_missing_required)
        menu.addSeparator()
        menu.addAction('复制依赖清单', self._copy_list)
        menu.addAction('清空日志', self.log.clear)
        menu.popup(event.globalPos())

    def _copy_list(self):
        """把当前表格内容复制到剪贴板（纯文本，方便贴到 Issue 里）。"""
        lines = ['\t'.join(COLUMNS)]
        for i_row in range(self.table.rowCount()):
            words = []
            for i_col in range(self.table.columnCount()):
                if i_col == 5:
                    words.append('')
                    continue
                item = self.table.item(i_row, i_col)
                words.append(item.text() if item is not None else '')
            lines.append('\t'.join(words))
        try:
            QtWidgets.QApplication.clipboard().setText('\n'.join(lines))
            self._set_status('依赖清单已复制到剪贴板。')
        except Exception as err:
            print(f'复制失败: {err}')


# =============================================================================
# GUI 接口与菜单
# =============================================================================

def check_runtime_env():
    """显示「运行环境」控件（检查第三方依赖是否安装）.

    这个函数被注册成 GUI 函数（``gui.add_func``），所以控制台里可以
    ``gui.check_runtime_env()`` 直接打开；菜单「设置 → 运行环境」也调它。

    ⚠️ 只通过 ``gui.get_widget`` 打开（而不是直接 ``RuntimeEnvView()``）：
    这样标签页只会有**一个**，重复调用只是把已有页面切到前面。
    """

    def oper(widget):
        widget.gui_restore = 'gui.check_runtime_env()'  # 重启后自动恢复本标签页
        widget.refresh()

    gui.get_widget(
        RuntimeEnvView, caption=CAPTION, on_top=True,
        icon='set', oper=oper,
        tooltip='检查 zmlx 的第三方依赖是否安装，并支持一键安装')


@execute_once(file=__file__)
def setup_ui():
    """注册 GUI 函数与菜单项（本文件作为插件被 ``load_all`` 执行时调用）.

    ⚠️ 本函数在**控制台内核线程**里执行，``gui.add_func`` / ``gui.add_action``
    会被 GuiApi 派发到主线程执行（见 ``zmlx/ui/main.py`` 的
    ``__console_kernel``）。

    ⚠️ 本插件声明了 ``# ** enabled = False``（**默认不加载**）：用户若在
    「设置 → 插件」里勾上它，本函数才会被执行 —— 于是「设置 → 运行环境」才
    出现。**菜单的可见性就是「用户有没有启用它」**。
    """
    gui.add_func('check_runtime_env', check_runtime_env)

    # ★ 菜单挂在「设置」下，**不是「帮助」**：这一项是**本机的运行环境**
    #   （依赖装没装、缺的能一键装），属于「配置这台机器」而不是「获取帮助」——
    #   它与「设置」下的系统 / 插件 / 路径 / 求解器 / 样式表同类。
    #   ⚠️ 菜单标题与 `main.py` 里那几处**逐字一致**（都写 ``'设置'``），
    #   否则 `get_menu` 会另建一个同名的新顶层菜单，界面上出现两个「设置」。
    #   ⚠️ 那几项的定义在 ``main.py``（主窗口自己的 action），本项在
    #   ``setups``（可选扩展），两处都可能先执行 —— 但 ``get_menu`` 是
    #   **按标题查找、缺则新建**，所以先来后到都不影响它们并进同一个菜单。
    gui.add_action(
        menu='设置', name='check_runtime_env',
        text='运行环境',
        icon='set',
        tooltip='检查 zmlx 依赖的第三方包是否已安装，缺失的可一键安装',
        slot=check_runtime_env,
        overwrite=False,
    )


def test_1():
    """直接运行本文件时的自测：显示控件窗口。"""
    app = QtWidgets.QApplication(sys.argv)
    widget = RuntimeEnvView()
    widget.resize(900, 620)
    widget.show()
    sys.exit(app.exec())


# ⚠️⚠️ 两条路径必须**分成两支**、而且**先判插件**：插件机制执行时 ``__name__``
#    是 ``'__zml_plugin__'``（见 :func:`zmlx.ui.plugins._alg._make_space`），
#    直接 ``python runtime_env.py`` 才是 ``'__main__'``。
#
#    历史教训（2026-10-19）：搬成插件时这里曾写成「先 ``if __name__ == '__main__':
#    test_1()``、再判断 ``_PLUGIN_FLAG in globals()`` 调 setup_ui」两段并列。当时
#    插件路径的 ``__name__`` **也是** ``'__main__'``，于是 ``test_1()`` 被无条件
#    执行 —— 它建第二个 ``QApplication``、在控制台内核线程上调 ``exec()``，最后
#    ``sys.exit()`` 抛 ``SystemExit``（``BaseException``，``load_all`` 与
#    ``main.py`` 的 ``except Exception`` 都兜不住），``setup_ui()`` 永远执行不到。
#    表现：「设置 → 插件」里勾上「运行环境」、重启后菜单里始终没有它。
if __name__ == '__zml_plugin__':
    setup_ui()      # 插件路径（由 load_all exec 执行）：只注册，不开窗口

if __name__ == '__main__':
    test_1()        # 直接 python runtime_env.py：开窗口自测
    # ⚠️ 用独立的 ``if`` 而不是 ``elif``：两种运行方式的判断互不相干。
