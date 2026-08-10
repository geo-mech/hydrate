"""
默认求解器代码（线程安全）。

存储创建求解器的 Python 代码字符串.
make_solver() 通过 eval/exec 执行，创建局部实例，避免多线程冲突。

支持两种格式:
    1. 简单表达式 (eval):  "ICCGSolver(tolerance=1e-12)"
    2. 完整语句 (exec):    "from X import Y\\nsolver = Y(...)"
"""

_default_code = (
    'from zmlx.exts._sol import ConjugateGradientSolver\n'
    'solver = ConjugateGradientSolver(tolerance=1e-20)'
)


def set_default_solver_code(code):
    """设置默认求解器代码."""
    global _default_code
    _default_code = code


def get_default_solver_code():
    """获取默认求解器代码."""
    return _default_code


def _make_eval_space():
    """创建 eval 命名空间，包含常见求解器类."""
    from zmlx.exts._sol import (
        ConjugateGradientSolver, ICCGSolver, SparseLUSolver,
        SimplicialLDLTSolver, BiCGSTABSolver, ILUBiCGSTABSolver,
    )
    return {
        'ConjugateGradientSolver': ConjugateGradientSolver,
        'ICCGSolver': ICCGSolver,
        'SparseLUSolver': SparseLUSolver,
        'SimplicialLDLTSolver': SimplicialLDLTSolver,
        'BiCGSTABSolver': BiCGSTABSolver,
        'ILUBiCGSTABSolver': ILUBiCGSTABSolver,
    }


def make_solver(code=None):
    """执行代码创建局部求解器实例.

    Args:
        code: Python 代码, None 时用默认代码.
    Returns:
        求解器实例 (有 .fn / .ctx 属性).
    """
    c = code or _default_code
    # 1) 完整语句 (exec，无需预定义空间，效率最高)
    d = {}
    try:
        exec(c, d)
        r = d.get('solver')
        if r is not None and hasattr(r, 'fn') and hasattr(r, 'ctx'):
            return r
    except Exception:
        pass
    # 2) 简单表达式 (eval，需预导入求解器类)
    try:
        r = eval(c, _make_eval_space())
        if hasattr(r, 'fn') and hasattr(r, 'ctx'):
            return r
    except (SyntaxError, NameError):
        pass
    raise ValueError(f'Not a solver: {c}')


def add_solver_log(msg):
    from zmlx.system import app_data
    logs = app_data.get("_solver_logs")
    if isinstance(logs, list):
        logs.append(msg)
    else:
        logs = [msg]
        app_data.set("_solver_logs", logs)


def _test():
    # eval 表达式
    print('default:', get_default_solver_code())
    s = make_solver()
    print('solver:', s)
    # exec 语句
    s2 = make_solver(
        'from zmlx.exts._sol import ICCGSolver\n'
        'solver = ICCGSolver(tolerance=1e-12, shift=0.001)')
    print('exec:', s2)
    # eval with param
    set_default_solver_code('BiCGSTABSolver(tolerance=1e-8)')
    s3 = make_solver()
    print('eval:', s3)


if __name__ == '__main__':
    _test()
