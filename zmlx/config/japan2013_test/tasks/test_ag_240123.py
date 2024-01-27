from zmlx.config.japan13 import h2o_inj
from zmlx.filesys.opath import opath


def test_ag():
    h2o_inj(folder=opath('japan2013', f'test_ag'),
            ag=2,
            time_max=3600 * 24 * 6.3,
            srg=0.01,
            k_times=0.04,
            krg_times=5,
            sh_min=0.5,
            sh_max=0.5,
            dt_max=60,
            # krw_times=0.1,
            # face_area_prod=0.015
            )


if __name__ == '__main__':
    test_ag()
