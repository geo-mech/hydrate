from zmlx.alg.fsys import join_paths

__all__ = ['join_paths']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15, please import from "zmlx.alg.fsys" instead',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    print(join_paths('x', 'y'))
    print(join_paths('x', 'y', None))
