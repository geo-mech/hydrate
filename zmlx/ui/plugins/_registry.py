"""插件状态的唯一真相：**名单 + 优先级 + 禁用**（三个概念、三个变量）.

本模块只管「一个插件现在是什么状态」，**不负责**扫描目录、执行脚本 —— 那是
:mod:`zmlx.ui.plugins._alg` 的事。

三个概念，各管一件事
--------------------

==============  ==============================  ===========================================
概念             变量（三个独立的环境变量）       回答什么问题
==============  ==============================  ===========================================
**名单 / 顺序**  ``zml_plugins``                有哪些插件、按什么顺序显示与执行
**优先级**       ``zml_plugin_priority``        谁先执行（让高优先级**整体**插到前面）
**禁用**         ``zml_plugin_disabled``        哪个插件**不执行**（默认全部启用）
==============  ==============================  ===========================================

⚠️⚠️ **三者刻意不合并**。旧实现用「浮点 rank」一个变量同时表达顺序、纳入与排除
（排除 = rank 置成 1e20），于是「排最后」和「不要它」在数据上长得一模一样，用户
拖动一次还要给**每个**文件写一条环境变量。现在：

- **拖动顺序只改 ``zml_plugins`` 一个键**（一次写盘），不碰优先级、不碰禁用；
- **习惯用法**：优先级与禁用存在 ``zml_plugins`` 的标记里；'zml_plugin_priority' /
  ``zml_plugin_disabled`` 两个键只为**兼容老记录**保留（迁移时读一次，之后不写）；
- 三件事各自独立可解释，谁也不会被另一个顺手改写。

⚠️ 优先级**不参与列表排序**：列表顺序永远 = 名单顺序。执行时按「高 → 正常 → 低」
分三段跑，**段内仍按名单顺序** —— 「拖动」永远精确，「插队」是另一件显式的事
（与线程调度里「调线程优先级不改变它被创建的先后」同一个道理）。

``zml_plugins`` 的格式
----------------------

一条记录一个插件，记录之间用 ``;`` 分隔，记录内的字段用 ``:`` 分隔::

    <绝对路径>:*:high:disabled;<另一个绝对路径>

- 第 1 段是**绝对路径**（Windows 盘符 ``C:`` 会让朴素的分割出错，解析时专门处理）；
- 后续段是可以**任意顺序**出现的标记：

  ========================  ==================================================
  标记                       含义
  ========================  ==================================================
  ``*``                     **标准文件名**（``zml_plugin.py`` 或兼容名
                            ``zml_gui_setup.py``）= 由自动发现并入的那份记录
  ``high`` / ``low``        该插件的优先级（``normal`` 是缺省，不写）
  ``disabled``              **不启用**（``enabled`` 是缺省，不写）
  ========================  ==================================================

⚠️ **带 ``*`` 的记录只显示、不重新扫描**。作用有二：① 让自动发现到的插件在
「设置 → 插件」里**看得见**（旧实现里它们根本不在清单中，直到用户拖一下才突然
冒出来）；② 首次并入时一并记录，下次启动不再重复扫描那些目录。要「重新扫描并
发现新文件」，用 :func:`zmlx.ui.plugins.rescan`。

⚠️ ``*`` 是**陈旧标记**：文件被删掉后记录仍在（用户可能只是临时挪走）。显示层
应当把不存在的文件标成「文件不存在」，而**不要**因此改变执行顺序 —— 见
:func:`get_state_list`。

旧数据迁移
----------

本模块的键名**全新**，老版本仍能读老键，新版本也不与老键互相踩。首次读取名单时
（``plugins._alg.get_files`` 里，且只做一次）会：

1. 把旧键 ``zml_gui_setup_files`` 里登记的文件并入名单（保持原顺序，追加在后面）；
2. 把旧 rank 恰好等于 ``1e20`` 的文件标记为 ``disabled``（旧实现里那是「忽略」
   的唯一表达）；其余旧 rank（1.0 ~ 1e10 那一档表达的是**顺序**）**不搬** ——
   顺序已由名单本身表达，搬过来只会多一份互相矛盾的数据；
3. 清空旧键：老版本再启动时看到「没有额外登记」，与迁移后的语义一致。

⚠️ **内置插件路径改写**（2026-10-19 起，见 :func:`migrate_builtin_paths`）：内置插件
从 ``plugins/`` 下沉到 ``plugins/builtin/``，名单里的**绝对路径**必须跟着改，
否则用户的启用选择会**静默丢失**（旧记录被当成「文件缺失」跳过，新路径没有任何
记录 ⇒ 回到插件自报的默认值）。

⚠️ **幂等**：清空空键之后再次进入时没有任何可搬的东西，什么也不做。
"""

