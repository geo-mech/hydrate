"""
利用0到1之间的随机数来填充Vector. 此模块主要是作为一个示例，用以说明:
    如何在c/c++中调用zml的dll函数，并加快关键的计算进程.
"""

import ctypes
import os
import zml


dll = ctypes.cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), 'fill_01.dll'))
dll.fill_01.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t)


def fill_01(v):
    dll.fill_01(v.handle, zml.dll.vector_set, zml.dll.get_rand, v.size)


def test(count):
    import timeit
    v = zml.Vector()
    v.size = count

    for step in range(5):
        t0 = timeit.default_timer()
        for i in range(v.size):
            v[i] = zml.get_rand()
        t1 = timeit.default_timer()
        fill_01(v)
        t2 = timeit.default_timer()
        print(f'cpu time. Python: {t1-t0}s, and C++: {t2-t1}s. Python/C++: {(t1-t0)/(t2-t1)}')


if __name__ == '__main__':
    test(50000)
