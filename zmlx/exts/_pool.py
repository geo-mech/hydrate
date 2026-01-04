from ctypes import c_void_p, c_int
from typing import Optional

from zmlx.exts._dll import core
from zmlx.exts._utils import HasHandle


class ThreadPool(HasHandle):
    """
    封装 zml::thread_pool_ty.
    """
    core.use(c_void_p, 'new_thread_pool', c_int)
    core.use(None, 'del_thread_pool', c_void_p)

    def __init__(self, num_threads: int = 0, handle: Optional[c_void_p] = None):
        """
        创建线程池.
        Args:
            num_threads (int, optional): 线程数量. 默认为0. 如果给定0，则由系统自动确定线程数量。
            handle (c_void_p, optional): 已有的句柄。如果提供，则忽略其他参数。
        """
        super().__init__(
            handle,
            lambda: core.new_thread_pool(num_threads),
            core.del_thread_pool)

    core.use(None, 'thread_pool_join', c_void_p)

    def join(self):
        """
        等待所有任务执行完毕，并且，终止线程池
        """
        return core.thread_pool_join(self.handle)

    core.use(None, 'thread_pool_wait', c_void_p)

    def wait(self):
        """
        等待所有任务执行完毕，并且，终止线程池
        """
        return core.thread_pool_wait(self.handle)

    core.use(None, 'thread_pool_stop', c_void_p)

    def stop(self):
        """
        停止线程池
        """
        return core.thread_pool_stop(self.handle)

    core.use(None, 'thread_pool_sync', c_void_p)

    def sync(self):
        """
        同步等待当前存在的任务 (不停止线程池，因此，线程池在后续还可以再使用)
        """
        return core.thread_pool_sync(self.handle)
