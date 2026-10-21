"""JSON 扩展读写（增强的错误处理）.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from json import *


from zmlx.exts import make_parent


def write(path, obj, encoding=None, indent=2):
    """
    将一个对象写入到json文件
    """
    try:
        make_parent(path)  # 确保父目录存在
        with open(path, 'w',
                  encoding='utf-8' if encoding is None else encoding) as file:
            dump(obj, file, indent=indent)
    except Exception as err:
        warn(f'write json. err={err}. path={path}')


def read(path, encoding=None, default=None):
    """
    从json文件中读取对象
    """
    try:
        with open(path, 'r',
                  encoding='utf-8' if encoding is None else encoding) as file:
            return load(file)
    except Exception as err:
        warn(f'read json. err={err}. path={path}')
        return default
