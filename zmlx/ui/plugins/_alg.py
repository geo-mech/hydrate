"""插件的**发现与执行**（名单与状态见 :mod:`zmlx.ui.plugins._registry`）.

本模块只做三件事：

1. **发现**：扫描目录、找出 ``zml_plugin.py`` / ``zml_gui_setup.py``；
2. **执行**：按名单顺序逐个执行插件脚本（:func:`load_all`）；
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

#: 插件被 ``load_all`` 执行时，命名空间里的 ``__name__`` 就是**这个值**.
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
#: ``is_disabled`` 会在 ``load_all`` 的循环里逐个调 ``get_meta``，不缓存就要反复
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

        ⚠️ **2026-10-22 起 ``zmlx/scen`` 纳入自动发现**（它本来**不在**
        ``app_data.get_paths()`` 里，只有这一处会查）。于是随包分发的自包含插件可以
        整个住在 ``scen/<包>/`` 下（``scen/easter_eggs/zml_plugin.py``），入口与它
        import 的实现模块同处一包。

        ⚠️ **只取 ``scen`` 的「一层子目录」**，与其它搜索路径完全一致 —— 因此
        ``scen/<包>/zml_plugin.py`` 是**唯一**的自包含形态。不要往 ``scen/<包>/<子包>/
        zml_plugin.py`` 嵌套：那样「``scen/<包>`` 自己算不算插件」就没有答案了
        （插件机制按目录判语义，一个目录里只能有一个 ``zml_plugin.py``）。

        Returns:
            list[str]: 候选目录。
        """
        from zmlx.algs.sys import listdir

        folders = [f for f in app_data.get_paths() if not _Folders.is_temp(f)]
        try:
            from zmlx.scen import get_path as scen_path
            scen = scen_path()
            if scen not in folders:
                folders.append(scen)  # 附加 scen 文件夹
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
    （``load_all`` 就是这么做的）。这样界面也能直接用同一个列表画出「全部插件」
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

    ⚠️ 另外两个键**只读不生效**（2026-10-23 加，为将来的插件依赖预留）：::

        # ** inner_name = 'image_browser'
        # ** dependencies = ['viewers', 'data_editor']

    - ``inner_name``：内部标识（``str | None``）。**没写就是 ``None``，不回落到文件名**
      —— 一旦回落，等于每个插件都有标识符，「没写」与「写了」就分不清了。
    - ``dependencies``：依赖的 ``inner_name`` 列表（``list[str] | None``）。
      **缺省是 ``None`` 而不是 ``[]``**：``None`` = 没声明，``[]`` = 明确声明「无依赖」。
    - 两者**当前完全不起作用**：不排序、不校验存在性与唯一性、界面也不显示。
      写错只会得到一条警告，不会被丢掉整个配置（宽松校验，见 `_parse_dependencies`）。

    ⚠️ ``enabled`` 的含义是「**默认是否自动加载**」，不是「能否执行」、也不是强制
    开关：① 用户显式勾选/取消过之后一律以用户的为准（见 :func:`is_disabled`）；
    ② 即使被判为「禁用」，:func:`load_now`（临时加载）与「被其它插件作为依赖拉起」
    都**照样执行**它 —— 「禁用」过滤的只有 :func:`load_all` 那一层（2026-10-24 定）。

    ⚠️ 这里**只读文本、不执行插件体**：``code_config`` 只 ``exec`` 那些注释行，
    插件本身的代码一行都不跑。所以给一个坏文件调用它也是安全的。

    ⚠️ **结果按 (路径, mtime) 缓存**：``is_disabled`` 会在 ``load_all`` 的循环里
    逐个调用它，不缓存的话每次都要读一遍文件。

    Args:
        path: 插件文件路径。

    Returns:
        dict: ``{'name': str, 'desc': str, 'enabled': bool,
        'inner_name': str | None, 'dependencies': list[str] | None}``。
        后两个键只读不生效（见上）。
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

    inner_name = _parse_inner_name(cfg.get('inner_name', None), path)
    dependencies = _parse_dependencies(cfg.get('dependencies', None), path)

    meta = {'name': name.strip(), 'desc': desc.strip(), 'enabled': enabled,
            'inner_name': inner_name, 'dependencies': dependencies}
    _meta_cache[key] = (mtime, meta)
    return meta


