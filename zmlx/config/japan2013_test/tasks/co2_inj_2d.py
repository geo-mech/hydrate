from zmlx.config.japan13 import co2_inj
from zmlx.filesys.opath import opath

if __name__ == '__main__':
    co2_inj(root_folder=opath('japan2013'), q_inj=1.0e4, dim=2)
