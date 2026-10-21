"""插件的**发现与执行**（名单与状态见 :mod:`zmlx.ui.plugins._registry`）.

本模块只做三件事：

1. **发现**：扫描目录、找出 ``zml_plugin.py`` / ``zml_gui_setup.py``；
2. **执行**：按名单顺序逐个执行插件脚本（:func:`run_setup`）；
3. **临时加载**：:func:`load_now` 当场执行**单个**插件（界面「设置 → 插件」里的按钮），
   并记下「本次运行跑过哪些」以防重复执行（:func:`is_loaded`）。

「有哪些插件、以什么顺序、哪个被禁用」的记录一律放在
:mod:`zmlx.ui.plugins._registry` —— 这里**只读写那份名单**，不另起炉灶。

插件来源
--------

1. **名单**（``zml_plugins``）里登记的所有文件 —— 用户登记的、自动发现的都在这里，
   它是**唯一真相**；
2. **自动发现**（只扫一次，见下）：:func:`zmlx.system.app_data.get_paths` 及
   ``zmlx.scen`` 目录下，**每个目录只找一层子目录**里的标准文件名。新发现的文件会
   并入名单并记上 ``*``，下次启动**不再扫描**；
3. **本包的 ``builtin/`` 子目录**下的 ``.py``（``__init__.py`` 除外）—— 这是「随包分发的
   内置插件」的位置，界面「设置 → 插件」里默认启用的「图片浏览」「样式表」就在那里。

⚠️ **2026-10-19 起内置插件下沉到 ``builtin/``**（此前与机制文件同目录，靠「文件名不以
``_`` 开头」区分）。原判据是隐式的：往 ``plugins/`` 丢任何 ``.py`` 都会被启动时执行；
现在「是不是插件」由**所在目录**回答，``plugins/`` 本身只剩机制（``__init__`` / ``_alg`` /
``_registry``），加内部辅助模块不必再靠下划线约定兜着。

⚠️ 与旧实现的差别：旧实现**每次启动**都扫遍 ``sys.path`` 的全部一级子目录
（实测 360 个目录、14 ms），而结果**不写进任何清单** —— 于是自动发现的插件在
「设置 → 插件」里看不见。现在改为「扫到就并入名单」，一次扫描、之后只读名单。

⚠️ 要**重新扫描**（例如刚往 ``scen/`` 下加了一个插件），调用
:func:`set_files` 时传 ``scan=True``；或在「设置 → 插件」里删掉那条记录。
"""

import ast
import os
import sys

from zmlx.system import app_data, read_text, warn
from zmlx.ui.plugins import _registry
from zmlx.ui.plugins._registry import (
    LEGACY_PLUGIN_NAME, PLUGIN_NAME, add_file, get_priority, is_disabled,
    norm as _norm, remove_file)

# 本模块已经做过「迁移 + 首次自动发现」的标记（进程内一次）
_scanned = False

#: 插件被 ``run_setup`` 执行时，命名空间里的 ``__name__`` 就是**这个值**.
#: 插件文件靠它区分「被插件机制执行」与「被人 ``python xxx.py`` 直接运行」——
#: 两种情况都是「顶层代码」，只有 ``__name__`` 能把它们分开。
#: 典型用法（插件文件末尾）::
#:
#:     if __name__ == '__zml_plugin__':   # 被插件机制执行：只注册
#:         setup_ui()
#:     elif __name__ == '__main__':       # 直接运行：开窗口自测
#:         test_1()
#:
#: ⚠️ **2026-10-19 起 ``__name__`` 不再是 ``'__main__'``**（旧写法是把它设成
#: ``'__main__'`` + 在命名空间里塞一个 ``'__zml_plugin__': True`` 的键）。改动
#: 的理由：一个值就够了，插件不必 import 任何东西、也不必再判断字典的键。
#: 代价：把入口写在 ``if __name__ == '__main__':`` 里的**老插件会静默不注册**，
#: 所以 :func:`_run_plugin` 会对这种文件发一条警告（见 :func:`_warn_legacy_entry`）。
_PLUGIN_FLAG = '__zml_plugin__'

