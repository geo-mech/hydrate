from zmlx.io.utils import load_col
__all__ = ['load_col']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)







def test():
    text = """1 2
    3 4
    5 6
    7 8
    """
    print(load_col(index=1, text=text))


if __name__ == '__main__':
    test()
