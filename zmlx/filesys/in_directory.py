"""已弃用的模块，请改用 zmlx.algs.fsys.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.algs.fsys import in_directory

__all__ = ['in_directory']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


def test():
    file_name = r'C:\Users\zhaob\OneDrive\MyProjects\ZNetwork\projects\zml\zmlx\filesys\in_directory.py'
    directory = r'C:\Users\zhaob\OneDrive\MyProjects\ZNetwork\projects\zml'

    if in_directory(file_name, directory):
        print(f"{file_name} 在 {directory} 下或其子目录中")
    else:
        print(f"{file_name} 不在 {directory} 下或其子目录中")


if __name__ == '__main__':
    test()
