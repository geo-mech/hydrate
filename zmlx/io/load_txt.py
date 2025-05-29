from zmlx.io.base import load_txt

__all__ = [
    'load_txt'
]

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)




def test():
    from io import StringIO
    text = """1 2
    3 4
    5 6
    7 8
    """
    print(load_txt(StringIO(text)))


if __name__ == '__main__':
    test()
