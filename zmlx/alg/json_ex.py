from json import *
import warnings


def write(path, obj, encoding=None):
    try:
        with open(path, 'w', encoding='utf-8' if encoding is None else encoding) as file:
            dump(obj, file)
    except Exception as err:
        warnings.warn(f'write json. err={err}. path={path}')


def read(path, encoding=None, default=None):
    try:
        with open(path, 'r', encoding='utf-8' if encoding is None else encoding) as file:
            return load(file)
    except Exception as err:
        warnings.warn(f'read json. err={err}. path={path}')
        return default

