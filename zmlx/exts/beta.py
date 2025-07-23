
from zml import *
import timeit

core = DllCore(dll_obj=load_cdll(name='beta.dll', first=os.path.dirname(__file__)))


def update_sand(model: Seepage, *args, **kwargs):
    model.update_sand(*args, **kwargs)


class Thread(HasHandle):
    core.use(c_void_p, 'new_thread')
    core.use(None, 'del_thread', c_void_p)

    def __init__(self, handle=None):
        super().__init__(handle, core.new_thread, core.del_thread)

    core.use(None, 'thread_join', c_void_p)

    def join(self):
        core.thread_join(self.handle)


core.use(None, 'prime_calculations')
core.use(None, 'prime_calculations_thread', c_void_p)

def prime_calculations(thread=None):
    if thread is None:
        core.prime_calculations()
    else:
        core.prime_calculations_thread(thread.handle)


core.use(c_void_p, 'new_thread_prime_calculations')

def new_thread_prime_calculations():
    return core.new_thread_prime_calculations()

def test_1():
    t0 = timeit.default_timer()
    prime_calculations()
    t1 = timeit.default_timer()
    print(t1 - t0)

    threads = []
    for i in range(8):
        threads.append(Thread())

    for step in range(1000):
        t1 = timeit.default_timer()
        for thread in threads:
            print(thread.handle)
            prime_calculations(thread)
        for thread in threads:
            thread.join()
        t2 = timeit.default_timer()
        print(t2 - t1)


if __name__ == '__main__':
    test_1()