def _parse_inner_name(value, path):
    """把 ``# ** inner_name`` 解析成 ``str | None``（**不做任何推断**）.

    ⚠️ 没写就是 ``None``，**不要**回落到文件名 —— 见 PLAN ``T-20261023-08``：
    一旦回落，等于每个插件都「有了标识符」，「没写」与「写了」就分不清了。
    ``name`` 那条「没写用文件名」的规则**不要**照搬到这里。

    Args:
        value: ``code_config`` 里读到的原始值。
        path: 插件路径（只用于警告文字）。

    Returns:
        str | None: 去首尾空白的名字；没写 / 写错 / 全空白时为 ``None``。
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if len(value) > 0 else None
    warn(f'插件 {path} 的 inner_name 应为字符串，已忽略：{value!r}', stacklevel=3)
    return None


def _parse_dependencies(value, path):
    """把 ``# ** dependencies`` 解析成 ``list[str] | None``（宽松校验，绝不抛异常）.

    ⚠️ 缺省是 ``None`` 而**不是** ``[]``：``None`` = 没声明，``[]`` = 明确声明「无依赖」
    —— 将来做依赖解析时两者语义不同。

    ⚠️ 校验刻意宽松：这只是**默认不起作用**的预留字段，一个写坏的 ``dependencies``
    不该让整个插件列表垮掉（与「配置写坏了也用兜底值」的既有行为一致）。

    ⚠️ **不校验**：不查重、不查依赖指向的插件是否存在 —— 那是将来真正启用依赖功能时的事。

    Args:
        value: ``code_config`` 里读到的原始值。
        path: 插件路径（只用于警告文字）。

    Returns:
        list[str] | None: 去空白、丢掉空串与坏项之后的列表；没写 / 类型不对时为 ``None``。
    """
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        warn(f'插件 {path} 的 dependencies 应为列表，已忽略：{value!r}', stacklevel=3)
        return None
    result = []
    dropped = []
    for item in value:
        if isinstance(item, str) and len(item.strip()) > 0:
            result.append(item.strip())
        else:
            dropped.append(item)
    if dropped:
        warn(f'插件 {path} 的 dependencies 里有 {len(dropped)} 项不是有效字符串，'
             f'已丢弃：{dropped!r}', stacklevel=3)
    return result


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


def _looks_like_path(text):
    """这个字符串**看起来**是路径吗（用来区分「文件不存在」与「没有这个插件」）.

    ⚠️ 只服务于**错误信息**：传入一个不存在的路径时，用户要看到的是
    「文件不存在：<那个路径>」，而不是「找不到插件」。所以不能只看
    ``os.path.isfile``，得先判断它长得像不像路径。

    Args:
        text: 已去空白的字符串。

    Returns:
        bool: 看起来像路径返回 True。
    """
    if len(text) == 0:
        return False
    if text.endswith('.py') or text.endswith('.pyw'):
        return True
    if os.path.isabs(text):
        return True
    return (os.sep in text) or ('/' in text)


def _find_by_inner_name(name):
    """按 ``inner_name`` 在名单里找插件路径（**精确相等**，取第一个）.

    ⚠️ 遍历顺序**固定为** :func:`get_files` 的顺序（名单顺序 + 优先级分段）——
    不要另起一套，否则同一个名字在不同调用点可能命中不同插件。

    ⚠️ 不做大小写折叠、不做前缀/模糊匹配、不做 stem 推断。

    Args:
        name: 已去空白的 ``inner_name``。

    Returns:
        str | None: 第一个匹配项的路径；没有匹配返回 None。
    """
    hits = []
    for path in get_files():
        try:
            inner = get_meta(path).get('inner_name', None)
        except Exception:      # 读不出配置的插件不该让查找整体失败
            continue
        if isinstance(inner, str) and inner == name:
            hits.append(path)
    if len(hits) == 0:
        return None
    if len(hits) > 1:
        warn(f'inner_name {name!r} 命中 {len(hits)} 个插件，取第一个：{hits[0]}\n'
             f'其余：{hits[1:]}', stacklevel=3)
    return hits[0]


def _resolve(target):
    """把「**路径或 `inner_name`**」统一解析成路径.

    判定顺序**固定**（不能反过来）：
    1. 是一个**存在的文件** → 当路径，原样返回；
    2. 否则在名单里找 ``inner_name == target`` → 返回那个插件的路径；
    3. 都不是：看起来像路径（有分隔符 / ``.py`` 结尾 / 绝对路径）→ 原样返回，
       交给调用处报「文件不存在」；否则返回 ``None``（调用处报「找不到插件」）。

    ⚠️ 顺序的理由：路径是**可验证的**（文件在不在），名字是**自称的**。
    这样**现有按路径调用的行为一个字节都不变** —— 凡是今天能用的路径都走第 1 步。

    Args:
        target: 路径或 ``inner_name``。

    Returns:
        str | None: 解析出的路径；无法识别时为 None。
    """
    if not isinstance(target, str):
        return None
    text = target.strip()
    if len(text) == 0:
        return None
    if os.path.isfile(text):
        return text
    hit = _find_by_inner_name(text)
    if hit is not None:
        return hit
    return text if _looks_like_path(text) else None


def is_loaded(path):
    """本次运行里这个插件**是否已经执行过**（启动时执行的也算）.

    ⚠️ 与 :func:`is_disabled` 是两件事：前者是「**实际**跑过没有」（运行时事实），
    后者是「用户**要不要**它跑」（持久设置）。临时加载过的插件仍然可以是「禁用」状态
    —— 禁用只影响**下次启动**。

    ⚠️ 参数接受「**路径或 `inner_name`**」（2026-10-24）：先经 :func:`_resolve`
    解析成路径再查表 —— 因为 :data:`_loaded` 的键**永远只能是规范化路径**，
    否则同一个插件会有「路径」与「名字」两把钥匙，「只加载一次」立刻失效。

    Args:
        path: 插件文件路径，或插件的 ``inner_name``。

    Returns:
        bool: 本次运行已成功执行过返回 True；名字解析不出来也返回 False。
    """
    target = _resolve(path)
    if target is None:
        return False
    return _norm(target) in _loaded


def get_load_error(path):
    """读上一次临时加载失败的原因.

    ⚠️ 参数同样接受「**路径或 `inner_name`**」（2026-10-24）：先解析成路径再查
    :data:`_load_errors` —— 键永远只是规范化路径，不能拿名字当键。

    Args:
        path: 插件文件路径，或插件的 ``inner_name``。

    Returns:
        str | None: 例如 ``'NameError: ...'``；没失败过、或后来成功了，返回 None。
    """
    target = _resolve(path)
    if target is None:
        # 解析不出来时，``load_now`` 把错误记在「输入原样规范化」的键下 —— 这里要
        # 用**同一个键**取回来，否则按名字查失败原因永远是 None（2026-10-24 实测踩到）。
        return _load_errors.get(_norm(path) if isinstance(path, str) else '')
    return _load_errors.get(_norm(target))


def load_one(path, *, ignore_disabled=True):
    """执行**一个**插件（:func:`load_now` 与 :func:`load_all` 共用的那一段）.

    ⚠️ **成功才写** :data:`_loaded`，失败才写 :data:`_load_errors` —— 标记时机是
    「执行成功之后」，提前标记会让失败的插件被误认为已执行（依赖递归也靠这个标记截断环）。

    Args:
        path: 插件脚本路径（**必须是真实路径**，不解析名字；解析由调用方做）。
        ignore_disabled: True（默认）不管禁用状态；False 则已禁用就不执行。

    Returns:
        bool: 真的执行了返回 True；文件不存在 / 已经加载过 / （严格模式下）被禁用 /
        抛异常，都返回 False。
    """
    key = _norm(path)
    if len(key) == 0 or not os.path.isfile(path):
        _load_errors[key] = f'文件不存在：{path}'
        return False
    if key in _loaded:
        return False
    if not ignore_disabled and is_disabled(path):
        # ⚠️ 不写进 _load_errors：这不是「加载失败」，而是「按设置不该执行」。
        #    用户之后取消禁用、再点一次，仍应当能正常加载。
        return False
    try:
        # 先让插件所在目录的**上级**可 import
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


def load_with_deps(path, *, ignore_disabled=True):
    """执行一个插件，**成功之后**再递归执行它声明的 ``dependencies``.

    顺序**不可调换**（PLAN ``T-20261023-10``）::

        ① 执行自己 → ② 成功了才标记（:func:`load_one` 内部做）
        → ③ 再逐个递归拉依赖 → ④ 自己失败就**不标记、不碰依赖**

    ⚠️ 这个顺序**天然处理循环依赖**：A ⇄ B 时，A 执行成功即被标记，递归到 B、B 成功
    也被标记，再回到 A 时 ``A 已在 _loaded`` → 停。反过来（先拉依赖再执行自己）会无限递归。

    ⚠️ **依赖一律不看「禁用」**：「禁用」的语义只有一条 —— **启动时不自动加载它**。
    而依赖不是「自动加载」的，是被主插件的关系**拉起来**的。所以递归这一层固定
    ``ignore_disabled=True``；只有**最外层**（用户/启动循环指定的那个）才看调用方传的
    ``ignore_disabled``。

    ⚠️ **依赖失败只警告，不影响主插件的返回值**：主插件已经执行成功，没法回滚 ——
    这是「先执行自己」带来的必然取舍。

    Args:
        path: 插件脚本路径（真实路径）。
        ignore_disabled: 只作用于**最外层**；递归时一律 True（见上）。

    Returns:
        bool: 主插件是否成功执行。
    """
    if not load_one(path, ignore_disabled=ignore_disabled):
        return False

    try:
        deps = get_meta(path).get('dependencies', None) or []
    except Exception as err:
        warn(f'读插件依赖失败：{path}（{err}）', stacklevel=2)
        deps = []

    for name in deps:
        target = _resolve(name)
        if target is None:
            warn(f'插件 {path} 依赖的 {name!r} 找不到（既不是存在的文件，'
                 f'也没有同名 inner_name），已跳过', stacklevel=2)
            continue
        if _norm(target) in _loaded:
            # ⚠️ **已在本次运行执行过就直接跳过，不要当成失败**：循环依赖（A ⇄ B）
            #    正是靠这一步自然结束的 —— 若在这里调 load_with_deps，它会因为
            #    load_one 返回 False（已加载）而**误报**一条「依赖加载失败」警告
            #    （2026-10-24 实测踩到）。
            continue
        if not load_with_deps(target, ignore_disabled=True):
            reason = _load_errors.get(_norm(target), '未知原因')
            warn(f'插件 {path} 依赖的 {name!r} 加载失败：{reason}', stacklevel=2)
    return True


def load_now(path, *, ignore_disabled=True):
    """**立即执行**一个插件脚本（临时加载）：不改名单、不改启用状态、不写盘.

    这就是界面「设置 → 插件」里那一列按钮做的事 —— 想试一个默认不加载的插件，
    不必勾选、不必重启，点一下就看到它的菜单。

    ⚠️⚠️ **默认不受「禁用」限制**（2026-10-22 定稿，推翻同日的上一次改动）：
    两个入口的语义**不同**，把它们绑在一起会**让这个按钮彻底没用**：

    ==============  ==========================================================
    入口               「启用 / 禁用」意味着什么
    ==============  ==========================================================
    ``load_all``    **持久设置**：下次启动跑不跑 —— 必须尊重它
    ``load_now``     **用户当场要求试一下** —— 与设置无关，也不改设置
    ==============  ==========================================================

    推论很致命：**启用的插件启动时早就执行过**（``is_loaded`` 为真、按钮显示
    「已加载」且点不动），所以**唯一能点「加载」的恰好是禁用的插件**。于是
    「临时加载尊重禁用」= 按钮对谁都无效（2026-10-22 实测：17 项里 14 项禁用，
    点谁都没反应，且不报错）。

    现在恢复原语义：默认执行，**不写任何设置**，重启后仍按「默认加载」勾选决定
    （「设置 → 插件」第一列，2026-10-25 由「启用」改名）。
    需要严格模式（「禁用的就别跑」）时，由调用方显式传 ``ignore_disabled=False``。

    ⚠️ **线程**：本函数在**调用它的线程**里执行，自己**不建线程** —— 怎么安排线程是
    调用方的事。界面上的「临时加载」按钮交给 ``gui.start``（界面的**控制台线程**，
    与启动时的 :func:`load_all` 同一条通道）。插件体里的 ``gui.add_action`` /
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

    ⚠️ **被依赖拉起的插件即使「禁用」也会执行**（2026-10-24）：本函数成功后会把
    它声明的 ``dependencies`` 递归拉起来，而递归那一层**一律不看禁用** ——
    禁用只表示「启动时不自动加载它」，而被拉起的插件不是被自动加载的。
    详见 :func:`load_with_deps`。

    Args:
        path: 插件脚本路径，**或插件的 ``inner_name``**（2026-10-24 起）。名字按
            :func:`_resolve` 的规则解析成路径；解析不出来才报错。
        ignore_disabled: True（默认）= 不管禁用状态都执行 —— 这正是「临时加载」的
            语义。传 False 则退回「已禁用就不执行」

    Returns:
        bool: 真的执行了返回 True；文件不存在、名字解析不出来、本次运行已经加载过
        （或在严格模式下被禁用），返回 False。
    """
    target = _resolve(path)
    if target is None:
        # ⚠️ 键只能是**规范化路径**；解析不出来时用输入原样当键（只为让调用方
        #    按同样的输入把错误取回去，绝不会和某个真实路径撞上）。
        _load_errors[_norm(path) if isinstance(path, str) else ''] = (
            f'找不到插件：{path!r}（既不是存在的文件，也没有同名 inner_name）')
        return False
    # ⚠️ 走 load_with_deps：主插件成功之后会把它声明的 dependencies 递归拉起来
    #    （2026-10-24 起，见 PLAN T-20261023-10）。
    return load_with_deps(target, ignore_disabled=ignore_disabled)


def load_all():
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

    ⚠️ **每个插件走 :func:`load_with_deps`**（2026-10-24 起）：主插件成功后会递归
    拉起它声明的 ``dependencies``。由此产生两个必须知道的行为：

    1. **被依赖拉起的插件不看禁用**：「禁用」只表示「启动时不自动加载它」，而依赖是
       被主插件的关系拉起来的，不是自动加载的 ⇒ 它会被执行。这是本轮**唯一**的行为变化。
    2. **循环里要跳过已加载的**：B 若已被 A 的依赖递归拉起，等循环走到 B 时必须
       什么都不做（否则菜单挂两次）。
    """
    the_logs = []
    for path in get_files():
        # ⚠️ **先看「已加载」，再看「禁用」**：被依赖递归拉起的插件可能同时也是禁用的，
        #    这时它确实执行过了，日志要记 `Exec File:` —— 放到禁用判断之后就会被
        #    错记成「跳过（禁用）」，界面状态列跟着显示错（2026-10-24 实测踩到）。
        if _norm(path) in _loaded:
            the_logs.append(f'Exec File: {path}')
            continue
        if is_disabled(path):
            the_logs.append(f'Skipped (disabled): {path}')
            continue
        if not os.path.isfile(path):
            the_logs.append(f'Skipped (missing): {path}')
            continue
        if load_with_deps(path):
            the_logs.append(f'Exec File: {path}')
        else:
            error = _load_errors.get(_norm(path), '未知原因')
            the_logs.append(f'Failed: {error}')
    app_data.put('gui_setup_logs', the_logs)


def run_setup():
    """旧名（**已弃用**）：请改用 :func:`load_all`.

    ⚠️ 本转发层只做**单向转发**，将于 **2027-10-23** 删除。

    保留它有两个理由：① 外部工作区里的脚本可能还在调它；② 每次调用都留一条
    ``DeprecationWarning``（经 :func:`zmlx.system.warn`，于是也进「今天用到过没有」
    的日志），这样才能判断**到底还有没有人在用**，而不是凭感觉删。

    ⚠️ **不要在垫片里重复实现一遍逻辑** —— 复制会带来两份 ``_loaded`` 记账，
    「只加载一次」立刻失效。这里只有转发。

    Returns:
        None
    """
    warn('``plugins.run_setup`` 已改名为 ``plugins.load_all``；本转发层将于'
         ' 2027-10-23 删除。', DeprecationWarning, stacklevel=2)
    return load_all()


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