#: :func:`get_meta` 的缓存：``{规范化路径: (mtime, meta)}``.
#: ``is_disabled`` 会在 ``run_setup`` 的循环里逐个调 ``get_meta``，不缓存就要反复
#: 读文件、跑一遍 ``code_config``。用 mtime 做键，改了文件自动失效。
_meta_cache = {}

#: **本次运行里已经成功执行过**的插件：``{规范化路径: None}``。
#:
#: ⚠️ **进程级、不落盘**：它回答的是「这次启动到现在，这段脚本跑过没有」——
#: 不是「用户想不想让它跑」（那是 ``zml_plugins`` 的禁用标记）。两者刻意分开：
#: 临时加载（:func:`load_now`）**不改**任何持久设置，重启后一切照旧。
_loaded = {}

#: 上一次临时加载失败的原因：``{规范化路径: 错误文字}``。
#: 失败**不**写进 :data:`_loaded` —— 用户改好文件后应当能再点一次重试。
_load_errors = {}


def _set_default_enabled_resolver(func):
    """（内部）让 ``_registry`` 能按「插件自报的默认值」判断启用状态.

    ⚠️ 为什么要绕这一道：``_registry`` 是**被 ``_alg`` 导入**的底层模块，它不能
    反过来 ``import _alg``（循环导入）。而「用户没表过态时该不该启用」取决于插件
    文件里的 ``# ** enabled = ...``，那要用 :func:`get_meta` —— 只有本模块有。

    所以反向依赖走**运行时注入**：包 ``__init__`` 在导入完两边之后调本函数把
    :func:`get_meta` 交过去。没注入时 ``_registry`` 按「默认启用」处理 —— 那是
    最保守的退化行为，不会把插件误判成禁用。

    Args:
        func: ``get_meta`` 一类的函数（接路径、返回含 ``enabled`` 的 dict）。
    """
    _registry.set_default_enabled_resolver(func)


def _path(*args):
    """本包目录下的路径."""
    return os.path.join(os.path.dirname(__file__), *args)


#: 内置插件所在的子目录（相对本包）。见 :func:`_package_files`。
_BUILTIN = 'builtin'


def _builtin_path(*args):
    """``builtin/`` 子目录下的路径（内置插件都放这里）."""
    return _path(_BUILTIN, *args)


def _package_files():
    """``builtin/`` 目录里随包分发的内置插件.

    规则：**目录即语义** —— ``builtin/`` 下的 ``.py``（``__init__.py`` 除外）**一律**
    是插件。不再需要任何文件名约定。

    ⚠️ 早先的写法是「本包目录下的 ``.py``、不以 ``_`` 开头即插件」，那是一条**隐式**
    判据：往 ``plugins/`` 放一个临时脚本 / 实验文件 / 单测，它就会在每次启动时被
    ``exec`` 执行，而作者以为自己只是在旁边放了个文件。改成「内部实现在上一层、
    插件在本层」之后，放错位置的代价从「静默执行」降到「不会被执行」。

    ⚠️ 因此**不要**往 ``builtin/`` 放工具模块：它会被当成插件。工具放上一层并以
    ``_`` 开头（``_`` 前缀是「内部实现」的既有约定，与执行判据无关）。

    Returns:
        list[str]: 内置插件的绝对路径（按文件名排序）。
    """
    files = []
    folder = _builtin_path()
    try:
        for name in sorted(os.listdir(folder)):
            if not name.endswith('.py'):
                continue
            if name == '__init__.py':
                continue  # 本目录的包说明，不是插件
            files.append(os.path.join(folder, name))
    except OSError as err:
        warn(f'读取内置插件目录失败：{err}', stacklevel=2)
    return files


