"""SciPy 稀疏直接求解器（SuperLU）Python 封装.

通过 scipy.sparse.linalg.spsolve 求解 Ax=b，提供与 FuncSol 兼容的接口.

使用方式:
    from zmlx.exts.scipy_sol import SciPySolver
    solver = SciPySolver()
    err = solver.solve(rows, cols, vals, x, b)

    # 作为 FuncSol callback 使用:
    # solver.fn  → C 函数指针 (ctypes CFUNCTYPE)
    # solver.ctx → 上下文指针 (solver 实例 id)
"""

from ctypes import c_double, c_int, c_void_p, cast, CFUNCTYPE, POINTER

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve


# ── C callback 生成 ───────────────────────────────────────────────────

def _make_solve_callback(solver_instance):
    """生成一个 C 兼容的回调函数，将 FuncSol 参数转发到 solver_instance.solve().

    CFUNCTYPE 工厂函数会将 Python 函数包装为 C 函数指针.
    """

    @CFUNCTYPE(c_int, c_void_p, c_int, c_int,
               POINTER(c_int), POINTER(c_int), POINTER(c_double),
               POINTER(c_double), POINTER(c_double), c_int)
    def callback(ctx, n, nnz, rows_p, cols_p, vals_p, x_p, b_p, with_guess):
        try:
            # ctypes pointer → numpy
            rows_np = np.ctypeslib.as_array(rows_p, shape=(nnz,))
            cols_np = np.ctypeslib.as_array(cols_p, shape=(nnz,))
            vals_np = np.ctypeslib.as_array(vals_p, shape=(nnz,))
            b_np = np.ctypeslib.as_array(b_p, shape=(n,))

            # COO → CSR
            A = sp.coo_matrix((vals_np, (rows_np, cols_np)), shape=(n, n))
            A = A.tocsr()

            # Solve
            result = spsolve(A, b_np)

            # Write solution → x buffer
            x_np = np.ctypeslib.as_array(x_p, shape=(n,))
            x_np[:] = result
            return 0
        except Exception as e:
            print(f'SciPySolver error: {e}')
            return -1

    return callback


# ── SciPySolver ───────────────────────────────────────────────────────

class SciPySolver:
    """基于 scipy.sparse.linalg.spsolve (SuperLU) 的稀疏直接求解器.

    特点:
    - 纯 Python 实现，无需编译
    - COO 三元组输入（与 FuncSol 兼容）
    - 适用于一般稀疏方阵（自动 SuperLU 分解）
    - 小到中等规模（n < 5e4），大规模用迭代法
    """

    def __init__(self):
        self._handle = id(self)
        self._fn = _make_solve_callback(self)

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """求解 Ax = b (直接法，忽略 with_guess).

        Args:
            rows, cols, vals: COO 三元组（int32/float64 numpy 或 ctypes 数组，长度 nnz）
            x: 解向量缓冲区 (in/out, float64, 长度 n)
            b: 右端项 (float64, 长度 n)
            with_guess: 忽略（直接法）

        Returns:
            int: 0 = 成功
        """
        # 统一转为 numpy
        if not isinstance(rows, np.ndarray):
            rows = np.ctypeslib.as_array(rows, shape=(len(rows) if hasattr(rows, '__len__') else 0,))
        if not isinstance(cols, np.ndarray):
            cols = np.ctypeslib.as_array(cols, shape=(len(cols) if hasattr(cols, '__len__') else 0,))
        if not isinstance(vals, np.ndarray):
            vals = np.ctypeslib.as_array(vals, shape=(len(vals) if hasattr(vals, '__len__') else 0,))
        if not isinstance(b, np.ndarray):
            b_np = np.ctypeslib.as_array(b, shape=(len(b) if hasattr(b, '__len__') else 0,))
        else:
            b_np = b

        n = len(b_np)

        try:
            A = sp.coo_matrix((vals, (rows, cols)), shape=(n, n))
            A = A.tocsr()
            result = spsolve(A, b_np)

            if not isinstance(x, np.ndarray):
                x_np = np.ctypeslib.as_array(x, shape=(n,))
            else:
                x_np = x
            x_np[:] = result
            return 0
        except Exception as e:
            print(f'SciPySolver error: {e}')
            return -1

    @property
    def fn(self):
        """FuncSol C 函数指针."""
        return self._fn

    @property
    def ctx(self):
        """上下文指针（= id(self)），与 fn 配对."""
        return c_void_p(self._handle)

    @property
    def handle(self):
        return self._handle

    def __repr__(self):
        return f'{type(self).__name__}(handle={self._handle})'
