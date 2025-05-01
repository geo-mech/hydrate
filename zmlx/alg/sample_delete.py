import os
import warnings

from zmlx.alg.os import sample_delete

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)



if __name__ == '__main__':
    sample_delete(os.getcwd(), count_keep=100)
