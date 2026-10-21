"""旧流体包名（**兼容垫片，已弃用**）：``zmlx.fluid`` -> :mod:`zmlx.fluids`.

⚠️⚠️ **本包整个是一层兼容垫片，将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。
导入本包**或本包下任何子模块 / 子包**都会发出 :class:`DeprecationWarning`。

**新代码请写** ``from zmlx.fluids import create_h2o``（子模块路径
``from zmlx.fluids.h2o import create`` 同样可以）。

为什么改名为 ``fluids``
-----------------------

与 ``algs`` / ``utils`` / ``ui.widgets`` 统一用**复数**目录名 —— 本包里装的是
「各种流体」（水、甲烷、CO2、水合物……），复数才是它实际的内容。

⚠️ 本包的 ``__init__.py`` **不可省略**：没有它 ``zmlx.fluid`` 就不是包，
``from zmlx.fluid import create_h2o`` 与下面那些子模块 / 子包转发全都失效 ——
垫片的价值正在于「老路径一条都不断」。

覆盖范围
--------

本包递归覆盖旧 ``fluid/`` 的**整棵树**（含嵌套子包，最深 3 层）：

- ``zmlx.fluid.<模块>``（90 个）→ ``zmlx.fluids.<模块>``
- ``zmlx.fluid.<子包>``（18 个，如 ``cp`` / ``rkt`` / ``rkt.aq`` / ``conf.gas_density``
  / ``nist.h2o``）→ ``zmlx.fluids.<同名子包>``

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.fluid`` 改为 ``zmlx.fluids``.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
warn(
    '``zmlx.fluid`` 已弃用（2026-10-16）：流体包已改名为 ``zmlx.fluids``；'
    '本兼容包将于 **2027-10-16** 删除。请改用 ``from zmlx.fluids import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# 包级名字：转发到 zmlx.fluids 的对应实现。
#
# ⚠️ 用 PEP 562 的模块级 __getattr__ **惰性**转发，而不是静态 import：
#    fluids 的子模块会 import zmlx.exts（cp / rkt 还可能拖起第三方库），
#    静态导入容易在导入期打结（同类重构里实测踩过 partially initialized module）。
# ---------------------------------------------------------------------------

#: 名字 -> ``(所属模块, 该模块里的真实名字)``。
#:
#: ⚠️ **必须带上「真实名字」**：旧 ``__init__`` 里有一批是**起了别名**的，例如
#:    ``from zmlx.fluid.h2o import create as create_h2o`` —— 模块里叫 ``create``，
#:    包级才叫 ``create_h2o``。只记模块名就会去 ``zmlx.fluids.h2o`` 上找
#:    ``create_h2o``，必然 AttributeError（这一版验收脚本就是这么抓出来的）。
#:
#: ⚠️ 与当年 ``fluid/__init__.py`` 的导出面一致，**不扩大 API 面**。
_NAMES = {
    'create_aqueous': ('_aqueous', 'create_aqueous'),
    'create_mixture': ('_mixture', 'create_mixture'),
    'from_data': ('alg', 'from_data'),
    'from_file': ('alg', 'from_file'),
    'load_fludefs': ('alg', 'load_fludefs'),
    'create_ch4': ('ch4', 'create'),
    'create_ch4_hydrate': ('ch4_hydrate', 'create'),
    'create_co2': ('co2', 'create'),
    'create_co2_hydrate': ('co2_hydrate', 'create'),
    'create_h2o': ('h2o', 'create'),
    'create_h2o_gas': ('h2o_gas', 'create'),
    'create_h2o_ice': ('h2o_ice', 'create'),
    'create_solute': ('solution', 'create_solute'),
    'SelfPath': ('zmlx.exts', 'SelfPath'),
    # 旧 __init__ 末尾的 `get_path = SelfPath(__file__)` 也是**包级导出**，
    # 漏掉就会断 `from zmlx.fluid import get_path`（全量审计抓到的真缺口）。
    'get_path': ('zmlx.fluids', 'get_path'),
}


def __getattr__(name):
    """PEP 562：按需把 :mod:`zmlx.fluids` 的名字转发过来（理由见上面那段 ⚠️）."""
    entry = _NAMES.get(name)
    if entry is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    mod, real = entry
    full = mod if '.' in mod else 'zmlx.fluids.%s' % mod
    return getattr(importlib.import_module(full), real)


def __dir__():
    return sorted(set(list(globals()) + list(_NAMES)))
