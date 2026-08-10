"""CUDA GPU 稀疏线性求解器 Python 封装.

基于 CuPy/cupyx 实现 GPU 上的稀疏线性求解，
提供与 FuncSol 兼容的接口.

支持的求解方法:
    - direct:   cuSOLVER LU 直接分解 (默认)
    - cg:       ConjugateGradient (SPD)
    - bicgstab: BiCGSTAB (一般)
    - gmres:    GMRES (一般)
    - bicg:     BiCG (一般)

使用方式:
    from zmlx.exts.cuda_sol import CudaSolver
    solver = CudaSolver(method='cg', tol=1e-10)
    err = solver.solve(rows, cols, vals, x, b)
"""

from ctypes import c_double, c_int, c_void_p, CFUNCTYPE, POINTER

import numpy as np


# ── C callback ────────────────────────────────────────────────────────

def _make_solve_callback(solver_instance):

    @CFUNCTYPE(c_int, c_void_p, c_int, c_int,
               POINTER(c_int), POINTER(c_int), POINTER(c_double),
               POINTER(c_double), POINTER(c_double), c_int)
    def callback(ctx, n, nnz, rows_p, cols_p, vals_p, x_p, b_p, with_guess):
        try:
            rows_np = np.ctypeslib.as_array(rows_p, shape=(nnz,))
            cols_np = np.ctypeslib.as_array(cols_p, shape=(nnz,))
            vals_np = np.ctypeslib.as_array(vals_p, shape=(nnz,))
            b_np = np.ctypeslib.as_array(b_p, shape=(n,))
            x_np = np.ctypeslib.as_array(x_p, shape=(n,))
            return solver_instance._solve_core(
                n, rows_np, cols_np, vals_np, b_np, x_np, bool(with_guess))
        except Exception as e:
            print(f'CudaSolver error: {e}')
            return -1

    return callback


# ── CudaSolver ────────────────────────────────────────────────────────

class CudaSolver:
    """基于 CuPy 的 GPU 稀疏求解器.

    支持 direct / cg / bicgstab / gmres / bicg 五种方法.

    Args:
        method: 求解方法 ('direct', 'cg', 'bicgstab', 'gmres', 'bicg')
        tol: 收敛容差 (仅迭代法有效，默认 1e-10)
        maxiter: 最大迭代次数 (仅迭代法有效，默认 None = CuPy 内置默认)
    """

    def __init__(self, method='direct', tol=1e-10, maxiter=None):
        self._handle = id(self)
        self._fn = _make_solve_callback(self)
        self._method = method
        self._tol = tol
        self._maxiter = maxiter

    def _solve_core(self, n, rows, cols, vals, b, x_out, with_guess):
        import cupy as cp

        vals_g = cp.asarray(vals, dtype=cp.float64)
        rows_g = cp.asarray(rows, dtype=cp.int32)
        cols_g = cp.asarray(cols, dtype=cp.int32)
        b_g = cp.asarray(b, dtype=cp.float64)

        A = cp.sparse.coo_matrix(
            (vals_g, (rows_g, cols_g)), shape=(n, n)).tocsr()

        method = self._method

        if method == 'direct':
            from cupyx.scipy.sparse.linalg import spsolve
            x_g = spsolve(A, b_g)

        elif method == 'cg':
            from cupyx.scipy.sparse.linalg import cg
            x0 = cp.asarray(x_out, dtype=cp.float64) if with_guess else None
            x_g, info = cg(A, b_g, x0=x0, tol=self._tol, maxiter=self._maxiter)
            if info != 0:
                print(f'CudaSolver CG: not converged (info={info})')
                return -1

        elif method == 'bicgstab':
            from cupyx.scipy.sparse.linalg import bicgstab
            x0 = cp.asarray(x_out, dtype=cp.float64) if with_guess else None
            x_g, info = bicgstab(A, b_g, x0=x0, tol=self._tol, maxiter=self._maxiter)
            if info != 0:
                print(f'CudaSolver BiCGSTAB: not converged (info={info})')
                return -1

        elif method == 'gmres':
            from cupyx.scipy.sparse.linalg import gmres
            x0 = cp.asarray(x_out, dtype=cp.float64) if with_guess else None
            x_g, info = gmres(A, b_g, x0=x0, tol=self._tol, maxiter=self._maxiter)
            if info != 0:
                print(f'CudaSolver GMRES: not converged (info={info})')
                return -1

        elif method == 'bicg':
            from cupyx.scipy.sparse.linalg import bicg
            x0 = cp.asarray(x_out, dtype=cp.float64) if with_guess else None
            x_g, info = bicg(A, b_g, x0=x0, tol=self._tol, maxiter=self._maxiter)
            if info != 0:
                print(f'CudaSolver BiCG: not converged (info={info})')
                return -1

        else:
            print(f'CudaSolver: unknown method {method}')
            return -2

        cp.asnumpy(x_g, out=x_out)
        return 0

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """求解 Ax = b.

        Args:
            rows, cols, vals: COO 三元组 (int32/float64)
            x: 解向量缓冲区 (in/out, float64, 长度 n)
            b: 右端项 (float64, 长度 n)
            with_guess: 是否使用 x 当前值作为迭代初值
        Returns:
            int: 0 = 成功, 非 0 = 失败
        """
        if not isinstance(rows, np.ndarray):
            rows = np.ctypeslib.as_array(rows, shape=(len(rows),))
        if not isinstance(cols, np.ndarray):
            cols = np.ctypeslib.as_array(cols, shape=(len(cols),))
        if not isinstance(vals, np.ndarray):
            vals = np.ctypeslib.as_array(vals, shape=(len(vals),))
        if not isinstance(b, np.ndarray):
            b = np.ctypeslib.as_array(b, shape=(len(b),))
        if not isinstance(x, np.ndarray):
            x = np.ctypeslib.as_array(x, shape=(len(x),))

        try:
            return self._solve_core(len(b), rows, cols, vals, b, x, with_guess)
        except Exception as e:
            print(f'CudaSolver error: {e}')
            return -1

    @property
    def fn(self):
        """FuncSol C 函数指针."""
        return self._fn

    @property
    def ctx(self):
        """上下文指针 (= id(self)), 与 fn 配对."""
        return c_void_p(self._handle)

    @property
    def handle(self):
        return self._handle

    def __repr__(self):
        return (f'{type(self).__name__}(method={self._method}, '
                f'tol={self._tol}, handle={self._handle})')
