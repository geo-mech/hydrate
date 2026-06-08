import zmlx.alg.sys as warnings

warnings.warn(f'zml will be removed after 2027-5-25, please use zmlx instead', DeprecationWarning, stacklevel=2)

from zmlx import *

if __name__ == "__main__":
    main(sys.argv)
