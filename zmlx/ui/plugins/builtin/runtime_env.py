# ** name = '运行环境'
# ** desc = '「设置 → 运行环境」：检查 zmlx 依赖的第三方包是否已安装，缺失的可一键安装'
# ** enabled = True
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

  ⚠️ 2026-11-01 用 AST 重扫了一遍 ``zmlx/``（导出名 → 发行包名按下面的
  :data:`IMPORT_TO_PACKAGE` 映射），清单已补齐。扫描口径与取舍写在
  :data:`OPTIONAL_DEPENDENCIES` 上方的注释里，**加新的第三方 import 时请同步那里**。

线程模型（重要）
----------------
检测与安装都**不在 GUI 线程里执行**（安装尤其不能：一次 pip 可能几分钟）：

- :class:`EnvCheckThread`：逐个探测依赖（``importlib.metadata`` 查版本 +
  ``importlib.util.find_spec`` 查可导入性），结果用信号发回主线程再填表；
- :class:`InstallThread`：用 ``subprocess`` 起 pip / conda，逐行读输出并
  ``print`` 到**界面控制台**（2026-11-01 起不再单开日志文本框 —— 控制台支持
  ANSI 颜色，pip 自己的彩色输出能原样显示）。

⚠️ 子线程里**绝不碰任何控件**；信号是跨线程自动排队投递的，接收槽一定跑在
GUI 线程里。``print`` 也安全：``stdout`` 是 ``MainWindow.write``，它把整段投递到
GUI 线程再写控件。

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

#: 导入名 → pip 上的**发行包名**（两者不一致的那些）。
#:
#: 为什么需要一张表：扫描 ``zmlx`` 只能得到 ``import`` 里写的**导入名**
#: （``cv2`` / ``PIL`` / ``yaml``），而「装没装 / 怎么装」问的是**发行包名**
#: （``opencv-python`` / ``pillow`` / ``pyyaml``）。直接拿导入名去
#: ``pip install`` 有时候能撞对（pip 会认一部分别名），有时候会装错
#: （``sklearn`` 装的是个空的占位包，真包叫 ``scikit-learn``），所以必须显式映射。
#:
#: 其余导入名**与发行包名同名**（``numpy``、``reaktoro``、``pyvista`` …），
#: 不在这张表里 —— 表里只放「不一样」的，写全了反而容易和真实情况脱节。
IMPORT_TO_PACKAGE = {
    'cv2': 'opencv-python',
    'PIL': 'pillow',
    'mpl_toolkits': 'matplotlib',
    'sklearn': 'scikit-learn',
    'yaml': 'pyyaml',
    'win32com': 'pywin32',
    'cupyx': 'cupy',
}

#: 可选依赖：**扫描 ``zmlx`` 源码里全部 ``import``** 得到的第三方库。
#:
#: 这些库缺失时只会让**对应的那一块功能**不可用（例如没有 CoolProp 就换回
#: 内置的流体物性），因此单独成组。``package`` 是 pip 上的发行包名，``name``
#: 是导入名，``note`` 说明它被谁用、缺了会怎样。
#:
#: 口径（2026-11-01 用 AST 重扫 ``zmlx/`` 后定稿，**加新的第三方 import 时
#: 请回来同步**）
#: ----------------------------------------------------------------------
#:
#: 1. **不列**核心依赖（``numpy`` / ``scipy`` / ``matplotlib`` / ``pyqtgraph`` /
#:    ``PyQt6`` / ``PIL`` / ``pyvista`` / ``vtk`` …）—— 它们在「必需」组里，
#:    由 :func:`dependency_list` 按包名去重，写在这里也是白写。
#: 2. **不列** ``_Trash/`` *（历史垃圾目录）里的 import。
#: 3. **不列** ``zmlx`` 自己的模块（``shapes`` / ``train`` / ``gas_mig`` /
#:    ``wat_disp_oil``）—— 那些是 ``demos/`` 里「同目录脚本 import 同目录模块」或
#:    条件导入，不是第三方库。
#: 4. **不列** ``PyQt5``：只是 ``zmlx/ui/pyqt.py`` 的**兼容分支**（PyQt6 优先、
#:    缺失时才回退），装上它反而是错的方向。
#: 5. **列上** ``torch``（``scen/uv_equilibrium`` 的训练脚本）与 ``requests``
#:    （``scen/ai_assistant/chat.py``，AI 辅助插件的必需项）—— 前者只有模型训练
#:    才用，后者整个 AI 辅助都靠它，都属于「缺了只影响一块功能」。
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
         note='CUDA 线性求解（zmlx.exts.cuda_sol；另含 cupyx）'),
    dict(package='opencv-python', name='cv2',
         note='图像处理（zmlx.algs.image）'),
    dict(package='markdown', name='markdown',
         note='Markdown 渲染（zmlx.ui.widgets.md_view）'),
    dict(package='requests', name='requests',
         note='HTTP 请求（zmlx.scen.ai_assistant.chat，AI 辅助插件的必需项）'),
    dict(package='torch', name='torch',
         note='U 形网络训练（zmlx.scen.uv_equilibrium 的训练脚本）'),
    dict(package='iapws', name='iapws',
         note='水/蒸汽物性（zmlx.scen.geothermal_helium）'),
    dict(package='pyXSteam', name='pyXSteam',
         note='水/蒸汽物性（zmlx.fluids.conf.gas_density.h2o）'),
    dict(package='chemicals', name='chemicals',
         note='液体密度（zmlx.fluids.conf.liqu_density）'),
    dict(package='pygit2', name='pygit2',
         note='程序更新（zmlx.algs._update_by_git；有 git CLI 时用不到）'),
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
        from zmlx.data.dep import import_names, package_names, package_notes
    except Exception as err:
        print(f'读取 zmlx.data.dep 失败，使用内置兜底清单: {err}')
        package_names = list(FALLBACK_PACKAGES)
        if sys.platform.startswith('win'):
            package_names.append('pywin32')
        import_names = {}
        package_notes = {}

    deps = []
    for package in package_names:
        if package == 'pypiwin32':
            continue  # pywin32 的废弃别名，见模块文档
        deps.append(dict(
            package=package,
            name=import_names.get(package, None),
            group='必需',
            # 「备注」列直接显示它：一句话说清这个包在 zmlx 里干什么。
            note=package_notes.get(package, 'zmlx 的核心依赖'),
        ))
    return deps


