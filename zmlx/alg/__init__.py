"""旧算法包名（兼容层，**已改名为** :mod:`zmlx.algs`）.

⚠️⚠️ **本包整个是一层转发**，真正的实现在 :mod:`zmlx.algs`。本包只为让老路径继续可用：

```python
from zmlx.alg import clamp            # 老路径，仍然可用
from zmlx.alg.base import clamp       # 老路径，仍然可用
from zmlx.algs import clamp           # ✅ 新路径（推荐）
```

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。

⚠️ **注意本包内还有两类东西**：

1. 上面这种**改名转发**（36 个真模块的入口，转 ``zmlx.algs``）；
2. **更早就已弃用的模块**（``alpha`` / ``clamp`` / ``time`` …，共 60 个）——
   它们在改名**之前**就已经是弃用垫片了（各自 ``warnings.warn`` + 指向别处），
   本次改名**原样留在本包**、**没有**搬进 ``zmlx.algs``（已弃用的东西不往新包里带）。
   它们**自己发的**弃用警告保持不动。

⚠️ 本包的 ``__init__.py`` **不可省略**：没有它 ``zmlx.alg`` 就不是一个包，
``from zmlx.alg import clamp`` 与下面那些子模块转发全都失效。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.alg`` 改为 ``zmlx.algs``（本包成了转发层）.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

# ---------------------------------------------------------------------------
# 包级名字：转发到 zmlx.algs 的对应实现。
#
# ⚠️ 用 PEP 562 的模块级 __getattr__ **惰性**转发，而不是在这里静态 import：
#    某些子模块会 import zmlx.exts / zmlx.tfc，静态导入有可能在导入期打结
#    （同类重构里实测踩过 ``partially initialized module``）。
#    惰性转发在导入期一个子模块都不碰，对使用者完全无感：
#    ``from zmlx.alg import clamp`` 照常可用。
# ---------------------------------------------------------------------------


from zmlx.system import warn
warn(
    '``zmlx.alg`` 已弃用（2026-10-16）：算法包已改名为 ``zmlx.algs``；'
    '本兼容包将于 **2027-10-16** 删除。请改用 ``from zmlx.algs import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

#: 名字 -> 所属的 ``zmlx.algs`` 模块名。
#:
#: ⚠️ 与当年 ``alg/__init__.py`` 的导出面保持一致，**不扩大 API 面**。
_NAMES = {
    'code_config': '_code_config',
    'get_velocity_after_slowdown_by_viscosity': '_slowdown',
    'startfile': '_startfile',
    'update_by_git': '_update_by_git',
    'year_to_seconds': 'base',
    'rand_dir3': 'base',
    'make_index': 'base',
    'clamp': 'base',
    'linspace': 'base',
    'mean': 'base',
    'divide_list': 'base',
    'less': 'base',
    'is_sorted': 'base',
    'join_cols': 'base',
    'join_rows': 'base',
    'mass2str': 'base',
    'time2str': 'base',
    'fsize2str': 'base',
    'first_only': 'fsys',
    'print_tag': 'fsys',
    'join_paths': 'fsys',
    'make_fname': 'fsys',
    'count_lines': 'fsys',
    'list_files': 'fsys',
    'get_last_file': 'fsys',
    'create_interp1d': 'interp',
    'interp1': 'interp',
    'create_async': 'multi_proc',
    'apply_async': 'multi_proc',
    'sbatch': 'sys',
    'timing_show': 'sys',
    'pip_install': 'sys',
    'install_dep': 'sys',
    'get_cell_mask': 'zmlx.exts',
    'get_pos_range': 'zmlx.exts',
    'SelfPath': 'zmlx.exts',
    # 旧 __init__ 末尾的 `get_path = SelfPath(__file__)` 也是**包级导出**，
    # 漏掉就会断 `from zmlx.alg import get_path`（全量审计抓到的真缺口）。
    'get_path': 'zmlx.algs',
    # 基准里本包 `import warnings`（自己发弃用警告用），于是 zmlx.alg.warnings
    # 顺带可见；审计实测原本取得到，故补上（标准库的 warnings，不是本仓的那个）。
    # ⚠️ 基准里本包 `import warnings`，于是 zmlx.alg.warnings 顺带可见。
    #    它是**标准库的 warnings**（不是本仓的 zmlx.algs.sys）。见下方 __getattr__ 的特判。
}


def __getattr__(name):
    # ⚠️ 特判：``zmlx.alg.warnings`` 是**标准库**的 warnings（基准里本包
    #    `import warnings` 顺带可见），不是 zmlx.algs 的子模块 —— 不能走下面的
    #    'zmlx.algs.%s' 拼接，否则会去找 zmlx.algs.warnings 而 ModuleNotFoundError。
    if name == 'warnings':
        import warnings as _w
        return _w
    """PEP 562：按需把 :mod:`zmlx.algs`（或 :mod:`zmlx.exts`）的名字转发过来.

    ⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本包时会发出
    :class:`DeprecationWarning`。**新代码请写** ``from zmlx.algs import ...``。
    """
    mod = _NAMES.get(name)
    if mod is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    full = mod if '.' in mod else 'zmlx.algs.%s' % mod
    return getattr(importlib.import_module(full), name)


def __dir__():
    return sorted(set(list(globals()) + list(_NAMES)))