import os

from zmlx.system import app_data, get_hash, warn

# 「所有插件」的名单（有序、唯一真相）
_KEY_FILES = 'zml_plugins'

# 兼容键：老记录的「例外集合」。**只读不写**（新数据一律写进名单标记）
_KEY_PRIORITY = 'zml_plugin_priority'
_KEY_DISABLED = 'zml_plugin_disabled'

# 旧实现的登记表与旧 rank 的「排除」哨兵值。迁移时读一次，之后不再写
_LEGACY_FILES_KEY = 'zml_gui_setup_files'
_LEGACY_EXCLUDED_RANK = 1.0e20
_LEGACY_RANK_PREFIX = 'rank: '

# 标准插件文件名。⚠️ 与 ``_alg`` 里的两个常量**同源**：这里定义、那边 import，
# 免得两处各写一份字符串以后对不上。
PLUGIN_NAME = 'zml_plugin.py'
LEGACY_PLUGIN_NAME = 'zml_gui_setup.py'

# 优先级取值，按**执行先后**排（列表顺序不受它影响）
PRIORITIES = ('high', 'normal', 'low')
_DEFAULT_PRIORITY = 'normal'


def norm(path):
    """把路径规范化成「名单里比较用」的形式（绝对 + 大小写按平台归一）.

    ⚠️ **不解析符号链接**（``realpath``）：Windows 上它给路径加上 ``//?/`` 前缀
    （反斜杠版本见 :func:`os.path.realpath` 的文档），与用户手写、或写进环境变量里
    的路径对不上。

    Args:
        path: 任意路径（``str`` / ``os.PathLike``）。

    Returns:
        str: 规范化后的路径；非法输入返回空串。
    """
    if path is None:
        return ''
    try:
        return os.path.normcase(os.path.abspath(os.fspath(path)))
    except (TypeError, ValueError, OSError):
        return ''


def plugin_name_rank(path):
    """**只把旧名（兼容名）沉到同段的最后**，其余一律 0.

    ⚠️ 早先的写法是「``zml_plugin.py`` 得 0、其它得 1」，那会把推荐的插件名
    **提到普通文件之前** —— 于是用户在「设置 → 插件」里拖出来的顺序被文件名
    悄悄改写（实测：名单 ``[b.py, zml_plugin.py]`` 执行成 ``[zml_plugin.py, b.py]``）。
    「推荐名优先」的本意只是「同一目录下新旧两个文件名并存时优先新名」，不是
    「凡是新名都插队」。故这里只惩罚旧名。

    Args:
        path: 插件文件路径。

    Returns:
        int: 旧名 ``zml_gui_setup.py`` 返回 ``1``，其余（含 ``zml_plugin.py``）返回 ``0``。
    """
    return 1 if os.path.basename(path) == LEGACY_PLUGIN_NAME else 0


