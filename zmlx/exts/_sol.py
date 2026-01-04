from ctypes import c_double

from zmlx.exts._dll import core, c_void_p
from zmlx.exts._utils import HasHandle


class ConjugateGradientSolver(HasHandle):
    """
    Eigen库中共轭梯度求解器的包装类

    该类提供了对Eigen库中共轭梯度求解器的封装，允许用户设置求解器的容差，并获取当前的容差设置。
    """
    core.use(c_void_p, 'new_cg_sol')
    core.use(None, 'del_cg_sol', c_void_p)

    def __init__(self, tolerance=None, handle=None):
        """
        创建求解器

        Args:
            tolerance (float, optional): 求解器的容差。
                如果提供，将调用 `set_tolerance` 方法设置容差。默认为None。
            handle (c_void_p, optional): 求解器的句柄。
                如果提供，将使用该句柄初始化求解器。默认为None。

        Raises:
            AssertionError: 如果提供了句柄，但同时也提供了容差，将抛出此异常。
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
        """
        设置求解器的容差

        Args:
            tolerance (float): 要设置的容差。
        """
        core.cg_sol_set_tolerance(self.handle, tolerance)

    core.use(c_double, 'cg_sol_get_tolerance',
             c_void_p)

    def get_tolerance(self):
        """
        获取求解器的容差

        Returns:
            float: 当前求解器的容差。
        """
        return core.cg_sol_get_tolerance(self.handle)
