from zmlx.io.base import load_col

__all__ = ['load_col']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


def test():
    text = """1 2
    3 4
    5 6
    7 8
    """
    print(load_col(index=1, text=text))


if __name__ == '__main__':
    test()