class _Text:
    """``;`` / ``:`` 分隔文本的读写（私有命名空间类：模块级不散落工具函数）."""

    @staticmethod
    def split_items(text):
        """把 ``;`` 分隔的多条记录切成列表，去掉空项与首尾空白."""
        if not isinstance(text, str):
            return []
        return [item.strip() for item in text.split(';') if len(item.strip()) > 0]

    @staticmethod
    def split_path(text):
        """把「路径 + 若干标记」切成 ``(path, flags)``.

        ⚠️ 不能用朴素 ``split(':')``：Windows 盘符（如 ``C:``）本身带冒号。做法是先用
        ``os.path.splitdrive`` 把盘符摘下，剩下的部分再按 ``:`` 分，最后拼回去。

        Args:
            text: 名单里的一条记录。

        Returns:
            (str, list): ``(路径原文, 标记列表小写)``。
        """
        drive, rest = os.path.splitdrive(text)
        parts = rest.split(':')
        flags = [part.strip().lower() for part in parts[1:]]
        return (drive + parts[0]).strip(), [
            flag for flag in flags if len(flag) > 0]

    @staticmethod
    def join_path(path, flags):
        """``(路径, 标记)`` -> 名单里的一条记录."""
        flags = [flag for flag in flags if len(flag) > 0]
        return ':'.join([path] + flags)


class _Flags:
    """名单标记的解析与改写（``*`` / ``high`` / ``low`` / ``disabled``）."""

    STANDARD = '*'
    DISABLED = 'disabled'
    #: 用户**显式打开**过的标记（插件自己声明 ``enabled = False`` 时才需要它）。
    #: 没有这两个标记之一 = 用户没表过态 → 用插件自报的默认值。
    ENABLED = 'enabled'

    @staticmethod
    def parse_priority(flags):
        """从标记里取优先级（没有就返回 ``normal``）."""
        for value in PRIORITIES:
            if value in flags:
                return value
        return _DEFAULT_PRIORITY

    @staticmethod
    def with_priority(flags, value):
        """把 ``flags`` 里的优先级换成 ``value``（``normal`` 时删掉）."""
        result = [flag for flag in flags if flag not in PRIORITIES]
        if value != _DEFAULT_PRIORITY:
            result.append(value)
        return result

    @staticmethod
    def with_disabled(flags, disabled):
        """把「启用状态」的标记设成 ``disabled`` / ``enabled``.

        ⚠️ 这是**三态**里的「用户表态」：调它就意味着「记下用户的明确选择」，
        从此不再看插件自报的默认值。要「恢复默认」请用
        :func:`_Flags.clear_choice`。
        """
        result = [_flag for _flag in flags
                  if _flag not in (_Flags.DISABLED, _Flags.ENABLED)]
        result.append(_Flags.DISABLED if disabled else _Flags.ENABLED)
        return result

    @staticmethod
    def pick(flags, values):
        """按 ``values`` 的顺序，返回 ``flags`` 里第一个命中的标记（没有则 None）."""
        for value in values:
            if value in flags:
                return value
        return None

    @staticmethod
    def merge(first, second):
        """合并两条记录的标记：``first`` 的表态优先，``second`` 只补缺.

        ⚠️ 只在「同一条路径同时存在新旧两条记录」时用到（见
        :func:`migrate_builtin_paths`）：重复记录会让插件被**执行两次**，所以必须
        合并成一条。启用状态与优先级各自只能有一个值，冲突时以 ``first`` 为准 ——
        它在名单里排得更前，是更早的那个决定。

        Args:
            first: 先出现的标记列表。
            second: 后出现的标记列表。

        Returns:
            list[str]: 合并后的标记列表。
        """
        def choose(values):
            for flags in (first, second):
                value = _Flags.pick(flags, values)
                if value is not None:
                    return value
            return None

        def dropped(flag):
            if flag in (_Flags.DISABLED, _Flags.ENABLED):
                return True
            return flag in PRIORITIES and flag != _DEFAULT_PRIORITY

        result = [flag for flag in first if not dropped(flag)]
        for flag in second:
            if flag not in result and not dropped(flag):
                result.append(flag)
        choice = choose((_Flags.DISABLED, _Flags.ENABLED))
        if choice is not None:
            result.append(choice)
        priority = choose([v for v in PRIORITIES if v != _DEFAULT_PRIORITY])
        if priority is not None:
            result.append(priority)
        return result

    @staticmethod
    def clear_choice(flags):
        """清掉「用户表态」，回到「跟插件默认值走」."""
        return [_flag for _flag in flags
                if _flag not in (_Flags.DISABLED, _Flags.ENABLED)]