class _Folders:
    """自动发现的**搜索范围**：哪些目录值得查、哪些必须排除.

    ⚠️⚠️ **必须排除系统临时目录**（2026-10-18 修的正是一个真问题）：搜索路径来自
    ``app_data.get_paths()``（含 ``self.temp()``）**加上** ``sys.path``，而
    ``sys.path`` 里同样有 ``%TEMP%`` —— 临时目录出现两次。再对它展开一层子目录，
    本机实测得到 **2711 个**临时子目录参与扫描，占全部候选目录的 88%；更糟的是
    任何程序往 ``%TEMP%\\随便什么目录\\zml_plugin.py`` 放个文件，都会被当成插件
    **执行**，并且并入名单**永久留下**（文件删了也还在）。

    临时目录里全是短命文件，**不该**作为插件来源 —— 插件的正常位置是项目目录、
    ``zmlx/scen``、本包目录，或用户显式登记的文件。
    """

    @staticmethod
    def is_temp(folder):
        """这个目录是否位于系统临时目录（或 zmlx 自己的 temp）之下.

        Args:
            folder: 待判断的目录路径。

        Returns:
            bool: 在临时目录里返回 True。
        """
        key = _norm(folder)
        if len(key) == 0:
            return False
        for temp in _Folders.temp_roots():
            root = _norm(temp)
            if len(root) == 0:
                continue
            if key == root or key.startswith(root + os.sep):
                return True
        return False

    @staticmethod
    def temp_roots():
        """要排除的临时目录根（系统 temp + zmlx 自己的 temp）.

        Returns:
            list[str]: 绝对路径，去重后返回。
        """
        import tempfile

        roots = []
        for getter in (tempfile.gettempdir, app_data.temp):
            try:
                roots.append(getter())
            except Exception as err:  # 取不到就不排除那一个
                print(f'取临时目录失败：{err}')
        result = []
        seen = set()
        for root in roots:
            key = _norm(root)
            if len(key) > 0 and key not in seen:
                seen.add(key)
                result.append(root)
        return result

    @staticmethod
    def search():
        """自动发现的搜索范围：各搜索路径 + ``zmlx.scen``，**每个目录只取一层子目录**.

        ⚠️ 与旧实现一致（「查找一层子目录」是既有约定），但**只在首次扫描时做**：
        结果并入名单后就不再重复扫描。临时目录（见 :meth:`is_temp`）在**展开之前**
        就被剔除，免得白白遍历几千个子目录。

        Returns:
            list[str]: 候选目录。
        """
        from zmlx.algs.sys import listdir

        folders = [f for f in app_data.get_paths() if not _Folders.is_temp(f)]
        try:
            from zmlx.scen import get_path as scen_path
            folders.append(scen_path())  # 附加 scen 文件夹
        except Exception:
            pass

        # 只展开**非临时**目录的一层子目录；展开出来的若仍在临时目录里也丢掉
        sub = [f for f in listdir(path=folders, with_file=False, with_dir=True)
               if not _Folders.is_temp(f)]
        return folders + sub


def _discover(folders):
    """在给定目录里找标准插件文件，返回 ``[路径]``（已互相去重）."""
    found = []
    seen = set()
    for folder in folders:
        in_folder = []
        for name in (PLUGIN_NAME, LEGACY_PLUGIN_NAME):
            path = os.path.abspath(os.path.join(folder, name))
            if os.path.isfile(path):
                in_folder.append(path)
        if len(in_folder) > 1:
            warn(
                f'目录下同时存在插件文件 {LEGACY_PLUGIN_NAME} 与 {PLUGIN_NAME}：'
                f'{folder}\n'
                f'两者都会被加载，请删除旧文件 {LEGACY_PLUGIN_NAME}'
                f'（旧名仅作兼容，后续版本将不再支持）。',
                stacklevel=2
            )
        for path in in_folder:
            key = _norm(path)
            if key not in seen:
                seen.add(key)
                found.append(path)
    return found


def _scan_once():
    """首次调用时：迁移旧数据 + 把「尚未进名单的标准插件」自动并入名单.

    ⚠️ 迁移分两种，缺一不可：① 旧实现（``zml_gui_setup_files`` + 浮点 rank）的记录；
    ② **内置插件从 ``plugins/`` 搬到 ``plugins/builtin/`` 之后的路径改写**（见
    :func:`zmlx.ui.plugins._registry.migrate_builtin_paths`）。不做 ② 的话，名单里
    指向旧路径的记录会因为"文件不存在"被跳过，用户曾经手动打开过的彩蛋会**静默**
    退回默认关闭。
    """
    global _scanned
    if _scanned:
        return
    _scanned = True
    try:
        _registry.migrate_legacy()
    except Exception as err:
        print(f'迁移旧插件记录失败：{err}')
    try:
        _registry.migrate_builtin_paths()
    except Exception as err:
        print(f'迁移内置插件路径失败：{err}')
    try:
        known = {_norm(path) for path, _ in _registry.get_entries()}
        discovered = [
            path for path in _discover(_Folders.search() + [_path()])
            if _norm(path) not in known]
        if len(discovered) > 0:
            _registry.merge(discovered, standard=True)
    except Exception as err:
        print(f'自动发现插件失败：{err}')