def dependency_list():
    """返回控件要展示的完整依赖清单（必需在前，可选在后）。

    Returns:
        list: :func:`core_dependencies` 的结果，后面接
        :data:`OPTIONAL_DEPENDENCIES`（按**发行包名**去重）。
    """
    deps = core_dependencies()
    known = {dep['package'].lower() for dep in deps}
    for item in OPTIONAL_DEPENDENCIES:
        # ⚠️ 去重键用 package_of(name)：只给了导入名的条目也要认出来 ——
        #    否则「cv2」会被当成一个新包，与已有的「opencv-python」并列两行。

        package = item.get('package', None) or package_of(item.get('name'))
        if not package or package.lower() in known:
            continue
        known.add(package.lower())
        deps.append(dict(item, package=package, group='可选'))
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


def package_of(name):
    """把**导入名**换成 pip 上的**发行包名**（纯计算）.

    Args:
        name: ``import xxx`` 里的那个名字（如 ``cv2``）；``None`` / 空串原样返回。

    Returns:
        str | None: 发行包名；未在 :data:`IMPORT_TO_PACKAGE` 里登记时原样返回
        —— 按「导入名与发行包名同名」的惯例处理。
    """
    if not isinstance(name, str) or len(name) == 0:
        return name
    return IMPORT_TO_PACKAGE.get(name.split('.')[0], name)


