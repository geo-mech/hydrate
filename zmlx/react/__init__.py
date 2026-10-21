"""旧反应包名（**兼容垫片，已弃用**）：``zmlx.react`` -> :mod:`zmlx.reactions`.

⚠️⚠️ **本包整个是一层兼容垫片，将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。
导入本包**或本包下任何子模块 / 子包**都会发出 :class:`DeprecationWarning`。

**新代码请写** ``from zmlx.reactions import create_reaction``（子模块路径
``from zmlx.reactions.alg import create_reaction`` 同样可以）。

为什么改名为 ``reactions``
--------------------------

与 ``algs`` / ``utils`` / ``fluids`` / ``ui.widgets`` 统一用**复数**目录名 ——
本包装的是一堆**反应**定义（水合物、相变、燃烧、溶解……），复数才贴切。

⚠️ 本包的 ``__init__.py`` **不可省略**：没有它 ``zmlx.react`` 就不是包，
``from zmlx.react import create_reaction`` 与下面那些子模块 / 子包转发全都失效。

⚠️ **本包内那 2 个旧弃用垫片不搬进 ``reactions/``**
（``add_reaction`` / ``create_reaction``，它们在改名**之前**就已弃用、
各自 warnings.warn 并指向 ``zmlx.reactions.alg``）—— 已弃用的东西不往新包里带，
它们**原地留在本包**，自己发的警告保持不动。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.react`` 改为 ``zmlx.reactions``.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
warn(
    '``zmlx.react`` 已弃用（2026-10-16）：反应包已改名为 ``zmlx.reactions``；'
    '本兼容包将于 **2027-10-16** 删除。请改用 ``from zmlx.reactions import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# 包级名字：转发到 zmlx.reactions 的对应实现。
#
# ⚠️ 用 PEP 562 的模块级 __getattr__ **惰性**转发，而不是静态 import：
#    reactions 的子模块会 import zmlx.exts / zmlx.tfc，静态导入容易在导入期打结
#    （同类重构里实测踩过 partially initialized module）。
#
# ⚠️ 映射是 (所属模块, 该模块里的真实名字) 二元组 ——
#    旧 __init__ 里有起别名的（`from ... import X as Y`），只记模块名会去
#    模块上找一个不存在的名字（fluid 那次 7 个 create_* 全挂在这里）。
# ---------------------------------------------------------------------------

_NAMES = {
    'load_reactions': ('alg', 'load_reactions'),
    'add_reaction': ('alg', 'add_reaction'),
    'create_reaction': ('alg', 'create_reaction'),
    'create_inh': ('inh', 'create_inh'),
    'add_inh': ('inh', 'add_inh'),
    'SelfPath': ('zmlx.exts', 'SelfPath'),
    # 旧 __init__ 末尾的 `get_path = SelfPath(__file__)` 也是**包级导出**，
    # 漏掉就会断 `from zmlx.react import get_path`（全量审计抓到的真缺口）。
    'get_path': ('zmlx.reactions', 'get_path'),
}


def __getattr__(name):
    """PEP 562：按需把 :mod:`zmlx.reactions` 的名字转发过来（理由见上面那段 ⚠️）."""
    entry = _NAMES.get(name)
    if entry is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    mod, real = entry
    full = mod if '.' in mod else 'zmlx.reactions.%s' % mod
    return getattr(importlib.import_module(full), real)


def __dir__():
    return sorted(set(list(globals()) + list(_NAMES)))