def _is_builtin(path):
    """这个插件是不是**随包分发的内置插件**（就在 ``builtin/`` 目录里）.

    Args:
        path: 插件文件路径。

    Returns:
        bool: 在 ``zmlx/ui/plugins/builtin/`` 目录里返回 True。
    """
    folder = _norm(os.path.dirname(os.path.abspath(path)))
    return folder == _norm(os.path.abspath(_builtin_path()))


def is_standard(path):
    """这个插件是「**自动**」来的，还是用户用 :func:`add_file` **手动**加进来的.

    「自动」包括两类 —— 它们的共同点是**没人手动加它**：

    1. **内置插件**：随包分发在 ``zmlx/ui/plugins/builtin/`` 目录里（``_is_builtin``）；
    2. **自动发现**：目录扫描找到、并入名单时记了 ``*``（``_registry`` 的标记）。

    只有用户通过 :func:`add_file`（或「设置 → 插件」的「添加」）登记进来的才算
    「手动」。⚠️ 界面据此决定「移除」能不能点：自动来的移了下次扫描/分发时还在，
    手动加的才是真正可移除的。

    Args:
        path: 插件文件路径。

    Returns:
        bool: 自动来的返回 True；手动加的返回 False。
    """
    if _is_builtin(path):
        return True
    return _registry.is_standard(path)


def get_files():
    """返回**全部**插件的路径（含禁用、含文件已不存在的），按执行先后排好.

    ⚠️ **不预先过滤禁用**：要不要执行由调用方按 :func:`is_disabled` 自己判断
    （``run_setup`` 就是这么做的）。这样界面也能直接用同一个列表画出「全部插件」
    —— 否则用户勾掉一个插件后，它就从界面上消失了，再也没法勾回来。

    Returns:
        list[str]: 绝对路径，按「高 → 正常 → 低」分段、段内按名单顺序、
        同段时旧名（``zml_gui_setup.py``）排在最后。
    """
    _scan_once()
    files = [item['path'] for item in _registry.get_state_list()]
    known = {_norm(path) for path in files}

    # 名单之外、但就在包目录里的内置插件（用户还没登记的）
    for path in _package_files():
        key = _norm(path)
        if key not in known:
            known.add(key)
            files.append(path)
    return files


def get_meta(path):
    """读取一个插件脚本自带的**名字 / 描述 / 默认启用状态**（从 ``# **`` 配置里取）.

    插件可以（也应该）在第一行附近写：:

        # ** name = '图片浏览'
        # ** desc = '扫描工作路径下的图片，缩略图相册 + 大图预览'

    彩蛋、依赖可选库、实验性的插件还应当声明自己的默认状态::

        # ** enabled = False     # 用户没表态时**默认不加载**

    解析用的是 :func:`zmlx.algs.code_config`（与 demo 同一套机制：把所有 ``# **``
    行拼起来 ``exec`` 一次）。**全是可选的** —— 没写就用兜底值，不会报错：

    ==========  ==========================================================
    情况         用什么顶上
    ==========  ==========================================================
    没有 name    文件名（``image_browser.py`` → ``image_browser``）
    name 不是串  文件名
    没有 desc    ``''``（界面显示「（无描述）」）
    没有 enabled ``True``（默认加载）
    ==========  ==========================================================

    ⚠️ ``enabled`` 是**默认值**，不是强制开关：用户显式勾选/取消过之后，
    一律以用户的为准（见 :func:`is_disabled`）。

    ⚠️ 这里**只读文本、不执行插件体**：``code_config`` 只 ``exec`` 那些注释行，
    插件本身的代码一行都不跑。所以给一个坏文件调用它也是安全的。

    ⚠️ **结果按 (路径, mtime) 缓存**：``is_disabled`` 会在 ``run_setup`` 的循环里
    逐个调用它，不缓存的话每次都要读一遍文件。

    Args:
        path: 插件文件路径。

    Returns:
        dict: ``{'name': str, 'desc': str, 'enabled': bool}``。
    """
    key = _norm(path)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = None

    cached = _meta_cache.get(key)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        from zmlx.algs import code_config
        cfg = code_config(path=path, encoding='utf-8')
    except Exception as err:  # 配置写坏了不该让整个列表垮掉
        warn(f'读取插件配置失败：{path}（{err}）', stacklevel=2)
        cfg = {}

    name = cfg.get('name', None)
    if not isinstance(name, str) or len(name.strip()) == 0:
        name = stem  # 没写名字就用文件名

    desc = cfg.get('desc', None)
    if not isinstance(desc, str):
        desc = ''

    enabled = cfg.get('enabled', None)
    if not isinstance(enabled, bool):
        enabled = True  # 没写 / 写错 → 默认加载

    meta = {'name': name.strip(), 'desc': desc.strip(), 'enabled': enabled}
    _meta_cache[key] = (mtime, meta)
    return meta


