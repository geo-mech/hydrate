"""线性求解器模块 (Linear Solvers).

提供 6 种 Eigen 稀疏线性求解器的 Python 封装:
- 直接法: SparseLU, SimplicialLDLT
- 迭代法: ConjugateGradient, ICCG (预条件 CG), BiCGSTAB, ILU-BiCGSTAB

所有求解器统一通过 C callback 模式与 zml.dll 通信:
  solver.fn   → C 函数指针 (FuncSol 类型)
  solver.ctx  → 上下文指针 (传递给 fn 的第一个参数)

使用示例:
    solver = ConjugateGradientSolver(tolerance=1e-10)
    err = solver.solve(rows, cols, vals, x, b)
    # 或将 fn/ctx 传递给需要 solver callback 的底层函数
"""

from ctypes import c_double, c_int, c_void_p, cast, CFUNCTYPE, POINTER

from zmlx.exts._dll import core
from zmlx.exts._utils import HasHandle

# ===========================================================================
# C callback 类型定义
# ===========================================================================

# FuncSol 是 zml.dll 中 c_solver_ty 对应的 C 函数指针类型.
#
# C 侧签名:
#   int solve(void* ctx,           // 求解器实例指针 (solver.handle)
#             int n,               // 方程数量 (矩阵维度)
#             int nnz,             // 非零元个数 (CSR 三元组长度)
#             const int* rows,     // CSR 行偏移数组 (长度 nnz)
#             const int* cols,     // CSR 列索引数组 (长度 nnz)
#             const double* vals,  // CSR 数值数组 (长度 nnz)
#             double* x,           // 解向量 (长度 n, in/out)
#             const double* b,     // 右端项 (长度 n)
#             int with_guess)      // 是否使用 x 中的初值 (1=是, 0=否)
#
# 返回值: 0 = 成功, 非 0 = 失败/不收敛
#
# 通过 solver.fn 获取该类型的函数指针, solver.ctx 获取上下文指针,
# 二者组成一对传递给需要 solver callback 的底层 C 函数.

FuncSol = CFUNCTYPE(
    c_int,                  # 返回值: 0=成功
    c_void_p,               # ctx: 求解器实例句柄
    c_int,                  # n: 方程数
    c_int,                  # nnz: 非零元个数
    POINTER(c_int),         # rows: CSR 行偏移
    POINTER(c_int),         # cols: CSR 列索引
    POINTER(c_double),      # vals: CSR 值
    POINTER(c_double),      # x: 解向量 (in/out)
    POINTER(c_double),      # b: 右端项
    c_int                   # with_guess: 1=使用初值
)


# ===========================================================================
# SparseLU — 通用 LU 直接分解
# ===========================================================================

class SparseLUSolver(HasHandle):
    """Eigen SparseLU 直接求解器.

    基于 Eigen::SparseLU 实现, 通过 LU 分解直接求解 Ax=b.

    特点:
    - 结果精确到机器精度 (不依赖迭代收敛)
    - 适用于任意方阵, 不要求对称或正定
    - 不需要设置容差和初值 (with_guess 参数被忽略)
    - 适用于小到中等规模问题 (n < 1e4), 大规模问题建议用迭代法

    与 ConjugateGradientSolver 的区别:
    - 直接法: 一次分解, 精确求解, 内存占用大
    - 迭代法: 逐步逼近, 速度快, 但依赖矩阵条件和初值
    """

    # DLL 函数注册
    core.use(c_void_p, 'new_lu_sol')           # 创建 SparseLU 实例
    core.use(None, 'del_lu_sol', c_void_p)     # 销毁实例

    def __init__(self, handle=None):
        """创建 LU 直接求解器.

        Args:
            handle: 已存在的 C 侧求解器句柄 (通常由 DLL 内部创建).
                    为 None 时自动创建新实例.
        """
        super().__init__(handle, core.new_lu_sol, core.del_lu_sol)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)})'

    # solve 函数注册
    core.use(c_int, 'lu_sol_solve',
             c_void_p, c_int, c_int,
             POINTER(c_int), POINTER(c_int), POINTER(c_double),
             POINTER(c_double), POINTER(c_double), c_int)

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """直接求解 Ax = b (LU 分解).

        Args:
            rows: CSR 行偏移数组 (np.ndarray, dtype=int32, 长度 nnz)
            cols: CSR 列索引数组 (np.ndarray, dtype=int32, 长度 nnz)
            vals: CSR 数值数组 (np.ndarray, dtype=float64, 长度 nnz)
            x: 解向量 (np.ndarray, dtype=float64, 长度 n).
               直接法忽略 with_guess, x 被覆盖为精确解.
            b: 右端项向量 (np.ndarray, dtype=float64, 长度 n)
            with_guess: 已忽略. 直接法不使用初值.

        Returns:
            int: 0 表示成功.
        """
        return core.lu_sol_solve(
            self.handle,
            len(b), len(rows),
            rows, cols, vals, x, b,
            1 if with_guess else 0
        )

    @property
    def fn(self):
        """C 函数指针, 用于传递给需要 solver callback 的底层函数.

        Returns:
            FuncSol: self.solve 对应的 C 函数指针.
        """
        return cast(core.dll.lu_sol_solve, FuncSol)

    @property
    def ctx(self):
        """上下文指针, 与 fn 配对传递给 C callback 的 ctx 参数.

        Returns:
            c_void_p: 当前求解器实例的句柄.
        """
        return self.handle