def check_dependency(dep):
    """检测单个依赖是否已安装（纯计算，不碰界面）。

    判定规则：

    - 有导入名时以「能否 import」为准（这才是运行时真正关心的）；
      ``importlib.metadata`` 只用来取版本号；
    - 没有导入名时退化为「``importlib.metadata`` 里有没有这个发行包」。

    ⚠️ **``package`` 缺省时不再拿 ``name`` 顶替**（2026-11-01 修）：旧写法
    ``dep['package']`` 在只给了导入名的条目上会直接 ``KeyError``，而扫描结果
    天然是「先有导入名」，所以必须能从 ``name`` 反推发行包名 —— 走
    :func:`package_of`，它认得 ``cv2 → opencv-python`` 这类不同名的。

    Args:
        dep: 依赖描述（见 :func:`dependency_list`）。

    Returns:
        dict: ``dep`` 的副本，另加：

        - ``installed`` (bool)：是否可用；
        - ``version`` (str | None)：发行包版本号；
        - ``note`` (str)：一句话说明（**「备注」列直接显示的就是它**）；
        - ``detail`` (str)：给用户看的补充说明（放进单元格 tooltip）。
    """
    name = dep.get('name', None)
    package = dep.get('package', None) or package_of(name)
    version = _dist_version(package) if package else None
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
    result['package'] = package
    # ⚠️ 「备注」列**直接读 note**，不再从 detail 里切 —— detail 是给 tooltip 的
    #    多行说明（已装版本 / 导入名 / 用法），与「这个包干什么用的」是两件事。
    result.setdefault('note', '')
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

    每个包的安装过程会**逐行**读出来，用 ``print`` 送进界面控制台；每个包结束时
    发一次 :attr:`sig_done`。

    ⚠️ ``install`` 是**真正的慢活**（一次 pip 可能几分钟），这正是它必须待在
    子线程里的原因 —— 否则整个界面会假死。

    ⚠️ 异常绝不允许逃出 :meth:`run`，否则线程静默死掉、界面永远停在
    「安装中...」。

    ⚠️ **输出走 ``print``，不再发 ``sig_output`` 信号**（2026-11-01 按用户要求）：
    界面已经有一块**支持 ANSI 颜色**的控制台（``OutputWidget``），安装日志没有
    理由再单开一个只读文本框。``print`` 在这里是安全的 —— ``stdout`` 是
    ``MainWindow.write``，它把整段投递到 GUI 线程（见那里的注释），子线程只管
    打印、不碰控件。

    Attributes:
        sig_done: 信号，携带 ``(包名, 是否成功)``。
    """

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
        """执行一条安装命令，把输出逐行 ``print`` 到界面控制台。

        Args:
            cmd: 命令行参数列表。
            package: 包名（只用于日志）。

        Returns:
            bool: 子进程返回码为 0 时返回 True。
        """
        print(f'{ANSI_INFO}[安装] 开始安装 {package}{ANSI_RESET}')
        print(f'{ANSI_DIM}$ {" ".join(cmd)}{ANSI_RESET}')
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, encoding='utf-8', errors='replace')
        except Exception as err:
            print(f'{ANSI_ERROR}[安装] 启动安装进程失败: {err}{ANSI_RESET}')
            return False
        try:
            with proc.stdout:  # 显式关闭管道，否则会漏一个文件对象
                for line in proc.stdout:
                    # ⚠️ 逐行 print：界面控制台会**解释其中的 ANSI 转义码**，
                    #    所以 pip 自带的颜色（下载进度、错误红字）原样保留 ——
                    #    不要在这里 strip 掉它们。
                    print(line.rstrip())
            proc.wait()
        except Exception as err:
            print(f'{ANSI_ERROR}[安装] 读取安装输出失败: {err}{ANSI_RESET}')
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
                print(f'{ANSI_WARN}[conda:{package}] 失败: {err}{ANSI_RESET}')
            print(f'{ANSI_WARN}[conda:{package}] 失败，回退 pip{ANSI_RESET}')
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
                    print(f'{ANSI_ERROR}[安装] {package} 出现异常: {err}'
                          f'{ANSI_RESET}')
                    ok = False
                # ⚠️ 成功 / 失败用颜色区分：控制台支持 ANSI（OutputWidget 的 _Ansi）
                color = ANSI_OK if ok else ANSI_ERROR
                print(f'{color}[安装] {package} '
                      f'{"成功" if ok else "失败"}{ANSI_RESET}')
                self.sig_done.emit(package, bool(ok))
        except Exception as err:  # 防御性：异常绝不能逃出 run()
            print(f'{ANSI_ERROR}[安装] 安装线程异常: {err}{ANSI_RESET}')


# =============================================================================
# 控件
# =============================================================================

#: 表格的列标题。
COLUMNS = ['依赖包', '导入名', '分组', '状态', '版本', '备注', '操作']

#: 每列「按什么排序」—— 决定这一列的值如何装进 ``QTableWidgetItem``。
#:
#: ============  ========================================================
#: 取值           含义
#: ============  ========================================================
#: ``'text'``     普通文字，直接比较
#: ``'number'``   数值：显示用原文、排序用数值（版本号 / 分组序）
#: ``'state'``    「状态」列：显示「已安装 / 未安装 / 检测中...」，
#:                排序按**重要性**（未安装在前）而不是按汉字
#: ``'none'``     「操作」列：按钮不是 item、没有可比较的值
#: ============  ========================================================
COLUMN_KINDS = ['text', 'text', 'number', 'state', 'number', 'text', 'none']

#: 「备注」列的列号与「操作」列的列号（:meth:`RuntimeEnvView._layout_columns` 用）。
COL_NOTE = 5
COL_ACTION = 6

#: 列宽的**优先级**：(最小, 理想, 可伸展)。
#:
#: ``_layout_columns`` 按这个顺序分配宽度：
#:
#: 1. 先给**所有**列它的「最小」宽度；
#: 2. 再按顺序（依赖包 → 操作 → 导入名 → 版本 → 分组 → 状态 → 备注）补到「理想」；
#: 3. 还剩的空间只给「可伸展」的列 —— 只有**备注**。
#:
#: 所以「依赖包」与「操作」是**优先保证**的（用户要求，2026-11-01）：窗口再窄，
#: 它们也先拿到自己的理想宽度；空间不够时，**「备注」整列隐藏**而不是被压成一
#: 条看不懂的窄缝（见 :meth:`RuntimeEnvView._layout_columns`）。
#:
#: ⚠️ 「依赖包」的理想宽度**按实际名字算**（:meth:`RuntimeEnvView._fitted_width`
#: 用 ``QFontMetrics`` 量最长的包名），不是写死一个偏大的数 —— 用户要求「足够
#: 显示名字即可」。最小宽度 110 是兜底：真到那么窄就停在那儿，而不是继续压，
#: 免得压到连名字都认不出。
#:
#: ⚠️ 「依赖包」不再用 Qt 的 ``Stretch``：那会让它把整块富余全吃掉，富余应当
#: 留给备注。
COLUMN_WIDTHS = {
    0: (110, 190, False),   # 依赖包：理想值由 _fitted_width 按名字实测覆盖
    1: (86, 120, False),    # 导入名
    2: (52, 52, False),     # 分组
    3: (72, 72, False),     # 状态
    4: (74, 96, False),     # 版本
    COL_NOTE: (150, 300, True),   # 备注：唯一可伸展的列
    COL_ACTION: (64, 64, False),  # 操作
}

#: 补宽度的**顺序**（越靠前越优先拿到空间）。
#:
#: 依赖包 / 操作在最前 —— 它们是「优先保证」的两列；备注排**最后**，因为它是
#: 空间不够时那个该让步的（不够就整列藏起来，见 ``_layout_columns``）。
COLUMN_PRIORITY = (0, COL_ACTION, 1, 4, 2, 3, COL_NOTE)

#: 竖向滚动条 + 边框留下的余量（算列宽时先扣掉）。
_TABLE_SLACK = 14

#: 显示**全部**列（含备注）时至少需要的宽度。
#:
#: 低于它就只能靠横向滚动条 —— 与其让用户左右拖，不如先牺牲备注把整张表塞进
#: 当前宽度（用户要求：宽度不够时隐藏备注，优先保证「依赖包」和「操作」）。
_MIN_TOTAL = sum(lo for lo, _, _ in COLUMN_WIDTHS.values()) + _TABLE_SLACK

#: 排序值存在 item 的哪个角色上（**由** :class:`_SortItem` **自己比较**）。
#:
#: ⚠️ **不能靠 PyQt 默认的 ``__lt__``**：它对**自定义角色**不比较，会把值转成
#: 字符串再比（实测 ``'0.4.10'`` 与 ``'0.46.4'`` 变成字符串序）；而把排序值塞进
#: ``DisplayRole`` 又会顶掉显示文字。所以显示文字留在 ``DisplayRole``（Qt 原样
#: 显示），排序值单独存这里，并在 :meth:`_SortItem.__lt__` 里显式读出来比较。
_ROLE_SORT = QtCore.Qt.ItemDataRole.UserRole + 1

#: 「状态」列的排序权重：越小越靠前（升序 = 未安装 → 已安装）。
_STATE_RANK = {'未安装': 0, '检测中...': 1, '已安装': 2}

#: 「分组」列的排序权重：必需在前。
_GROUP_RANK = {'必需': 0, '可选': 1}

#: 版本号排序时补零到几段（见 :func:`_version_key`）。
_VERSION_PAD = 4


def _version_key(text):
    """把版本号字符串切成可比较的元组（缺失 / 非法值排在**最前**）.

    ⚠️ **不能按字符串比**：那样 ``'2.14.1'`` 会排在 ``'2.3.3'`` 之后。这里按
    ``(数字序列, 原文)`` 比较。

    ⚠️⚠️ **必须补零到定长再比**（2026-11-01 实测踩到）：只给数字元组的话，
    Python 元组比较是**逐项先比、长度只在前缀完全相同时才起作用** —— 于是
    ``(3, 11)`` 排在 ``(3, 1, 10)`` **之后**（``11 > 1`` 先于长度生效），实测
    ``3.11`` 跑到了 ``3.10.7`` 后面。补零成 ``(3, 11, 0, 0)`` /
    ``(3, 1, 10, 0)`` 才是真正的语义版本序。

    ⚠️ **无版本号（``'-'``）排在最前**：原先让它沉到最后，结果降序时它跑到最上面
    —— 而「没有版本号」正是最该被看见的（通常是没装的包）。

    Args:
        text: 版本号原文（可能为 ``None`` / ``'-'``）。

    Returns:
        tuple: ``(数字序列, 原文)``；无值时为 ``((), '')``（比任何带数字的都小）。
    """
    if not text or text == '-':
        return ((), '')
    numbers = []
    for part in str(text).replace('-', '.').split('.'):
        digits = ''.join(ch for ch in part if ch.isdigit())
        numbers.append(int(digits) if digits else 0)
    numbers = numbers[:_VERSION_PAD]
    numbers += [0] * (_VERSION_PAD - len(numbers))
    # ⚠️ 必须是 (数字, 原文) 的**元组**：只要返回的东西不是 tuple，Qt 会把它当
    #    字符串排序（PyQt 的 `__lt__` 结果不被认作比较器），实测表现为「按字符串
    #    排」—— 所以最后再套一层 tuple 兜底，别让任何分支漏回来一个 list。
    return (tuple(numbers), str(text))


#: 各种状态下的文字颜色。
COLOR_OK = '#1a7f37'        # 已安装（绿）
COLOR_MISSING = '#c0392b'   # 必需依赖缺失（红）
COLOR_OPTIONAL = '#b9770e'  # 可选依赖缺失（橙）

# ANSI 转义码：安装日志走 ``print`` 进界面控制台，那里支持颜色（见 ``OutputWidget``
# 的 ``_Ansi``）。用 SGR 的**基础色**（31 红 / 32 绿 / 33 黄 / 36 青），控件会按
# 当前主题自动换成合适的色值（浅色 / 暗色各一套），所以不要写 256 色或真彩 ——
# 那样暗色模式下可能看不见。
ANSI_RESET = '\033[0m'
ANSI_INFO = '\033[36m'    # 青：开始安装 / 命令回显
ANSI_DIM = '\033[90m'     # 亮黑：命令行回显（比正文淡一档）
ANSI_OK = '\033[32m'      # 绿：成功
ANSI_WARN = '\033[33m'    # 黄：回退 / 警告
ANSI_ERROR = '\033[31m'   # 红：失败


class _SortItem(QtWidgets.QTableWidgetItem):
    """带**自定义排序键**的表格单元格.

    ⚠️⚠️ **为什么需要这个子类**（2026-11-01 实测）：``QTableWidget`` 点标题排序时
    调的是 item 的 ``__lt__``，而 PyQt6 的默认实现对**自定义角色**不比较 —— 它把
    值转成字符串再比，于是版本号退化成字符串序（``0.4.10`` > ``0.46.4``）。把
    排序值塞进 ``DisplayRole`` 又能生效，但那样会顶掉显示文字。

    所以这里显式覆写 ``__lt__``：

    - 两格都有排序键 → 按键比（键由调用方给，保证是可比的类型）；
    - 只有一格有 → 有键的排在前面（「操作」列里只有按钮行有键）；
    - 都没有 → 退回原来的文字比较，行为与不写这个类时一致。
    """

    def __lt__(self, other):
        """按排序键比较（两侧都没有键时退回文字比较）。"""
        mine = self.data(_ROLE_SORT)
        theirs = other.data(_ROLE_SORT) if isinstance(
            other, QtWidgets.QTableWidgetItem) else None
        if mine is not None and theirs is not None:
            return mine < theirs
        if mine is not None:
            return True
        if theirs is not None:
            return False
        return super().__lt__(other)


class RuntimeEnvView(QtWidgets.QWidget):
    """运行环境检测控件：列出依赖、标出是否安装、缺失的可一键安装。

    布局从上到下：工具条（重新检测 / 安装缺失 / 只看未安装）→ 依赖表格。

    ⚠️ **没有「安装日志」文本框**（2026-11-01 按用户要求）：安装输出走 ``print``
    进**界面控制台**（支持 ANSI 颜色，pip 自己的彩色输出原样保留），控件里只留
    工具条上的进度条 + 表格里的「安装中 / 重试」按钮状态。

    ⚠️ **检测与安装都在后台线程里跑**（:class:`EnvCheckThread` /
    :class:`InstallThread`），界面从不被阻塞；子线程只发信号 / ``print``，不碰控件。

    ⚠️ :meth:`refresh` 只做「要不要起线程」的判断（微秒级），满足主窗口对
    ``refresh()`` 必须快的硬性要求（见 ``zmlx/ui/widget/AGENTS.md``）。

    表格的两个约定（2026-11-01 按用户要求定）
    ----------------------------------------

    - **点列标题排序**：每列都排得动。「状态」「分组」按**重要性**排（未安装 /
      必需在前）而不是按汉字，版本号按**数值**排（``2.3.3`` 不会跑到 ``2.14.1``
      后面）。排序值单独存在 :data:`_ROLE_SORT` 角色上，与显示文字互不影响，
      所以「已安装 / 未安装」这些汉字怎么改都不影响排序。
    - **宽度不撑大上一级控件**：容器不设最小宽度；文字被截断时，**完整内容在
      tooltip 里**。竖向滚动条常驻，避免「滚动条出现 / 消失」把整页最小宽度顶大。
    - **列宽按优先级分配**（:meth:`_layout_columns`，见 :data:`COLUMN_WIDTHS`）：
      「依赖包」只为显示名字取宽（:meth:`_fitted_width` 实测）且**不吃富余**，
      「操作」恒保；富余只给备注，**空间不够时备注整列隐藏**、宽回来自动恢复。

    列（:data:`COLUMNS`，按显示顺序）
    --------------------------------

    依赖包 / 导入名 / 分组 / 状态 / 版本 / **备注** / 操作。

    ⚠️ **「备注」列**（2026-11-01 按用户要求加）说明这个包在 zmlx 里干什么用，文字
    来自依赖条目自己的 ``note`` 字段：可选依赖写在 :data:`OPTIONAL_DEPENDENCIES`，
    必需依赖写在 :data:`zmlx.data.dep.package_notes`（唯一来源，改那边界面就跟着变）。
    ⚠️ 加列时**同步改** :data:`COLUMNS` 与 :data:`COLUMN_KINDS`，并检查
    ``_fill_table`` / ``_copy_list`` 里有没有写死的列号 —— 后者已改为按
    ``COLUMN_KINDS`` 找「操作」列（按钮不是 item，不能照抄）。
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
        # ⚠️ **总宽必须压在 ~400 px 以内**（用户要求：宽度不能把上一级控件撑大，
        #    2026-11-01 实测）：这一行五样东西横向排开，`一键安装缺失(必需)` 一个
        #    字不省就有 134 px，合计把整个控件顶到 396 px。三处收紧 —— 状态文字
        #    改为可被压窄、两个按钮用更短的文案、进度条去掉 160 px 的硬下限。
        bar = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel(self)
        # 状态文字可能很长（「共 30 项，未安装 3 项（其中必需 0 项）」），但它是
        # 最该被压缩的那个：minWidth 给小 + `Ignored` 横向策略 ⇒ 标签不顶住布局。
        # 完整文字见 _set_status 写进 tooltip。
        self.status_label.setMinimumWidth(40)
        self.status_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred)
        bar.addWidget(self.status_label, 1)

        self.only_missing = QtWidgets.QCheckBox('只看未安装', self)
        self.only_missing.setToolTip('勾选后隐藏已经安装的依赖，剩下的就是需要补的')
        self.only_missing.toggled.connect(self._apply_filter)
        bar.addWidget(self.only_missing)

        # ⚠️ 按钮的**最小宽度**由 Qt 按「文字 + 内边距」算死（这里各 80 px），
        #    单靠缩短文案压不下去。给两个按钮一个更小的下限即可 —— 文字本身
        #    不会失败：它们各自的 tooltip 写着完整含义，而且主窗口正常宽度下
        #    按钮本来就按 sizeHint 显示，只有窗口被压到极窄时才会截断。
        self.button_check = QtWidgets.QPushButton('重新检测', self)
        self.button_check.setToolTip('在后台线程里重新检测一遍（不会卡住界面）')
        self.button_check.clicked.connect(self.start_check)
        self.button_check.setMinimumWidth(56)
        bar.addWidget(self.button_check)

        self.button_install_all = QtWidgets.QPushButton('安装缺失项', self)
        self.button_install_all.setToolTip(
            '安装所有缺失的**必需**依赖。可选依赖请按行点击「安装」。')
        self.button_install_all.setEnabled(False)  # 检测出缺失的必需依赖后才可用
        self.button_install_all.clicked.connect(self.install_missing_required)
        self.button_install_all.setMinimumWidth(56)
        bar.addWidget(self.button_install_all)

        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setMinimumWidth(60)
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

        # ⚠️ **宽度不能把上一级控件撑大**（用户要求，2026-11-01）：
        #    1. 所有列都给一个小的 minimumSectionSize —— 默认是 26~30 px，
        #       我们要能压到 40 px 而不被下限顶住；
        #    2. 列宽**不再由 Qt 的 Stretch 分配**，而是 :meth:`_layout_columns`
        #       按优先级算（见那边的说明）：依赖包 / 操作 优先拿到空间，富余的
        #       才给备注，**不够就把备注整列藏起来**；
        #       「备注」与「依赖包」都不用 ResizeToContents —— 让最长的一块决定
        #       整张表，与「不撑大上级」直接冲突；
        #    3. 竖向滚动条**常驻**（关掉 Qt 默认的「按需显示」）：否则
        #       「先窄后宽、滚动条消失」时多出来的 ~16 px 会把整页最小宽度撑大，
        #       窗口就再也缩不回去。
        #    ⚠️ 列太窄时文字被截断，但**完整内容在 tooltip 里**（见 _fill_table）。
        hdr = self.table.horizontalHeader()
        hdr.setMinimumSectionSize(40)
        for i_col in range(len(COLUMNS)):
            hdr.setSectionResizeMode(
                i_col, QtWidgets.QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # ⚠️ **点标题排序**（用户要求，2026-11-01）：必须等第一次 _fill_table 铺完
        #    才开启 —— 空表时开排序无事发生，而 compare → 建临时行时会打日志。
        #    「操作」列开了排序也只是按空 item 排，点它不会崩。
        self.table.setSortingEnabled(True)

        # ⚠️ 宽度分配挂在自己的 resizeEvent 上（不设任何最小宽度：本控件自己就该
        #    能被压窄，撑大上一级的是它）。首次布局由 _fill_table 之后调用一次。
        self._layout_columns()

        # ⚠️ 不要给表格设 minimumWidth：（历史上是 setColumnWidth(0, 220) + 固定
        #    宽度，窄窗口下整页拉宽。）
        layout.addWidget(self.table, 1)

        # ⚠️ **不再有「安装日志」文本框**（2026-11-01 按用户要求）：安装输出直接
        #    ``print`` 到界面控制台 —— 那块面板本来就支持 ANSI 颜色、有滚动历史和
        #    右键复制，单开一个只读文本框是重复造轮子。见 :class:`InstallThread`。

    # ------------------------------------------------------------------ 列宽

    def resizeEvent(self, event):
        """窗口尺寸变了（主线程调用）：重新分配列宽。"""
        super().resizeEvent(event)
        self._layout_columns()

    def _fitted_width(self, i_col, minimum):
        """算出「正好装下这一列最长文字」的宽度（不低于 ``minimum``）.

        ⚠️ 用 ``QFontMetrics.horizontalAdvance`` 量的是**当前字体**下的真实宽度，
        所以换字体、改 DPI、系统缩放之后会自动跟着变 —— 写死一个像素值做不到这点。

        Args:
            i_col: 列号。
            minimum: 下限（量出来更小就用它）。

        Returns:
            int: 建议的列宽（已含单元格左右留白）。
        """
        metrics = QtGui.QFontMetrics(self.table.font())
        style = self.table.style()
        pad = (
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_FocusFrameHMargin) * 2
            + style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_DefaultFrameWidth) * 2
            + 8)  # 排序箭头 / 溢出让出的一点余量
        widest = metrics.horizontalAdvance(COLUMNS[i_col])
        for i_row in range(self.table.rowCount()):
            item = self.table.item(i_row, i_col)
            if item is not None:
                widest = max(widest, metrics.horizontalAdvance(item.text()))
        return max(int(minimum), int(widest + pad))

    def _layout_columns(self):
        """按 :data:`COLUMN_WIDTHS` 的优先级分配列宽（**空间不够就藏备注**）.

        规则（用户要求，2026-11-01）：

        - 「依赖包」与「操作」**优先保证**，是这两列先拿到各自的宽度；
        - **「依赖包」只为显示名字取宽度**（实测最长的包名，见
          :meth:`_fitted_width`），不吃富余；
        - 富余空间**只给「备注」**；
        - 空间连「备注」的最小宽度都放不下 → **把备注整列隐藏**，宁可少一列
          也不把它压成一条看不懂的窄缝；窗口变宽时自动恢复。

        ⚠️ 这是**布局**，不是「限制宽度」：本控件仍然可以被压到很窄，压窄的代价
        只是少显示一列，而不是把上一级控件撑开。
        """
        table = self.table
        if table is None:
            return
        total = (table.viewport().width() - _TABLE_SLACK)
        if total <= 0:
            return  # 还没布局出来，等下一次 resizeEvent

        # ---- 依赖包：理想宽度按**实际名字**实测，不做写死的偏大值 ----
        widths_ideal = {k: v[1] for k, v in COLUMN_WIDTHS.items()}
        widths_ideal[0] = self._fitted_width(0, COLUMN_WIDTHS[0][0])

        # ---- 显示全部列（含备注）至少要多少；不够就先把备注藏起来 ----
        besides_note = sum(
            COLUMN_WIDTHS[k][0] for k in COLUMN_WIDTHS if k != COL_NOTE)
        note_min = COLUMN_WIDTHS[COL_NOTE][0]
        note_visible = (besides_note + note_min + _TABLE_SLACK) <= total
        if table.isColumnHidden(COL_NOTE) != (not note_visible):
            table.setColumnHidden(COL_NOTE, not note_visible)

        # ---- 两次分配：先给所有人「最小」，再按优先级补到「理想」 ----
        widths = {}
        rest = total
        for i_col, (lo, _, _) in COLUMN_WIDTHS.items():
            if i_col == COL_NOTE and not note_visible:
                continue  # 藏起来的列不占宽度
            widths[i_col] = lo
            rest -= lo
        for i_col in COLUMN_PRIORITY:
            if i_col not in widths:
                continue
            hi = widths_ideal[i_col]
            if rest > 0:
                extra = min(rest, max(0, hi - widths[i_col]))
                widths[i_col] += extra
                rest -= extra
        # ---- 富余只给可伸展的列（只有备注） ----
        if rest > 0:
            for i_col, (_, _, stretch) in COLUMN_WIDTHS.items():
                if stretch and i_col in widths:
                    widths[i_col] += rest
                    break

        for i_col, width in widths.items():
            table.setColumnWidth(i_col, max(1, int(width)))
        if not note_visible:
            # 藏起来的列也要给个合理宽度：恢复显示时直接用，不必等下一轮布局
            table.setColumnWidth(COL_NOTE, note_min)

    def _make_item(self, i_col, text, sort_value=None, tooltip=None):
        """造一个表格单元格（显示文字与排序值分开存）。

        Args:
            i_col: 列号（用来查 :data:`COLUMN_KINDS`）。
            text: 显示的文字。
            sort_value: 排序用的值；``None`` 表示「按显示文字排」。
            tooltip: 悬停提示（**列被压窄时靠它看全文**）。

        Returns:
            QtWidgets.QTableWidgetItem: 造好的单元格。
        """
        item = _SortItem(text)
        kind = COLUMN_KINDS[i_col] if i_col < len(COLUMN_KINDS) else 'text'
        if sort_value is not None:
            item.setData(_ROLE_SORT, sort_value)
        elif kind == 'number':
            item.setData(_ROLE_SORT, _version_key(text))
        if tooltip is not None:
            item.setToolTip(tooltip)
        return item

    def _fill_table(self, data):
        """按检测结果重建表格。

        Args:
            data: 依赖描述列表（可以带 ``installed`` / ``version`` /
                ``detail``，也可以只有清单本身 —— 那时状态显示「检测中...」）。

        ⚠️ **排序期间必须先关排序再铺数据**：``setSortingEnabled(True)`` 时，
        每 ``setItem``/``setCellWidget`` 一次都可能触发重排，行号会在铺到一半时
        变掉，按钮就挂到别的行上去了（Qt 官方文档明确要求这时先关后开）。
        """
        self._buttons = {}
        table = self.table
        was_sorting = table.isSortingEnabled()
        table.setSortingEnabled(False)  # ⚠️ 见 docstring：否则行号会在铺表途中变掉
        try:
            table.clearSpans()  # setRowCount(0) 不会清 span，必须显式清
            table.setRowCount(len(data))

            for i_row, dep in enumerate(data):
                package = dep.get('package', '')
                installed = dep.get('installed', None)
                version = dep.get('version', None)
                detail = dep.get('detail', '') or ''
                note = dep.get('note', '') or ''

                name = dep.get('name') or '-'
                group = dep.get('group', '')

                # ⚠️ 每一格都带 tooltip：窄窗口下列会被截断，提示是唯一的全文出口。
                table.setItem(i_row, 0, self._make_item(
                    0, package, tooltip=detail or package))
                table.setItem(i_row, 1, self._make_item(1, name, tooltip=name))
                table.setItem(i_row, 2, self._make_item(
                    2, group, sort_value=_GROUP_RANK.get(group, 9)))

                if installed is None:
                    text, color = '检测中...', None
                elif installed:
                    text, color = '已安装', COLOR_OK
                else:
                    text = '未安装'
                    color = (COLOR_MISSING if group == '必需'
                             else COLOR_OPTIONAL)
                cell_state = self._make_item(
                    3, text, sort_value=_STATE_RANK.get(text, 9),
                    tooltip=detail)
                if color is not None:
                    cell_state.setForeground(QtGui.QColor(color))
                table.setItem(i_row, 3, cell_state)

                table.setItem(i_row, 4, self._make_item(
                    4, version or '-', tooltip=version or ''))

                # ★ 「备注」列：一句话说清这个包在 zmlx 里干什么。
                table.setItem(i_row, 5, self._make_item(
                    5, note or '-', tooltip=note or '（没有说明）'))

                if installed is False:  # 未安装 → 给一个安装按钮
                    button = QtWidgets.QPushButton('安装', table)
                    button.setToolTip(f'在后台线程里安装 {package}')
                    button.clicked.connect(
                        lambda checked=False, pkg=package: self.start_install(pkg))
                    table.setCellWidget(i_row, 6, button)
                    self._buttons[package] = button
                else:
                    # ⚠️ 必须显式清空：重建表格时 setRowCount 不会移除已有的
                    #    cellWidget，残留的旧按钮会挂到别的行上去。
                    table.removeCellWidget(i_row, 6)
        finally:
            table.setSortingEnabled(was_sorting)

        # ⚠️ 铺完再分一次列宽：构造时 viewport 往往还没算出真实宽度，
        #    只靠 resizeEvent 的话首次显示会落在默认列宽上。
        self._layout_columns()

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
        """更新工具条上的状态文字。

        ⚠️ 同时写进 tooltip：状态标签允许被压窄（为了不撑大上一级控件），
        窗口窄时文字会被截断，完整内容靠悬停看。
        """
        self.status_label.setText(text)
        self.status_label.setToolTip(text)

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
        # ⚠️ 装到控制台，不是本控件：安装耗时可能几分钟，用户要能同时看别的页面。
        #    `>>` 去控制台看完整输出（pi p 的原色也会保留）。
        print(f'{ANSI_INFO}===== 开始安装 {len(dep_list)} 个包 '
              f'({time.strftime("%Y-%m-%d %H:%M:%S")}) ====={ANSI_RESET}')
        print(f'{ANSI_DIM}    安装过程的完整输出在「控制台」标签页里。{ANSI_RESET}')

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
        thread.sig_done.connect(self._on_install_done)
        thread.finished.connect(self._on_install_finished)
        _keep(thread)
        self._install_thread = thread
        thread.start()

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
        print(f'{ANSI_INFO}===== 安装结束，重新检测依赖 ... ====={ANSI_RESET}')
        self.start_check()

    # ------------------------------------------------------------------ 其它

    def contextMenuEvent(self, event):
        """右键菜单：重新检测 / 安装缺失 / 复制依赖清单。"""
        menu = QtWidgets.QMenu(self)
        menu.addAction('重新检测', lambda: self.refresh(force=True))
        menu.addAction('安装缺失的必需依赖', self.install_missing_required)
        menu.addSeparator()
        menu.addAction('复制依赖清单', self._copy_list)
        menu.popup(event.globalPos())

    def _copy_list(self):
        """把当前表格内容复制到剪贴板（纯文本，方便贴到 Issue 里）。

        ⚠️ 「操作」列是按钮、不是 item，按 :data:`COLUMN_KINDS` 跳过 —— 不要
        写死列号：加一列就会漏掉 / 错位（v1.9.13 加「备注」列时正是这么修的）。
        """
        action_cols = [i for i, kind in enumerate(COLUMN_KINDS) if kind == 'none']
        lines = ['\t'.join(COLUMNS)]
        for i_row in range(self.table.rowCount()):
            words = []
            for i_col in range(self.table.columnCount()):
                if i_col in action_cols:
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
    （⚠️ 2026-11-01 起本插件**默认启用**，所以这两条入口开箱即有。）

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

    ⚠️ 本插件声明了 ``# ** enabled = True``（**默认加载**，2026-11-01 由默认不加载
    改为默认启用）：界面上「设置 → 运行环境」开箱即有。用户仍可在
    「设置 → 插件」里取消勾选「默认加载」把它关掉 —— 启动过滤只看那个选择。
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
