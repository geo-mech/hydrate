from zmlx.alg.fsys import list_code_files

__all__ = ['list_code_files']

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)



if __name__ == '__main__':
    for file in list_code_files(path='..'):
        print(file)