def rescan():
    """重新扫描：把新出现的标准插件（``zml_plugin.py`` 等）并入名单.

    ⚠️ 只在「重置」时用。正常启动只扫一次 —— 名单是唯一真相，扫描结果并入后
    就不再重复扫描（见 :func:`_scan_once`），这也是本包能做到「启动时不遍历
    几百个目录」的原因。
    """
    global _scanned
    _scanned = False
    _scan_once()


def _make_space(path):
    """给一个插件造**它自己的**执行命名空间.

    ⚠️⚠️ **插件一律用独立命名空间，不共用 ``app_data.space``**（2026-10-18 定）：
    插件体里的模块级定义（常量、类、辅助函数）会**原样写进**传给 ``exec`` 的 dict。
    共用全局空间就会**互相覆盖** —— 实测两个游戏的模块级名字**共有 16 个**
    （``BASE_W`` / ``BASE_H`` / ``CAPTION`` / ``FPS`` / ``COL`` / ``EDGE`` /
    ``setup_ui`` / ``test_1`` …），后执行的那个会把前一个的值覆盖掉，先执行的
    那个游戏再开窗口时就拿到错误尺寸。

    **需要 ``app_data.space`` 的插件自己 import 去用**即可（``from zmlx.system
    import app_data; app_data.space[...]``）—— 那是显式的、看得见的依赖，不靠
    执行环境偷偷提供。所以这里**什么都不抄**，只给 ``__name__`` 与 ``__file__``
    两个名字。

    Args:
        path: 插件文件路径。

    Returns:
        dict: 供 ``exec`` 用的独立命名空间。``__name__`` 是
        :data:`_PLUGIN_FLAG`（``'__zml_plugin__'``），插件据此判断
        「我是不是被插件机制执行的」。
    """
    return {
        # ★ 明确告诉插件「你现在是被插件机制执行的」，而不是被人直接
        #   ``python xxx.py`` 跑的。两者都是「顶层代码」，只有 ``__name__``
        #   能把它们分开 —— 插件文件末尾据此决定「只注册」还是「开窗口自测」。
        '__name__': _PLUGIN_FLAG,
        '__file__': path,
    }


def _main_guard(tree):
    """找出模块顶层的 ``if __name__ == '__main__':`` 节点（没有则返回 None）.

    Args:
        tree: :func:`ast.parse` 的结果。

    Returns:
        ast.If | None: 那个 ``if`` 语句节点。
    """
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare):
            continue
        left = test.left
        if not (isinstance(left, ast.Name) and left.id == '__name__'):
            continue
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            continue
        right = test.comparators[0]
        if isinstance(right, ast.Constant) and right.value == '__main__':
            return node
    return None


def _has_top_level_call(tree, skip):
    """模块顶层（除 ``skip`` 这个分支之外、不含函数/类体）有没有**任何调用**.

    判据是「有没有 ``Call`` 节点」，所以 ``setup_ui()``、``gui.add_action(...)``、
    ``x = make(...)`` 都算 —— 只要注册动作会真的执行，就不会被判成老写法。

    Args:
        tree: :func:`ast.parse` 的结果。
        skip: 要跳过的顶层语句（那个 ``__main__`` 分支）。

    Returns:
        bool: 有顶层调用返回 True。
    """
    for node in tree.body:
        if node is skip:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue        # 定义不算执行（装饰器调用也不改变结论）
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                return True
    return False


