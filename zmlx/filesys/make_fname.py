from zmlx.alg.fsys import make_fname

__all__ = ['make_fname']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)



if __name__ == '__main__':
    print(make_fname(1, '.', '.txt'))
    print(make_fname(1, '.', 'txt'))
