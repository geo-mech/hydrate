"""
尚且处于测试中的模块。在功能稳定之后，会逐步被转移到zml中。因此，这个模块，可以被视为zml模块的一个扩展（会首先导入zml中的所有内容）
"""

from zml import *

core = DllCore(dll_obj=load_cdll(name='beta.dll', first=os.path.dirname(__file__)))

core.use(c_int, 'add', c_int, c_int)
core.use(c_void_p, 'get_add_address')
core.use(c_int, 'repeat_operation', c_int, c_int, c_int, c_void_p)


def repeat_operation(func):
    if not isinstance(func, type(core.dll.repeat_operation)) and callable(func):
        func = CFUNCTYPE(c_int, c_int, c_int)(func)

    return core.repeat_operation(5, 3, 1000000, func)


def benchmark_performance():
    """性能基准测试：比较各种调用方式的性能"""
    import timeit

    def test_python_callback():
        return repeat_operation(lambda x, y: x + y)

    def test_c_to_c():
        return repeat_operation(core.dll.add)

    def test_inner():
        return repeat_operation(core.dll.get_add_address())

    tests = [
        ("Python回调给C", test_python_callback),
        ("C函数指针传递给C", test_c_to_c),
        ("内部调用", test_inner),
    ]

    for name, test_func in tests:
        print(f'测试{name}:')
        t0 = timeit.default_timer()
        res = test_func()
        print(f'结果: {res}, 耗时: {timeit.default_timer() - t0:.6f} 秒')
        print('')

    f = ctypes.cast(core.dll.get_add_address(), CFUNCTYPE(c_int, c_int, c_int))
    print(f(4, 5))


if __name__ == '__main__':
    benchmark_performance()
