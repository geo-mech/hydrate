import warnings

from zmlx.filesys.change_fmt import *

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        key = sys.argv[1]
        path = None
        if len(sys.argv) >= 3:
            path = sys.argv[2]
        if key == 'seepage2txt':
            seepage2txt(path)

        if key == 'txt2seepage':
            txt2seepage(path)