# ===========================================================================
# SimplicialLDLT — 对称正定 LDL^T 分解
# ===========================================================================

class SimplicialLDLTSolver(HasHandle):
    """Eigen SimplicialLDLT 稀疏 Cholesky 直接求解器.

    基于 LDL^T 分解, 比 SparseLU 快 2-5 倍, 但仅适用于对称正定 (SPD) 矩阵.

    典型应用:
    - FEM 刚度矩阵 (Ku = f)
    - 渗流压力泊松方程 (∇·(k∇p) = q)
    - 任何经过对称正定性验证的矩阵

    限制:
    - 矩阵必须是对称正定的, 否则分解失败或结果错误
    - 同样适用于小到中等规模 (n < 1e4)
    """

    core.use(c_void_p, 'new_ldlt_sol')
    core.use(None, 'del_ldlt_sol', c_void_p)

    def __init__(self, handle=None):
        """创建 LDLT 直接求解器.

        Args:
            handle: 已存在的求解器句柄.
        """
        super().__init__(handle, core.new_ldlt_sol, core.del_ldlt_sol)

    def __repr__(self):
        return f'{type(self).__name__}(handle={int(self.handle)})'

    core.use(
        c_int, 'ldlt_sol_solve',
        c_void_p, c_int, c_int,
        POINTER(c_int), POINTER(c_int), POINTER(c_double),
        POINTER(c_double), POINTER(c_double), c_int)

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """直接求解 Ax = b (LDL^T 分解).

        Args:
            rows, cols, vals: CSR 三元组数组 (长度 nnz)
            x: 解向量 (in/out, 长度 n). 直接法忽略 with_guess.
            b: 右端项 (长度 n)
            with_guess: 已忽略.

        Returns:
            int: 0 表示成功.
        """
        return core.ldlt_sol_solve(
            self.handle,
            len(b), len(rows),
            rows, cols, vals, x, b,
            1 if with_guess else 0)

    @property
    def fn(self):
        """C 函数指针 (FuncSol)."""
        return cast(core.dll.ldlt_sol_solve, FuncSol)

    @property
    def ctx(self):
        """上下文指针 (求解器句柄)."""
        return self.handle


# ===========================================================================
# BiCGSTAB — 双共轭梯度稳定化 (非对称)
# ===========================================================================

