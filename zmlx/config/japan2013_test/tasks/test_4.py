from zmlx.config.japan13 import h2o_inj
from zmlx.filesys.opath import opath


def test_4():
    h2o_inj(folder=opath('japan2013', f'test_4'),
            time_max=3600 * 24 * 6.3
            )


if __name__ == '__main__':
    test_4()