def _warn_legacy_entry(path, text):
    """对仍把入口写在 ``if __name__ == '__main__':`` 里的老插件发一条警告.

    ⚠️ **为什么要发**：2026-10-19 起插件命名空间的 ``__name__`` 是
    ``'__zml_plugin__'``（不再是 ``'__main__'``）。老写法把**全部注册**放在
    ``if __name__ == '__main__':`` 里（例如 ``gui.execute(main, ...)``），改后
    那段代码**根本不执行**，表现是「插件明明启用了、菜单却没出现」，而且**没有
    任何报错**——只能靠这条警告把它变成可见的问题。

    ⚠️ **判据刻意很窄**（宁可不报，也不误报），要同时满足三条：

    1. 有模块顶层的 ``if __name__ == '__main__':``（:func:`_main_guard`）；
    2. 那个分支**之外**没有任何顶层调用（:func:`_has_top_level_call`）——
       所以「顶层调 ``setup_ui()``、末尾再留个 ``__main__`` 自测」这种**完全
       正确**的写法不会被冤枉；
    3. 全文**一次都没提到** ``'__zml_plugin__'`` —— 提到就说明作者已按新约定迁过
       （用两条独立 ``if`` 写的迁移版本也不会被误报）。

    ⚠️ 源码有语法错误时**不报**（交给 ``exec`` 去抛真正的错误），避免警告掩盖
    更重要的问题。

    Args:
        path: 插件文件路径（只用于警告文字）。
        text: 插件源码（已读入的同一份内容）。
    """
    if _PLUGIN_FLAG in text:
        return
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    guard = _main_guard(tree)
    if guard is None:
        return
    if _has_top_level_call(tree, guard):
        return
    warn(
        f'插件入口写在「if __name__ == \'__main__\':」里，插件机制下不会执行：'
        f'{path}\n'
        f'  · 现在插件执行时 __name__ 是 \'{_PLUGIN_FLAG}\'（2026-10-19 起）。\n'
        f'  · 请把注册代码移到模块顶层（直接调 setup_ui()），或改成：\n'
        f'      if __name__ == \'{_PLUGIN_FLAG}\':\n'
        f'          setup_ui()\n'
        f'      elif __name__ == \'__main__\':\n'
        f'          test_1()',
        stacklevel=2,
    )


def _run_plugin(path):
    """执行一个插件：**每个插件一个独立命名空间**，不碰 ``app_data.space``.

    ⚠️⚠️ **所有插件（外部 ``zml_plugin.py`` 与内置插件）一律独立命名空间，没有
    例外、也没有配置项**（2026-10-18 定）：插件体里的模块级定义（常量、类、
    辅助函数）会原样写进传给 ``exec`` 的那个 dict，若共用一个全局空间就会
    **互相覆盖** —— 实测两个游戏的模块级名字共有 16 个（``BASE_W`` /
    ``BASE_H`` / ``CAPTION`` / ``FPS`` / ``COL`` / ``EDGE`` / ``setup_ui`` /
    ``test_1`` …），后执行的那个会把前一个的值覆盖掉，先执行的那个游戏再开窗口
    时就拿到错误尺寸。

    插件需要什么就**自己 import**：``from zmlx.ui import gui``、``from zmlx.system
    import app_data`` —— 依赖写在代码里、看得见，不由执行环境偷偷提供。所以
    :func:`_make_space` 只给 ``__name__`` / ``__file__`` 两样，
    既不抄 ``app_data.space``，也不提供「配置运行空间」的开关。

    Args:
        path: 插件文件路径。
    """
    text = read_text(path, encoding='utf-8', default=None)
    if text is None:
        raise OSError(f'读不出插件内容（文件不存在或不是 UTF-8）：{path}')
    _warn_legacy_entry(path, text)
    exec(text, _make_space(path))


def is_loaded(path):
    """本次运行里这个插件**是否已经执行过**（启动时执行的也算）.

    ⚠️ 与 :func:`is_disabled` 是两件事：前者是「**实际**跑过没有」（运行时事实），
    后者是「用户**要不要**它跑」（持久设置）。临时加载过的插件仍然可以是「禁用」状态
    —— 禁用只影响**下次启动**。

    Args:
        path: 插件文件路径。

    Returns:
        bool: 本次运行已成功执行过返回 True。
    """
    return _norm(path) in _loaded