class BiCGSTABSolver(HasHandle):
    """Eigen BiCGSTAB 迭代求解器.

    双共轭梯度稳定化方法, 适用于一般非对称方阵.

    适用场景:
    - 对流主导的输运问题 (非对称矩阵)
    - CG/ICCG 不收敛时作为备选

    与 CG 的区别:
    - CG: 仅适用于 SPD 矩阵, 收敛更快 (对于 SPD)
    - BiCGSTAB: 适用于任意方阵, 但每次迭代代价更高
    """

    core.use(c_void_p, 'new_bicgstab_sol')
    core.use(None, 'del_bicgstab_sol', c_void_p)

    def __init__(self, tolerance=None, handle=None):
        """创建 BiCGSTAB 求解器.

        Args:
            tolerance: 收敛容差 (默认使用 Eigen 内置默认值, 约 1e-6).
            handle: 已存在的求解器句柄. 如果提供, tolerance 必须为 None.
        """
        super().__init__(handle, core.new_bicgstab_sol,
                         core.del_bicgstab_sol)
        if handle is None:
            if tolerance is not None:
                self.set_tolerance(tolerance)
        else:
            assert tolerance is None

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'tolerance={self.get_tolerance()})')

    core.use(None, 'bicgstab_sol_set_tolerance', c_void_p, c_double)

    def set_tolerance(self, tolerance):
        """设置收敛容差.

        Args:
            tolerance: 残差范数阈值. 越小精度越高但迭代次数越多.
        """
        core.bicgstab_sol_set_tolerance(self.handle, tolerance)

    core.use(c_double, 'bicgstab_sol_get_tolerance', c_void_p)

    def get_tolerance(self):
        """获取当前容差."""
        return core.bicgstab_sol_get_tolerance(self.handle)

    core.use(c_int, 'bicgstab_sol_solve',
             c_void_p, c_int, c_int,
             POINTER(c_int), POINTER(c_int), POINTER(c_double),
             POINTER(c_double), POINTER(c_double), c_int)

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """迭代求解 Ax = b.

        Args:
            rows, cols, vals: CSR 三元组 (长度 nnz)
            x: 解向量 (in/out, 长度 n). with_guess=True 时使用其中值作初值.
            b: 右端项 (长度 n)
            with_guess: 是否使用 x 的当前值作为迭代初值.

        Returns:
            int: 0 = 收敛成功, 非 0 = 不收敛.
        """
        return core.bicgstab_sol_solve(
            self.handle,
            len(b), len(rows),
            rows, cols, vals, x, b,
            1 if with_guess else 0
        )

    @property
    def fn(self):
        """C 函数指针 (FuncSol)."""
        return cast(core.dll.bicgstab_sol_solve, FuncSol)

    @property
    def ctx(self):
        """上下文指针 (求解器句柄)."""
        return self.handle


# ===========================================================================
# ILU-BiCGSTAB — 不完全 LU 预条件 BiCGSTAB
# ===========================================================================

