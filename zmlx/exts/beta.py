
from zml import *
import timeit

core = DllCore(dll_obj=load_cdll(name='beta.dll', first=os.path.dirname(__file__)))


def update_sand(model: Seepage, *args, **kwargs):
    model.update_sand(*args, **kwargs)


core.use(c_int, 'prime_calculations', c_int, c_void_p, c_void_p)

def prime_calculations(n_max, pool=None, result=None):
    if isinstance(pool, ThreadPool):
        h1 = pool.handle
    else:
        h1 = 0

    if isinstance(result, Any):
        h2 = result.handle
    else:
        h2 = 0

    return core.prime_calculations(
        n_max,
        h1,
        h2,
    )

core.use(None, 'sleep_for', c_int, c_void_p)

def sleep_for(ms, pool=None):
    core.sleep_for(ms, pool.handle if isinstance(pool, ThreadPool) else 0)


def test_1():
    pool = ThreadPool(10)
    for step in range(10):
        t0 = timeit.default_timer()
        results = []
        for i in range(10):
            results.append(Any())
            prime_calculations(1000000, pool, results[-1])
        pool.sync()
        t1 = timeit.default_timer()
        print(f'time = {t1 - t0}')
        print(f'Results = {[x.get_int() for x in results]}')

if __name__ == '__main__':
    test_1()