def _read_state():
    """读名单原文（未解析）."""
    return app_data.getenv(key=_KEY_FILES, encoding='utf-8', default='') or ''


def _write_state(entries):
    """把 ``[(path, flags)]`` 写回 ``zml_plugins``（**一次**写盘）."""
    app_data.setenv(
        key=_KEY_FILES, encoding='utf-8',
        value=';'.join(_Text.join_path(path, flags) for path, flags in entries))


def _read_exceptions(key):
    """读兼容键里的「例外集合」（``;`` 分隔的路径），返回原始字符串列表."""
    return _Text.split_items(
        app_data.getenv(key=key, encoding='utf-8', default=''))


def _read_legacy_rank(path):
    """读旧实现的浮点 rank（失败返回 None）."""
    try:
        return float(app_data.getenv(key=get_hash(_LEGACY_RANK_PREFIX + path)))
    except (TypeError, ValueError):
        return None


def get_entries():
    """返回名单（解析后），**不做迁移**（迁移由 ``_alg.get_files`` 负责）.

    Returns:
        list[tuple[str, list[str]]]: ``[(路径原文, 标记列表)]``，保持名单顺序。
    """
    result = []
    for item in _Text.split_items(_read_state()):
        path, flags = _Text.split_path(item)
        if len(path) > 0:
            result.append((path, flags))
    return result


def set_entries(entries):
    """按 ``[(path, flags)]`` 整份替换名单（**一次**写盘）.

    Args:
        entries: 见 :func:`get_entries` 的返回值。
    """
    _write_state(list(entries))


def merge(paths, *, standard=False):
    """把一批文件并入名单（已存在的保持原位置），返回本次新增的数量.

    Args:
        paths: 要并入的路径（列表）。
        standard: True = 这些文件由自动发现得到，记 ``*``（下次启动不再扫描）。

    Returns:
        int: 新增的记录数。
    """
    entries = get_entries()
    known = {norm(path) for path, _ in entries}
    added = 0
    for path in paths:
        key = norm(path)
        if len(key) == 0 or key in known:
            continue
        entries.append((os.path.abspath(path), []) if not standard
                       else (os.path.abspath(path), [_Flags.STANDARD]))
        known.add(key)
        added += 1
    if added > 0:
        _write_state(entries)
    return added


def add_file(path):
    """手动登记一个插件文件：追加到名单末尾.

    ⚠️ 只登记、**不执行**：执行发生在下次 :func:`zmlx.ui.plugins.run_setup`
    （即重启界面）时。已在名单里的文件不会被重复添加，它的优先级与禁用状态保持不动。

    Args:
        path: 插件文件路径。

    Returns:
        bool: 真的加进去了返回 True；已在名单里、或路径非法返回 False。
    """
    return merge([path]) > 0


def remove_file(path):
    """把一个**手动登记**的插件移出名单（**只移出名单，不删磁盘文件**）.

    ⚠️ 与 :func:`add_file` 成对：**只有用 :func:`add_file` 加进来的才能移除**。
    自动发现的插件（``is_standard`` 为真）**不会被移除**，直接返回 False ——
    不这么做的话，移除了也会在下次启动扫描时**自己回来**，等于给了用户一个
    假的「删除」按钮。不想让自动发现的插件执行，请用 :func:`set_disabled`。

    Args:
        path: 插件文件路径。

    Returns:
        bool: 真的移出了返回 True；不在名单里、或是自动发现的（``is_standard``）
        返回 False。
    """
    key = norm(path)
    if len(key) == 0:
        return False
    entries = get_entries()
    kept = [(item, flags) for item, flags in entries
            if norm(item) != key or _Flags.STANDARD in flags]
    if len(kept) == len(entries):
        return False  # 不在这条名单里，或者它是自动发现的（被留下）
    _write_state(kept)
    return True