class ILUBiCGSTABSolver(HasHandle):
    """ILUT 预条件 BiCGSTAB 迭代求解器.

    ILU (Incomplete LU) 预条件 + BiCGSTAB, 比普通 BiCGSTAB 收敛快 5-50 倍.

    调节参数:
    - tolerance: 收敛容差
    - droptol: ILU 分解时的丢弃容差 (控制预条件器的稀疏度)
    - fillfactor: ILU 填充因子 (控制内存占用, 默认 ~5-10)

    典型使用:
        solver = ILUBiCGSTABSolver(tolerance=1e-10, droptol=1e-3, fillfactor=5)
    """

    core.use(c_void_p, 'new_ilu_bicgstab_sol')
    core.use(None, 'del_ilu_bicgstab_sol', c_void_p)

    def __init__(self, tolerance=None, droptol=None, fillfactor=None, handle=None):
        """创建 ILU-BiCGSTAB 求解器.

        Args:
            tolerance: 收敛容差.
            droptol: ILU 丢弃容差, 控制预条件器稀疏度. 典型值 1e-2 ~ 1e-4.
            fillfactor: ILU 填充因子, 控制预条件器内存. 典型值 3~10.
            handle: 已存在的求解器句柄.
        """
        super().__init__(handle, core.new_ilu_bicgstab_sol,
                         core.del_ilu_bicgstab_sol)
        if handle is None:
            if tolerance is not None:
                self.set_tolerance(tolerance)
            if droptol is not None:
                self.set_droptol(droptol)
            if fillfactor is not None:
                self.set_fillfactor(fillfactor)
        else:
            assert tolerance is None and droptol is None and fillfactor is None

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'tolerance={self.get_tolerance()})')

    core.use(None, 'ilu_bicgstab_sol_set_tolerance', c_void_p, c_double)
    core.use(c_double, 'ilu_bicgstab_sol_get_tolerance', c_void_p)

    def set_tolerance(self, v):
        """设置收敛容差."""
        core.ilu_bicgstab_sol_set_tolerance(self.handle, v)

    def get_tolerance(self):
        """获取当前容差."""
        return core.ilu_bicgstab_sol_get_tolerance(self.handle)

    core.use(None, 'ilu_bicgstab_sol_set_droptol', c_void_p, c_double)

    def set_droptol(self, v):
        """设置 ILU 丢弃容差 (控制预条件器稀疏度)."""
        core.ilu_bicgstab_sol_set_droptol(self.handle, v)

    core.use(None, 'ilu_bicgstab_sol_set_fillfactor', c_void_p, c_int)

    def set_fillfactor(self, v):
        """设置 ILU 填充因子 (控制预条件器内存)."""
        core.ilu_bicgstab_sol_set_fillfactor(self.handle, v)

    core.use(c_int, 'ilu_bicgstab_sol_solve',
             c_void_p, c_int, c_int,
             POINTER(c_int), POINTER(c_int), POINTER(c_double),
             POINTER(c_double), POINTER(c_double), c_int)

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """ILU 预条件 BiCGSTAB 求解.

        Args:
            rows, cols, vals: CSR 三元组 (长度 nnz)
            x: 解向量 (in/out, 长度 n)
            b: 右端项 (长度 n)
            with_guess: 是否使用 x 作为初值.

        Returns:
            int: 0 = 收敛.
        """
        return core.ilu_bicgstab_sol_solve(
            self.handle,
            len(b), len(rows),
            rows, cols, vals, x, b,
            1 if with_guess else 0)

    @property
    def fn(self):
        """C 函数指针 (FuncSol)."""
        return cast(core.dll.ilu_bicgstab_sol_solve, FuncSol)

    @property
    def ctx(self):
        """上下文指针 (求解器句柄)."""
        return self.handle


# ===========================================================================
# ConjugateGradient — 共轭梯度 (SPD)
# ===========================================================================

class ConjugateGradientSolver(HasHandle):
    """Eigen 共轭梯度 (CG) 迭代求解器.

    适用于对称正定 (SPD) 稀疏矩阵的标准迭代法.

    特点:
    - 每次迭代代价低 (仅一次矩阵-向量乘)
    - 收敛速度取决于条件数 (条件数越小越快)
    - 仅适用于 SPD 矩阵, 否则可能发散

    典型应用: 压力泊松方程, 热传导, 扩散方程.
    """

    core.use(c_void_p, 'new_cg_sol')
    core.use(None, 'del_cg_sol', c_void_p)

    def __init__(self, tolerance=None, handle=None):
        """创建 CG 求解器.

        Args:
            tolerance: 收敛容差 (默认 ~1e-6).
            handle: 已存在的求解器句柄.
        """
        super().__init__(handle, core.new_cg_sol,
                         core.del_cg_sol)
        if handle is None:
            if tolerance is not None:
                self.set_tolerance(tolerance)
        else:
            assert tolerance is None

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'tolerance={self.get_tolerance()})')

    core.use(None, 'cg_sol_set_tolerance',
             c_void_p, c_double)

    def set_tolerance(self, tolerance):
        """设置收敛容差.

        Args:
            tolerance: 残差范数阈值.
        """
        core.cg_sol_set_tolerance(self.handle, tolerance)

    core.use(c_double, 'cg_sol_get_tolerance', c_void_p)
    core.use(c_int, 'cg_sol_solve',
             c_void_p, c_int, c_int,
             POINTER(c_int), POINTER(c_int), POINTER(c_double),
             POINTER(c_double), POINTER(c_double), c_int)

    def get_tolerance(self):
        """获取当前容差."""
        return core.cg_sol_get_tolerance(self.handle)

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """CG 迭代求解 Ax = b.

        Args:
            rows, cols, vals: CSR 三元组 (长度 nnz)
            x: 解向量 (in/out, 长度 n)
            b: 右端项 (长度 n)
            with_guess: 是否使用 x 当前值作为初值.

        Returns:
            int: 0 = 收敛成功.
        """
        return core.cg_sol_solve(
            self.handle,
            len(b), len(rows),
            rows, cols, vals, x, b,
            1 if with_guess else 0
        )

    @property
    def fn(self):
        """C 函数指针 (FuncSol)."""
        return cast(core.dll.cg_sol_solve, FuncSol)

    @property
    def ctx(self):
        """上下文指针 (求解器句柄)."""
        return self.handle


