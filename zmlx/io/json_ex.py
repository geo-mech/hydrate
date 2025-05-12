import warnings
from json import *


def write(path, obj, encoding=None, indent=2):
    """
    将一个对象写入到json文件
    """
    try:
        with open(path, 'w',
                  encoding='utf-8' if encoding is None else encoding) as file:
            dump(obj, file, indent=indent)
    except Exception as err:
        warnings.warn(f'write json. err={err}. path={path}')


def read(path, encoding=None, default=None):
    """
    从json文件中读取对象
    """
    try:
        with open(path, 'r',
                  encoding='utf-8' if encoding is None else encoding) as file:
            return load(file)
    except Exception as err:
        warnings.warn(f'read json. err={err}. path={path}')
        return default