def migrate_legacy():
    """把旧实现（``zml_gui_setup_files`` + 浮点 rank）迁移到新模型.

    Returns:
        bool: 真的搬了东西返回 True（旧键为空时直接返回 False）。
    """
    legacy = _read_exceptions(_LEGACY_FILES_KEY)
    if len(legacy) == 0:
        return False

    moved = False
    entries = get_entries()
    known = {norm(path) for path, _ in entries}
    excluded = set()
    for item in legacy:
        key = norm(item)
        if len(key) == 0:
            continue
        if key not in known:
            entries.append((item, []))  # 保持旧登记表里的顺序，追加在后面
            known.add(key)
            moved = True
        if _read_legacy_rank(item) == _LEGACY_EXCLUDED_RANK:
            excluded.add(key)  # 旧语义：rank = 1e20 即「忽略」

    if moved:
        _write_state(entries)
    for key in excluded:
        for idx, (path, flags) in enumerate(entries):
            if norm(path) == key:
                entries[idx] = (path, _Flags.with_disabled(flags, True))
    if len(excluded) > 0:
        _write_state(entries)

    # 登记表已经搬进名单：清空旧键（老版本看到「没有额外登记」，与迁移后
    # 的语义一致 —— 那些文件已随扫描进入新名单）
    app_data.setenv(key=_LEGACY_FILES_KEY, encoding='utf-8', value='')
    return moved or len(excluded) > 0


def migrate_builtin_paths():
    """把名单里指向 ``plugins/<名>.py`` 的旧记录改写到 ``plugins/builtin/<名>.py``.

    ⚠️⚠️ **2026-10-19 内置插件下沉到 ``builtin/`` 之后，这一步是必需的**：名单里存的是
    **绝对路径**，文件一搬，旧记录就指向不存在的文件 ——
    :func:`zmlx.ui.plugins.run_setup` 会把它当成「文件缺失」跳过（不会报错），
    而新路径在名单里**没有任何记录** ⇒ :func:`is_disabled` 退回插件自报的默认值。
    结果：用户手动勾开过的彩蛋（默认 ``enabled = False``）会**静默**变回关闭，
    表现为「我明明开过，怎么又没了」，且没有任何提示。

    只改写「父目录恰好是本包目录、且 ``builtin/`` 下确实存在同名文件」的记录：其余
    记录（外部插件、用户已删除的文件）原样保留 —— 这条规则让函数**幂等**，重复调用
    不会产生第二次改写。

    ⚠️ 若新旧两条记录同时存在（例如搬迁后用户又在新路径上勾过一次），合并成一条：
    否则插件会被**执行两次**（:func:`zmlx.ui.plugins.get_files` 会给出两个路径）。
    标记按 :func:`_Flags.merge` 合并，更早的那条记录的表态优先。

    Returns:
        bool: 真的改写/合并了记录返回 True（没有旧记录时返回 False）。
    """
    folder = os.path.dirname(os.path.abspath(__file__))
    builtin = os.path.join(folder, 'builtin')
    result = []
    pos = {}  # 规范化路径 -> 在 result 里的下标
    changed = False
    for path, flags in get_entries():
        target = path
        if norm(os.path.dirname(path)) == norm(folder):
            candidate = os.path.join(builtin, os.path.basename(path))
            if os.path.isfile(candidate):
                target = candidate
        key = norm(target)
        if key in pos:  # 新旧两条记录指向同一个插件：合并，别让它执行两次
            idx = pos[key]
            result[idx] = (result[idx][0], _Flags.merge(result[idx][1], flags))
            changed = True
            continue
        pos[key] = len(result)
        result.append((target, flags))
        if target != path:
            changed = True
    if changed:
        _write_state(result)
    return changed


def find(path):
    """在名单里找一条记录.

    Args:
        path: 插件文件路径。

    Returns:
        (str, list) | None: ``(路径原文, 标记)``；不在名单里返回 None。
    """
    key = norm(path)
    if len(key) == 0:
        return None
    for item, flags in get_entries():
        if norm(item) == key:
            return item, flags
    return None


def is_standard(path):
    """这个插件是**自动发现**并入的，还是用户手动登记的.

    Args:
        path: 插件文件路径。

    Returns:
        bool: 自动发现（名单里带 ``*``）返回 True；用户登记、或不在名单里返回 False。
    """
    found = find(path)
    return found is not None and _Flags.STANDARD in found[1]


