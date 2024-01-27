from zmlx.config.japan13 import h2o_inj
from zmlx.filesys.opath import opath
from zmlx.kr.create_krf import create_krf


def test():
    h2o_inj(folder=opath('japan2013', f'test_7'),
            time_max=3600 * 24 * 6.3,
            gr=create_krf(0.15, 6, as_interp=True, k_max=1, s_max=1, count=300),
            perf_dz=-10,
            sh_min=0.6, sh_max=0.6, dt_max=100, k_times=4,
            )


if __name__ == '__main__':
    test()
