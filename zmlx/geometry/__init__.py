"""旧几何包名（**兼容垫片，已弃用**）：``zmlx.geometry`` -> :mod:`zmlx.geometries`.

⚠️⚠️ **本包整个是一层兼容垫片，将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。
导入本包**或本包下任何子模块**都会发出 :class:`DeprecationWarning`。

**新代码请写** ``from zmlx.geometries.point import get_angle``（子模块路径），
或 ``from zmlx.geometries import get_angle``（包级，见下）。

为什么改名为 ``geometries``
---------------------------

与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``ui.widgets`` 统一用**复数**目录名。

⚠️ 本包的 ``__init__.py`` **不可省略**：没有它 ``zmlx.geometry`` 就不是包，
``from zmlx.geometry import get_angle`` 与下面那些子模块转发全都失效。

⚠️ **本包内那 10 个旧弃用垫片不搬进 ``geometries/``**
（``get_angle`` / ``get_center`` / ``get_norm`` / ``get_seg_angle`` /
``get_seg_point_distance`` / ``point_distance`` / ``seg_intersection`` /
``seg_point_distance`` / ``triangle_area`` / ``utils``）——
它们在改名**之前**就已弃用（各自 ``warnings.warn`` + 指向 ``zmlx.geometries`` 的
``point`` / ``segment`` / ``triangle`` / ``base``，其中 ``get_norm`` 指向 ``numpy.linalg``），
已弃用的东西不往新包里带，它们**原地留在本包**、自己发的警告保持不动。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.geometry`` 改为 ``zmlx.geometries``.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
warn(
    '``zmlx.geometry`` 已弃用（2026-10-16）：几何包已改名为 ``zmlx.geometries``；'
    '本兼容包将于 **2027-10-16** 删除。请改用 ``from zmlx.geometries import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# 包级名字：转发到 zmlx.geometries 的对应实现。
#
# ⚠️ 用 PEP 562 的模块级 __getattr__ **惰性**转发，而不是静态 import ——
#    避免「垫片导入期 -> geometries 子模块 -> 回头 import zmlx.*」打结
#    （同类重构里实测踩过 partially initialized module）。
#
# ⚠️ 映射是 (所属模块, 该模块里的真实名字) 二元组：
#    旧 __init__ 做的是 `from zmlx.geometry.base import *` —— base 自己又是从
#    point / segment / triangle 转出来的（见 geometries/base.py 的 _keep）。
#    这里统一指向 **base**（它就是当年的聚合出口，实测那 8 个名字在 base 上都能取到），
#    不再自己去猜上游 —— 猜错只会得到静默的 AttributeError。
# ---------------------------------------------------------------------------

_BASE_NAMES = ['get_angle', 'get_center', 'get_norm', 'get_seg_angle',
               'point_distance', 'seg_intersection', 'seg_point_distance',
               'triangle_area']

#: 名字 -> (所属的 ``zmlx.geometries`` 模块, 该模块里的真实名字)
_NAMES = {n: ('base', n) for n in _BASE_NAMES}
# 旧 __init__ 把 point_distance 另起了个别名 get_distance
# （`from zmlx.geometry.base import point_distance as get_distance`）——
# 这是**别名**，模块里没有也叫 get_distance 的东西，所以真实名字仍是 point_distance。
_NAMES['get_distance'] = ('base', 'point_distance')
_NAMES['SelfPath'] = ('zmlx.exts', 'SelfPath')
# 旧 __init__ 末尾还有 get_path = SelfPath(__file__) —— 它同样是包级导出，
# 漏掉就会断 `from zmlx.geometry import get_path`（验收脚本抓到的真缺口）。
_NAMES['get_path'] = ('zmlx.geometries', 'get_path')


def __getattr__(name):
    """PEP 562：按需把 :mod:`zmlx.geometries` 的名字转发过来（理由见上面那段 ⚠️）."""
    entry = _NAMES.get(name)
    if entry is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    mod, real = entry
    full = mod if '.' in mod else 'zmlx.geometries.%s' % mod
    return getattr(importlib.import_module(full), real)


def __dir__():
    return sorted(set(list(globals()) + list(_NAMES)))
