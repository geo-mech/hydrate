from zmlx.config.japan13 import h2o_inj
from zmlx.filesys.opath import opath


def test_ag():
    h2o_inj(folder=opath('japan2013', f'test_ag2'),
            ag=2,
            time_max=3600 * 24 * 6.3,
            srg=0.01,
            k_times=0.1,
            krg_times=2,
            sh_min=0.1,
            sh_max=0.6,
            dt_max=100,
            # krw_times=0.1,
            # face_area_prod=0.015
            )


def test_ag3():
    h2o_inj(folder=opath('japan2013', f'test_ag3'),
            ag=2,
            time_max=3600 * 24 * 6.3,
            srg=0.01,
            k_times=0.1,
            krg_times=2,
            sh_min=0.1,
            sh_max=0.6,
            dt_max=100,
            z_offset=300,
            # krw_times=0.1,
            # face_area_prod=0.015
            )


def test_4():
    h2o_inj(folder=opath('japan2013', f'test_4'),
            time_max=3600 * 24 * 6.3
            )


if __name__ == '__main__':
    test_4()