def get_load_error(path):
    """读上一次临时加载失败的原因.

    Args:
        path: 插件文件路径。

    Returns:
        str | None: 例如 ``'NameError: ...'``；没失败过、或后来成功了，返回 None。
    """
    return _load_errors.get(_norm(path))


def load_now(path):
    """**立即执行**一个插件脚本（临时加载）：不改名单、不改启用状态、不写盘.

    这就是界面「设置 → 插件」里那一列按钮做的事 —— 想试一个默认不加载的插件，
    不必勾选、不必重启，点一下就看到它的菜单。

    ⚠️ **线程**：本函数在**调用它的线程**里执行，自己**不建线程** —— 怎么安排线程是
    调用方的事。界面上的「临时加载」按钮交给 ``gui.start``（界面的**控制台线程**，
    与启动时的 :func:`run_setup` 同一条通道）。插件体里的 ``gui.add_action`` /
    ``gui.add_func`` 都由 ``gui`` 缓冲区派发到 GUI 线程，所以本函数**不需要**在
    GUI 线程调用，也**没有**任何线程亲和性要求。

    ⚠️ **重复加载有两重保证**：
    ① 本函数用 :data:`_loaded` 拦住第二次调用（直接返回 False，不执行）；
    ② 插件若按约定用了 ``@execute_once(file=__file__)``，即使被别处重复执行，
       注册也只会发生一次。
    第一重是**必需的**：``execute_once`` 只是建议，不是所有插件都用了它 —— 而一个有
    副作用的插件（比如往菜单里加一项）被执行两次，就会真的出现两个菜单项。

    ⚠️ **失败不记入** :data:`_loaded`：报错后用户通常会去改文件，改完要能再点一次。
    失败原因存在 :data:`_load_errors` 里，用 :func:`get_load_error` 取。

    Args:
        path: 插件脚本路径。

    Returns:
        bool: 真的执行了返回 True；文件不存在、或本次运行已经加载过，返回 False。
    """
    key = _norm(path)
    if len(key) == 0 or not os.path.isfile(path):
        _load_errors[key] = f'文件不存在：{path}'
        return False
    if key in _loaded:
        return False
    try:
        # 与 run_setup 同样的处理：先让插件所在目录的**上级**可 import
        folder = os.path.dirname(os.path.dirname(path))
        if folder not in sys.path:
            sys.path.append(folder)
        _run_plugin(path)
    except Exception as err:
        _load_errors[key] = f'{type(err).__name__}: {err}'
        try:
            from zmlx.ui import gui
            gui.add_message(f'path = {path}, error = {err}')
        except Exception:      # 没有界面（headless）：错误已经存在 _load_errors 里
            pass
        return False
    _loaded[key] = None
    _load_errors.pop(key, None)
    return True


def run_setup():
    """依次执行所有**启用**的插件脚本（注册菜单、添加面板等）。

    ⚠️ 「禁用」的语义只有一条：**这段代码不执行**。:func:`get_files` 返回的是
    **全部**插件（含禁用、含已不存在的文件），所以这里自己要跳过两类：

    1. ``is_disabled(path)`` —— 用户关掉了它；
    2. 文件已经不在磁盘上 —— 没什么可执行的（用户可能只是临时挪走）。

    ⚠️ **每个插件都在自己的独立命名空间里执行**（见 :func:`_run_plugin`），
    不会污染 ``app_data.space``、也不会互相覆盖同名常量。

    插件执行后派生的东西（菜单项、后台线程）归插件自己负责，本系统不追踪、也不回收。

    ⚠️⚠️ **本函数处在界面启动的关键路径上，而且是同步执行**：插件顶层代码多花的每一
    毫秒都直接变成用户的等待（用户也不知道是哪个插件拖的）。所以插件的顶层只该做
    「接线」—— 挂菜单（``gui.add_action``）、注册 ``gui`` 命令（``gui.add_func``）、
    注册文件类型；重活一律推迟到用户真正用到时，或放进后台线程。判据与反例见
    ``AGENTS.md`` §0.5。
    """
    from zmlx.ui import gui

    the_logs = []
    for path in get_files():
        if is_disabled(path):
            the_logs.append(f'Skipped (disabled): {path}')
            continue
        if not os.path.isfile(path):
            the_logs.append(f'Skipped (missing): {path}')
            continue
        try:
            # 确保包含插件脚本的包能够被正确 import
            folder = os.path.dirname(os.path.dirname(path))
            if folder not in sys.path:
                sys.path.append(folder)

            the_logs.append(f'Exec File: {path}')
            _run_plugin(path)
            _loaded[_norm(path)] = None  # 记进「本次运行已执行」，供临时加载去重
        except Exception as err:
            the_logs.append(f'Failed: {err}')
            gui.add_message(f'path = {path}, error = {err}')
    app_data.put('gui_setup_logs', the_logs)


