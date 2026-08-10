"""Intel MKL PARDISO 直接求解器 Python 封装.

通过独立的 pardiso.dll 提供 PARDISO 稀疏直接求解器,
与 zml.dll 无依赖. 支持 SPD (mtype=2, LDL^T) 和通用 (mtype=11, LU) 模式.

使用方式:
    from zmlx.exts.pardiso import PARDISOSolver
    solver = PARDISOSolver()           # 默认 SPD 模式
    err = solver.solve(rows, cols, vals, x, b)

    # 作为 FuncSol callback 使用:
    # solver.fn  → C 函数指针
    # solver.ctx → 上下文指针 (solver.handle)
"""

import ctypes
import os
import sys
from ctypes import c_double, c_int, c_void_p, POINTER, cast

from zmlx.exts._sol import FuncSol

# ── DLL 加载 ──────────────────────────────────────────────────────────

def _find_mkl_bin():
    """查找 MKL 运行时 DLL 所在目录."""
    # 1. conda/pip mkl
    lib = os.path.join(sys.prefix, 'Library', 'bin')
    dll = os.path.join(lib, 'mkl_rt.3.dll')
    if os.path.isfile(dll):
        return lib

    # 2. pip mkl (site-packages/mkl/Library/bin/)
    for sp in sys.path:
        for name in ('mkl_rt.3.dll', 'mkl_rt.2.dll', 'mkl_rt.1.dll'):
            p = os.path.join(sp, 'mkl', 'Library', 'bin', name)
            if os.path.isfile(p):
                return os.path.dirname(p)

    # 3. %MKLROOT%
    mklroot = os.environ.get('MKLROOT', '')
    if mklroot:
        for sub in ('bin',):
            d = os.path.join(mklroot, sub)
            if os.path.isdir(d):
                return d

    return None


def _preload_mkl():
    """预加载 MKL 运行时 DLL, 确保 pardiso.dll 能找到依赖."""
    mkl_bin = _find_mkl_bin()
    if mkl_bin is not None:
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(mkl_bin)
            except OSError:
                pass
        for name in ('mkl_rt.3.dll', 'mkl_rt.2.dll', 'mkl_rt.1.dll'):
            p = os.path.join(mkl_bin, name)
            if os.path.isfile(p):
                try:
                    ctypes.CDLL(p)
                except OSError:
                    pass
                return mkl_bin


def _load_pardiso_dll():
    """加载 pardiso.dll."""
    _preload_mkl()
    here = os.path.dirname(os.path.realpath(__file__))
    dll_path = os.path.join(here, 'pardiso.dll')
    if not os.path.isfile(dll_path):
        dll_path = 'pardiso.dll'  # try system search
    try:
        return ctypes.CDLL(dll_path)
    except OSError as e:
        import warnings
        warnings.warn(f'Cannot load pardiso.dll: {e}')
        return None


_dll = _load_pardiso_dll()

# ── PARDISOSolver ─────────────────────────────────────────────────────

class PARDISOSolver:
    """Intel MKL PARDISO 稀疏直接求解器.

    支持两种矩阵类型:
    - mtype=2  (默认): SPD → LDL^T 分解
    - mtype=11:        一般非对称 → LU 分解

    Args:
        mtype: 矩阵类型, 2=SPD, 11=general.
        msglvl: PARDISO 消息级别 (0=静默, 1=统计信息).
        handle: 已存在的 C 侧求解器句柄.
    """

    def __init__(self, mtype=2, msglvl=0, handle=None):
        self._mtype = mtype
        if handle is not None:
            self._handle = handle
        elif _dll is not None:
            fn = _dll.new_pardiso_sol
            fn.restype = c_void_p
            fn.argtypes = [c_int]
            self._handle = fn(mtype)
            if self._handle is not None and msglvl != 0:
                _dll.pardiso_sol_set_msglvl(self._handle, msglvl)
        else:
            self._handle = None

    @property
    def handle(self):
        """C 侧求解器句柄 (opaque pointer)."""
        return self._handle

    @property
    def fn(self):
        """FuncSol C 函数指针, 用于传递给需要 solver callback 的底层函数."""
        if _dll is None:
            return None
        return cast(_dll.pardiso_sol_solve, FuncSol)

    @property
    def ctx(self):
        """上下文指针, 与 fn 配对传递给 C callback 的 ctx 参数."""
        return self._handle

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """求解 Ax = b (直接法, 忽略 with_guess).

        Args:
            rows: COO 行索引 (int32, 长度 nnz)
            cols: COO 列索引 (int32, 长度 nnz)
            vals: 稀疏矩阵值 (float64, 长度 nnz)
            x: 解向量 (in/out, float64, 长度 n)
            b: 右端项 (float64, 长度 n)
            with_guess: 忽略 (直接法不使用初值)

        Returns:
            int: 0 = 成功, 非 0 = 失败.
        """
        if _dll is None:
            return -999
        fn = _dll.pardiso_sol_solve
        fn.restype = c_int
        fn.argtypes = [c_void_p, c_int, c_int,
                       POINTER(c_int), POINTER(c_int), POINTER(c_double),
                       POINTER(c_double), POINTER(c_double), c_int]
        return fn(self._handle,
                  len(b), len(rows),
                  rows, cols, vals, x, b,
                  1 if with_guess else 0)

    def __del__(self):
        if _dll is not None and self._handle is not None:
            try:
                fn = _dll.del_pardiso_sol
                fn.restype = None
                fn.argtypes = [c_void_p]
                fn(self._handle)
            except Exception:
                pass
            self._handle = None

    def __repr__(self):
        mode = 'SPD' if self._mtype == 2 else 'general'
        return (f'{type(self).__name__}(mtype={self._mtype} ({mode}), '
                f'handle={self._handle})')
