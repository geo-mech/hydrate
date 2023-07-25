from json import *
import warnings
import os
from zmlx.filesys.join_paths import join_paths


def write(path, obj, encoding=None, indent=2):
    """
    将一个对象写入到json文件
    """
    try:
        with open(path, 'w', encoding='utf-8' if encoding is None else encoding) as file:
            dump(obj, file, indent=indent)
    except Exception as err:
        warnings.warn(f'write json. err={err}. path={path}')


def read(path, encoding=None, default=None):
    """
    从json文件中读取对象
    """
    try:
        with open(path, 'r', encoding='utf-8' if encoding is None else encoding) as file:
            return load(file)
    except Exception as err:
        warnings.warn(f'read json. err={err}. path={path}')
        return default


class Wrapper:
    def __init__(self, path=None):
        """
        关联一个Json文件
        """
        self.path = path
        self.data = {}
        if self.path is not None:
            if os.path.isfile(self.path):
                self.data = read(self.path)
                if not isinstance(self.data, dict):
                    self.data = {}

    def save(self):
        """
        保存到文件
        """
        if self.path is not None:
            write(self.path, self.data)

    def get(self, *args):
        """
        返回键值
        """
        data = self.data
        for arg in args:
            if isinstance(data, dict):
                data = data.get(arg)
            else:
                data = None
        return data

    def put(self, *args):
        """
        添加一个键值
        """
        if len(args) < 2:
            return
        data = self.data
        for idx in range(len(args) - 2):
            arg = args[idx]
            val = data.get(arg)
            if isinstance(val, dict):
                data = val
            else:
                data[arg] = {}
                data = data[arg]
        assert isinstance(data, dict)
        data[args[-2]] = args[-1]


class ConfigFile:
    """
    json输入文件(配置文件)
    """

    def __init__(self, file, keys=None):
        """
        初始化
        """
        if isinstance(file, ConfigFile):
            assert isinstance(file.keys, list)
            self.file = file.file
            self.keys = file.keys + list(keys)
        else:
            if isinstance(file, Wrapper):
                self.file = file
            else:
                self.file = Wrapper(file)
            if keys is None:
                self.keys = []
            else:
                self.keys = list(keys)

    def put(self, key, value, direct=False):
        """
        存入数据(和get对应)
        """
        if direct:
            self.file.put(*self.keys, key, value)
            self.file.save()
        else:
            self.file.put(*self.keys, key, 'value', value)
            self.file.save()

    def get(self, key, default=None, doc=None, direct=False):
        """
        读取数据(和put对应)
        """
        if direct:
            assert default is None and doc is None
            return self.file.get(*self.keys, key)

        value = self.file.get(*self.keys, key, 'value')
        if value is not None:
            if default is not None:
                if type(value) == type(default):
                    return value
            else:
                return value

        if default is None and doc is None:
            return

        self.file.put(*self.keys, key, 'value', default)
        self.file.put(*self.keys, key, 'default', default)
        self.file.put(*self.keys, key, 'type', f'{type(default)}')
        self.file.put(*self.keys, key, 'doc', doc)
        self.file.save()

        # 返回默认值
        return default

    def __call__(self, key, default=None, doc=None, direct=False):
        """
        读取数据(和put对应)
        """
        return self.get(key, default=default, doc=doc, direct=direct)

    def child(self, key, doc=None):
        """
        返回其中一个分支
        """
        assert isinstance(self.keys, list)
        config = ConfigFile(file=self.file, keys=self.keys + [key, ])
        if doc is not None:
            value = config.get('doc', direct=True)
            if value is None:
                config.put('doc', doc, direct=True)
        return config

    def __getitem__(self, key):
        """
        返回其中一个分支
        """
        return self.child(key)

    @property
    def path(self):
        """
        Json文件路径
        """
        return self.file.path

    @property
    def data(self):
        """
        Json文件数据 (self.keys所对应的分支)
        """
        return self.file.get(*self.keys)

    def as_path(self, key, default=None, doc=None, direct=False):
        """
        返回一个文件路径(以这个json所在的文件夹为根目录的相对路径)
        """
        if self.path is not None:
            if default is None:
                default = ''
            if doc is None:
                doc = 'relative file path'
            return join_paths(os.path.dirname(self.path),
                              self.get(key=key, default=default, doc=doc, direct=direct))