def test_1():
    """离线自检：迁移 / 合并 / 排序 / 禁用 / 往返（不联网、不改用户设置之外的状态）."""
    import tempfile

    root = tempfile.mkdtemp()
    made = []
    for name in ('zml_plugin.py', 'zml_gui_setup.py', 'b.py'):
        path = os.path.join(root, name)
        with open(path, 'w', encoding='utf-8') as file:
            file.write('')
        made.append(path)

    original = _registry.get_entries()
    try:
        _registry.set_entries([])
        _registry.merge([made[2]])
        _registry.merge([made[0], made[1]], standard=True)
        assert len(_registry.get_entries()) == 3, _registry.get_entries()

        # 顺序：名单顺序；旧名（兼容名）沉到同段最后，但推荐名**不会**被提前
        order = [os.path.basename(path) for path in _registry.get_files()]
        assert order == ['b.py', 'zml_plugin.py', 'zml_gui_setup.py'], order

        # 禁用：只改标记，不动顺序、不动优先级
        _registry.set_disabled(made[2], True)
        assert [os.path.basename(path) for path in _registry.get_files()] == [
            'zml_plugin.py', 'zml_gui_setup.py']
        assert _registry.get_priority(made[2]) == 'normal'

        # 优先级：high 整段提到最前；档内仍按名单顺序（旧名沉到最后）
        _registry.set_priority(made[1], 'high')
        assert [os.path.basename(path) for path in _registry.get_files()] == [
            'zml_gui_setup.py', 'zml_plugin.py']
        _registry.set_disabled(made[2], False)
        _registry.set_priority(made[2], 'high')
        assert [os.path.basename(path) for path in _registry.get_files()] == [
            'b.py', 'zml_gui_setup.py', 'zml_plugin.py']

        # 增删：add_file 是追加（已在名单里就不动），remove_file 只移出名单
        _registry.set_entries([])
        assert add_file(made[0]) is True
        assert add_file(made[0]) is False  # 重复添加
        assert add_file(made[1]) is True
        assert add_file(made[2]) is True
        assert [os.path.basename(path) for path in _registry.get_files()] == [
            'zml_plugin.py', 'b.py', 'zml_gui_setup.py']  # 旧名沉到最后
        assert remove_file(made[1]) is True
        assert [os.path.basename(path) for path in _registry.get_files()] == [
            'zml_plugin.py', 'b.py']
        assert remove_file(made[1]) is False  # 已经不在名单里

        # get_files 返回**全部**插件（含禁用）；执行时由 is_disabled 自己筛
        _registry.set_disabled(made[0], True)
        files = get_files()
        assert all(isinstance(item, str) for item in files), files
        # 名单里那两个都在（禁用与否都返回），顺序按名单：zml_plugin 后在 b.py 前
        ours = [os.path.basename(path) for path in files
                if os.path.dirname(path) == root]
        assert ours == ['zml_plugin.py', 'b.py'], ours
        assert is_disabled(made[0]) is True
        assert get_priority(made[1]) == 'normal'
        assert _registry.is_standard(made[0]) is False  # 用 add_file 登记的

        # 路径标记往返：带冒号的盘符不会被切坏
        text = 'C:\\a\\b\\zml_plugin.py:*:high:disabled'
        path, flags = _registry._Text.split_path(text)
        assert path == 'C:\\a\\b\\zml_plugin.py', path
        assert flags == ['*', 'high', 'disabled'], flags
        print('test_1 passed.')
    finally:
        _registry.set_entries(original)


if __name__ == '__main__':
    test_1()
