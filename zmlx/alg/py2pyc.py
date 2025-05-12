import sys
import warnings

from zmlx.alg.sys import py2pyc

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        py2pyc(ipath=sys.argv[1], opath=sys.argv[2])
