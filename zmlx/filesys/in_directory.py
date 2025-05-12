from zmlx.alg.fsys import in_directory

__all__ = ['in_directory']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


def test():
    file_name = r'C:\Users\zhaob\OneDrive\MyProjects\ZNetwork\projects\zml\zmlx\filesys\in_directory.py'
    directory = r'C:\Users\zhaob\OneDrive\MyProjects\ZNetwork\projects\zml'

    if in_directory(file_name, directory):
        print(f"{file_name} 在 {directory} 下或其子目录中")
    else:
        print(f"{file_name} 不在 {directory} 下或其子目录中")


if __name__ == '__main__':
    test()
