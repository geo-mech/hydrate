from zmlx.config.japan13 import h2o_inj
from zmlx.filesys.opath import opath
from zmlx.kr.create_krf import create_krf


def test():
    h2o_inj(folder=opath('japan2013', f'test_5'),
            time_max=3600 * 24 * 6.3,
            gr=create_krf(0.1, 10, as_interp=True, k_max=1, s_max=1, count=300)
            )


if __name__ == '__main__':
    test()