def is_disabled(path):
    """该插件是否**不启用** —— **用户的选择优先，否则看插件自己的默认**.

    判定顺序（三态）：

    ==========================  ==========================================
    名单里的标记                 结果
    ==========================  ==========================================
    ``disabled``                用户明确关掉 → **不启用**
    ``enabled``                 用户明确打开 → **启用**
    都没有（用户没表过态）       插件文件里 ``# ** enabled = ...`` 的值，
                                没写就是启用
    ==========================  ==========================================

    ⚠️ 这是刻意的：``enabled = False`` 是插件自报的**默认值**，不是强制开关。
    彩蛋默认不加载，但用户一旦在「设置 → 插件」里勾上，就以用户的为准 ——
    否则「默认关着」就变成了「永远不能开」。

    ⚠️ 默认值从插件文件读（``# ** enabled = ...``），由 :func:`zmlx.ui.plugins.
    get_meta` 提供；本模块不 import 它（会循环导入），而由包入口在运行时注入
    （见 :func:`set_default_enabled_resolver`）。没注入时按「默认启用」处理。

    ⚠️ 「禁用了」不等于「它做过的事被撤销」：插件是一段启动时执行的代码，一旦
    执行过，它派生的东西（挂在菜单上的项、起的后台线程）就归它自己，不由本系统
    回收。所以改了启用状态**重启才生效** —— 界面上的「状态」列也是这么写的。

    Args:
        path: 插件文件路径（``None`` 表示不在任何插件里 → 永远不禁用）。

    Returns:
        bool: 不启用返回 True。
    """
    if path is None:
        return False
    found = find(path)
    if found is not None:
        flags = found[1]
        if _Flags.DISABLED in flags:
            return True
        if _Flags.ENABLED in flags:
            return False
        return not _default_enabled(path)
    # 名单里没有（例如尚未迁移的老登记表）：退回兼容键
    key = norm(path)
    if any(norm(item) == key for item in _read_exceptions(_KEY_DISABLED)):
        return True
    return not _default_enabled(path)


#: 插件自报默认状态的读取函数（由 :func:`set_default_enabled_resolver` 注入）.
_default_enabled_resolver = None


def set_default_enabled_resolver(func):
    """（内部）注入「读取插件自报默认状态」的函数.

    ⚠️ 反向依赖走运行时注入，而不是 ``import``：``_registry`` 是被 ``_alg``
    导入的底层模块，反过来 import 会成环。见 :func:`zmlx.ui.plugins._alg.
    _set_default_enabled_resolver` 的说明。

    Args:
        func: 接路径、返回含 ``enabled`` 键的 dict 的函数。
    """
    global _default_enabled_resolver
    _default_enabled_resolver = func


def _default_enabled(path):
    """插件自报的默认启用状态（读不到就是 True）."""
    if _default_enabled_resolver is None:
        return True  # 没注入解析器：按最保守的「默认启用」处理
    try:
        meta = _default_enabled_resolver(path)
        enabled = meta.get('enabled', True)
        return bool(enabled)
    except Exception as err:  # 读配置出问题不该影响「能不能启动」
        warn(f'读取插件默认状态失败：{path}（{err}）', stacklevel=2)
        return True


def get_choice(path):
    """用户有没有对这个插件的启用状态**表过态**.

    Args:
        path: 插件文件路径。

    Returns:
        str | None: ``'disabled'`` / ``'enabled'`` / ``None``（没表态）。
    """
    found = find(path)
    if found is None:
        return None
    for flag in (_Flags.DISABLED, _Flags.ENABLED):
        if flag in found[1]:
            return flag
    return None


def get_priority(path):
    """返回该插件的优先级（``'high' / 'normal' / 'low'``）.

    Args:
        path: 插件文件路径。

    Returns:
        str: 未在名单里、或没设置过时返回 ``'normal'``。
    """
    found = find(path)
    if found is not None:
        return _Flags.parse_priority(found[1])
    key = norm(path)
    if any(norm(item) == key for item in _read_exceptions(_KEY_PRIORITY)):
        return 'high'  # 兼容：老记录只写了例外集合、没写名单标记
    return _DEFAULT_PRIORITY