# ===========================================================================
# ICCG — 不完全 Cholesky 预条件 CG
# ===========================================================================

class ICCGSolver(HasHandle):
    """ICCG = Incomplete Cholesky 预条件共轭梯度.

    比普通 CG 收敛快 5-50 倍, 用于病态 SPD 矩阵.

    原理:
    - 对矩阵 A 做不完全 Cholesky 分解: A ≈ LL^T
    - 用 L^{-1} A L^{-T} 替代 A 进行 CG 迭代
    - 近似分解大幅改善条件数, 加速收敛

    shift 参数:
    - 控制 IC 分解的正则化强度
    - 典型值 ~1e-3 (正值增加稳定性, 但降低预条件器精度)
    - 分解失败时 (负对角线) 尝试增大 shift

    典型应用:
    - FEM 刚度矩阵 (病态时 CG 收敛极慢)
    - 强非均质多孔介质渗流 (渗透率对比度 > 1e6)
    """

    core.use(c_void_p, 'new_iccg_sol')
    core.use(None, 'del_iccg_sol', c_void_p)

    def __init__(self, tolerance=None, shift=None, handle=None):
        """创建 ICCG 求解器.

        Args:
            tolerance: 收敛容差.
            shift: IC 正则化参数 (~1e-3). 分解失败时尝试增大.
            handle: 已存在的求解器句柄.
        """
        super().__init__(handle, core.new_iccg_sol, core.del_iccg_sol)
        if handle is None:
            if tolerance is not None:
                self.set_tolerance(tolerance)
            if shift is not None:
                self.set_shift(shift)
        else:
            assert tolerance is None and shift is None

    def __repr__(self):
        return (f'{type(self).__name__}(handle={int(self.handle)}, '
                f'tolerance={self.get_tolerance()})')

    core.use(None, 'iccg_sol_set_tolerance', c_void_p, c_double)
    core.use(c_double, 'iccg_sol_get_tolerance', c_void_p)

    def set_tolerance(self, v):
        """设置收敛容差."""
        core.iccg_sol_set_tolerance(self.handle, v)

    def get_tolerance(self):
        """获取当前容差."""
        return core.iccg_sol_get_tolerance(self.handle)

    core.use(None, 'iccg_sol_set_shift', c_void_p, c_double)

    def set_shift(self, v):
        """设置 IC 正则化参数.

        Args:
            v: shift 值 (~1e-3). 增大可提高稳定性但降低收敛速度.
        """
        core.iccg_sol_set_shift(self.handle, v)

    core.use(c_int, 'iccg_sol_solve',
             c_void_p, c_int, c_int,
             POINTER(c_int), POINTER(c_int), POINTER(c_double),
             POINTER(c_double), POINTER(c_double), c_int)

    def solve(self, rows, cols, vals, x, b, with_guess=False):
        """IC 预条件 CG 求解.

        Args:
            rows, cols, vals: CSR 三元组 (长度 nnz)
            x: 解向量 (in/out, 长度 n)
            b: 右端项 (长度 n)
            with_guess: 是否使用 x 作为初值.

        Returns:
            int: 0 = 收敛.
        """
        return core.iccg_sol_solve(
            self.handle,
            len(b), len(rows),
            rows, cols, vals, x, b,
            1 if with_guess else 0)

    @property
    def fn(self):
        """C 函数指针 (FuncSol)."""
        return cast(core.dll.iccg_sol_solve, FuncSol)

    @property
    def ctx(self):
        """上下文指针 (求解器句柄)."""
        return self.handle
