"""旧包名（**兼容层，已弃用**）：``zmlx.seepage_mesh`` -> :mod:`zmlx.seepage_meshes`.

⚠️⚠️ **本包是一层兼容转发，将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。
导入本包**或本包下任何子模块**都会发出 :class:`DeprecationWarning`。

**新代码请写** ``from zmlx.seepage_meshes import ...`` 或 ``from zmlx.seepage_meshes.<模块> import ...``。

为什么改名为 ``seepage_meshes``
----------------------

与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``ui.widgets``
统一用**复数**目录名。

⚠️ 本包的 ``__init__.py` **不可省略**：没有它 ``zmlx.seepage_mesh`` 就不是包，
``from zmlx.seepage_mesh import ...`` 与下面那些子模块转发全都失效 ——
兼容层的价值正在于「老路径一条都不断」。


Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.seepage_mesh`` 改为 ``zmlx.seepage_meshes``.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
warn(
    '``zmlx.seepage_mesh`` 已弃用（2026-10-16）：已改名为 ``zmlx.seepage_meshes``；'
    '本兼容包将于 **2027-10-16** 删除。请改用 ``from zmlx.seepage_meshes import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# 包级名字：转发到 zmlx.seepage_meshes 的对应实现。
#
# ⚠️ 用 PEP 562 的模块级 __getattr__ **惰性**转发，而不是静态 import ——
#    避免「垫片导入期 -> seepage_meshes 子模块 -> 回头 import zmlx.*」打结
#    （同类重构里实测踩过 partially initialized module）。
#
# ⚠️ 映射是 (所属模块, 该模块里的真实名字) 二元组：
#    旧 __init__ 里常有 `from ... import X as Y` 的**别名**
#    （fluid 那次 7 个 create_* 就因为只记模块名而全挂）。
# ---------------------------------------------------------------------------

_NAMES = {
    # ``SelfPath`` 来自 zmlx.exts（不在新包里），单独转接
    'SelfPath': ('zmlx.exts', 'SelfPath'),
    'create_cube': ('cube', 'create_cube'),
    'create_xy': ('cube', 'create_xy'),
    'create_xz': ('cube', 'create_xz'),
    'create_xyz': ('cube', 'create_xyz'),
    'create_cube_seepage_mesh': ('cube', 'create_cube'),
    'create_cylinder': ('cylinder', 'create_cylinder'),
    'add_cell_face': ('edit', 'add_cell_face'),
    'seepage_mesh_rescale': ('edit', 'scale'),
    'swap_yz': ('edit', 'swap_yz'),
    'swap_xy': ('edit', 'swap_xy'),
    'swap_xz': ('edit', 'swap_xz'),
    'seepage_mesh_swap_yz': ('edit', 'swap_yz'),
    'seepage_mesh_swap_xy': ('edit', 'swap_xy'),
    'seepage_mesh_swap_xz': ('edit', 'swap_xz'),
    'create_wellbore': ('wellbore', 'create_wellbore'),
    # 旧 __init__ 里的 `get_path = SelfPath(__file__)` 也是包级导出
    'get_path': ('zmlx.seepage_meshes', 'get_path'),}


def __getattr__(name):
    """PEP 562：按需把 :mod:`zmlx.seepage_meshes` 的名字转发过来（理由见上面那段 ⚠️）."""
    entry = _NAMES.get(name)
    if entry is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    mod, real = entry
    full = mod if '.' in mod else 'zmlx.seepage_meshes.%s' % mod
    return getattr(importlib.import_module(full), real)


def __dir__():
    return sorted(set(list(globals()) + list(_NAMES)))