def _ensure_in_list(entries, path):
    """确保 ``path`` 在名单里；不在就**追加**进 ``entries`` 并返回它.

    ⚠️⚠️ **内置插件原本不在名单里**（``_package_files()`` 只是把它们追加到
    ``get_files()`` 的返回值上，从没登记进 ``zml_plugins``）。于是对它们调
    ``set_disabled`` / ``set_priority`` 时匹配不到任何条目 —— 写入静默失效：
    用户取消勾选彩蛋、勾上彩蛋，界面上**什么都不会发生**。

    这里就地补登：没找到就追加到末尾（与用户手动「添加」同一个位置），
    并把规范化路径加进 ``known``（调用方据此去重）。

    Args:
        entries: ``[(路径, 标记)]``（会被就地修改）。
        path: 要确保存在的插件路径。

    Returns:
        int: 该条目在 ``entries`` 里的下标。
    """
    key = norm(path)
    for idx, (item, _) in enumerate(entries):
        if norm(item) == key:
            return idx
    entries.append((os.path.abspath(path), []))
    return len(entries) - 1


def set_disabled(path, disabled=True):
    """设置「是否启用」，**只改名单标记**（不动顺序、不动优先级）.

    Args:
        path: 插件文件路径（单个 ``str``，或路径列表一次改多个）。
        disabled: True = 禁用（启动时不执行），False = 启用。

    ⚠️ 对**内置插件**（``plugins/`` 目录里的）也有效：它们本来不在名单里，这里会
    先就地补登再写（见 :func:`_ensure_in_list`）。不补登的话，用户在「设置 → 插件」
    里勾选 / 取消勾选彩蛋会**没有任何效果**。

    ⚠️ 改完**重启**才生效：插件是一段启动时执行的代码，已经执行过的不会再撤回。
    """
    paths = [path] if isinstance(path, str) else list(path)
    wanted = {norm(item) for item in paths}
    if len(wanted) == 0:
        return
    order = {norm(item) for item in paths}
    entries = get_entries()
    for item in paths:
        _ensure_in_list(entries, item)
    for idx, (item, flags) in enumerate(entries):
        if norm(item) in order:
            entries[idx] = (item, _Flags.with_disabled(flags, disabled))
    _write_state(entries)


def clear_choice(paths=None):
    """清掉「用户对启用状态的表态」，回到**跟插件默认值走**.

    「恢复默认」用它：清完之后，``enabled = False`` 的插件（彩蛋）会重新变成
    默认不加载，而不是保留用户上次的勾选。

    Args:
        paths: 插件文件路径（单个 ``str`` 或列表）；``None`` 表示**全部插件**。
    """
    entries = get_entries()
    if paths is None:
        wanted = None
    else:
        items = [paths] if isinstance(paths, str) else list(paths)
        wanted = {norm(item) for item in items}
        if len(wanted) == 0:
            return
        for item in items:  # 内置插件不在名单里 → 就地补登（同 set_disabled）
            _ensure_in_list(entries, item)
    for idx, (item, flags) in enumerate(entries):
        if wanted is None or norm(item) in wanted:
            entries[idx] = (item, _Flags.clear_choice(flags))
    _write_state(entries)


def set_priority(path, priority):
    """设置优先级，**只改名单标记**（不动顺序）.

    Args:
        path: 插件文件路径（单个 ``str``，或路径列表一次改多个）。
        priority: ``'high'`` / ``'normal'`` / ``'low'``。

    Raises:
        ValueError: 优先级取值非法。
    """
    if priority not in PRIORITIES:
        raise ValueError(
            f'priority 只能是 {"/".join(PRIORITIES)}，收到：{priority!r}')
    paths = [path] if isinstance(path, str) else list(path)
    wanted = {norm(item) for item in paths}
    if len(wanted) == 0:
        return
    entries = get_entries()
    for item in paths:  # 内置插件不在名单里 → 就地补登（同 set_disabled）
        _ensure_in_list(entries, item)
    for idx, (item, flags) in enumerate(entries):
        if norm(item) in wanted:
            entries[idx] = (item, _Flags.with_priority(flags, priority))
    _write_state(entries)


