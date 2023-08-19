from json import *
import warnings


def read_json(path, encoding=None, default=None):
    """
    从json文件中读取对象
    """
    try:
        with open(path, 'r', encoding='utf-8' if encoding is None else encoding) as file:
            return load(file)
    except Exception as err:
        warnings.warn(f'read json. err={err}. path={path}')
        return default
