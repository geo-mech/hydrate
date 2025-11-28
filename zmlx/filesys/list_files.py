from zmlx.alg.fsys import list_files

__all__ = ['list_files']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    for file in list_files('..', keywords=['pyc', 'plot']):
        print(file)