def get_state_list():
    """返回**全部**插件（含禁用、含缺失）及各自状态 —— 界面的唯一数据源.

    ⚠️ 顺序**不是**用户可调的：用户登记的排在前面（按加入先后），自动发现的
    排在后面；真正的执行先后由优先级决定（见 :func:`zmlx.ui.plugins.get_files`）。

    Returns:
        list[dict]: 每项含 ``path`` / ``priority`` / ``disabled`` /
        ``standard``（是否自动发现）/ ``exists``（文件是否还在）。
    """
    result = []
    for path, flags in get_entries():
        result.append({
            'path': path,
            'priority': _Flags.parse_priority(flags),
            'disabled': _Flags.DISABLED in flags,
            'standard': _Flags.STANDARD in flags,
            'exists': os.path.isfile(path),
            # 「用户表过态吗」：None = 跟随插件自报的默认值（界面上会注明）
            'choice': get_choice(path),
        })
    return result


def list_all(*, only_existing=False, include_disabled=True):
    """返回名单里的**全部**插件（界面显示用），按「优先级 → 名单顺序」排.

    Args:
        only_existing: 只返回磁盘上确实存在的文件。
        include_disabled: 是否包含被禁用的那些。

    Returns:
        list[tuple[str, dict]]: ``[(路径, 状态)]``；状态含
        ``priority`` / ``disabled`` / ``standard`` / ``exists``。
    """
    entries = []
    for path, flags in get_entries():
        state = {
            'priority': _Flags.parse_priority(flags),
            'disabled': _Flags.DISABLED in flags,
            'standard': _Flags.STANDARD in flags,
            'exists': os.path.isfile(path),
        }
        if not include_disabled and state['disabled']:
            continue
        if only_existing and not state['exists']:
            continue
        entries.append((path, state))

    # 两个稳定排序串起来（先按文件名档次、再按优先级），等价于
    # ``key = (优先级, 文件名档次)``，但**只降不升**：旧名（兼容名）永远沉到
    # 同段的最后，而推荐的 ``zml_plugin.py`` **不会**被提到普通文件之前 ——
    # 名单顺序就是用户拖动出来的顺序，不能被「文件名好看」改写。
    entries.sort(key=lambda item: plugin_name_rank(item[0]))
    order = {value: idx for idx, value in enumerate(PRIORITIES)}
    entries.sort(key=lambda item: order[item[1]['priority']])
    return entries


def get_files():
    """返回**该执行的**插件（已过滤禁用、已按优先级分段排序）.

    ⚠️ 这是执行侧唯一的入口。界面要显示**全部**插件（含禁用、含缺失），
    用 :func:`list_all`。

    Returns:
        list[str]: 绝对路径，按「高 → 正常 → 低」分段、段内按名单顺序、
        同段同名时 ``zml_plugin.py`` 排在旧名之前。
    """
    return [path for path, _ in
            list_all(only_existing=True, include_disabled=False)]


def get_state_text():
    """返回一份可读的完整状态（调试用：``python -m zmlx.ui.plugins._registry``）."""
    lines = ['# 名单（按执行顺序；显示顺序 = 名单顺序）']
    entries = list_all()
    if len(entries) == 0:
        lines.append('  （空）')
    for idx, (path, state) in enumerate(entries):
        marks = []
        if state['disabled']:
            marks.append('禁用')
        if state['priority'] != _DEFAULT_PRIORITY:
            marks.append(state['priority'])
        if state['standard']:
            marks.append('自动发现')
        if not state['exists']:
            marks.append('缺失')
        lines.append(f'  {idx}: {path}  [{" ".join(marks) or "缺省"}]')
    if len(_read_exceptions(_LEGACY_FILES_KEY)) > 0:
        lines.append('⚠️ 旧登记表尚未迁移（下次启动 get_files 时自动迁移）')
    return '\n'.join(lines)


if __name__ == '__main__':
    print(get_state_text())
