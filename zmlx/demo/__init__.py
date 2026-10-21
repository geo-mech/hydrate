"""旧包名（**兼容层，已弃用**）：``zmlx.demo`` -> :mod:`zmlx.demos`.

⚠️⚠️ **本包只是因为外部还有人在用才存在**（2026-10-16 起弃用，**2027-10-16 删除**）。

⚠️ **本包是「最小垫片」—— 只转发确有外部引用的 2 个模块**
（`hydrate.co2_disp`、`opath`），**不是** `zmlx/demos/` 下 154 个案例的完整镜像：

    from zmlx.demo.hydrate.co2_disp import execute   # methane-hydrate 在用
    from zmlx.demo.opath import opath                # productivity 在用

为什么其余模块没有垫片
----------------------

`zmlx/demos/` 下绝大多数是**顶层的可运行案例**，不是给人 import 的库代码 ——
实测 154 个模块里只有 4 个被 import 过。为一个没人 import 的包留 180 个转发文件，
只会让人误以为 demo 是被大量依赖的库。

⚠️ **教训（这条值得记）**：当初判定「没人 import demo」时，我只在 **zmlx 本仓**里搜索，
结论是「零处引用」，于是删掉了旧包 —— **但外部工作区 `igg-hydrate-works` 里有 2 个
项目在用**。**「本仓没人引用」不等于「没人引用」。** 删任何「已弃用」模块之前，
必须连外部工作区一起搜。

⚠️ 新代码请写 ``from zmlx.demos.<模块> import ...``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
warn(
    '``zmlx.demo`` 已弃用（2026-10-16）：已改名为 ``zmlx.demos``；'
    '本兼容包将于 **2027-10-16** 删除。请改用 ``from zmlx.demos import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

# ⚠️ 本包**只**转发这两个确有外部引用的模块（见上面 docstring 的教训说明）。
_NAMES = {
    'opath': ('opath', 'opath'),
    'set_output': ('opath', 'set_output'),
}


def __getattr__(name):
    """PEP 562：按需转发 :mod:`zmlx.demos` 的名字（只覆盖上面那几个）。"""
    entry = _NAMES.get(name)
    if entry is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    mod, real = entry
    return getattr(importlib.import_module('zmlx.demos.%s' % mod), real)


def __dir__():
    return sorted(set(list(globals()) + list(_NAMES)))
