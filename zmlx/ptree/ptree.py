import os

from zmlx.filesys.make_parent import make_parent
from zmlx.filesys.path import *
from zmlx.io.json_ex import read as read_json, write as write_json


class _Adaptor:
    def __init__(self, data=None, path=None, read=None, write=None):
        """
        关联数据/文件
        """
        if data is None and read is not None and path is not None:
            if isfile(path):
                data = read(path)

        if data is None:
            self.data = {}
        else:
            self.data = data

        self.path = path
        self.write = write

    def save(self):
        """
        保存到文件
        """
        if self.write is not None and self.path is not None and not self.data.get('readonly', False):
            self.write(self.path, self.data)

    def get(self, *args):
        """
        返回值(其中的arg应该为int或者str类型)
        """
        data = self.data
        for arg in args:
            if isinstance(data, dict):
                data = data.get(arg)
                continue
            if isinstance(data, (list, tuple)) and isinstance(arg, int):
                data = data[arg] if 0 <= arg < len(data) else None
                continue
            else:
                return
        return data

    def put(self, *args):
        """
        添加值(会覆盖已有数据). 必须确保即将添加的位置是dict，否则添加失败. 返回是否添加成功.
        """
        if len(args) == 0:
            return False
        if len(args) == 1:  # 此时，设置根目录的数据
            self.data = args[0]
            return True
        assert len(args) >= 2
        data = self.data
        for idx in range(len(args) - 2):  # 找到即将写入的dict
            if not isinstance(data, dict):  # 此时，无法添加
                return False
            key = args[idx]
            assert isinstance(key, str)
            val = data.get(key)
            if val is not None:
                data = val
            else:
                data[key] = {}
                data = data[key]
        if isinstance(data, dict):
            data[args[-2]] = args[-1]  # 执行写入
            return True
        else:
            return False

    def fill(self, *args):
        """
        当不存在的时候来添加 (确保不会覆盖原本的内容)
        """
        if len(args) == 0:
            return False
        if self.get(*args[: -1]) is None and args[-1] is not None:
            return self.put(*args)
        else:
            return False


class PTree:
    """
    配置文件
    """

    def __init__(self, ada=None, keys=None):
        """
        初始化
        """
        assert ada is None or isinstance(ada, (PTree, _Adaptor))
        if ada is None:
            self.ada = _Adaptor()
            self.keys = [] if keys is None else list(keys)
        elif isinstance(ada, PTree):
            assert isinstance(ada.ada, _Adaptor)
            self.ada = ada.ada
            self.keys = ada.keys + list(keys)
        else:
            assert isinstance(ada, _Adaptor)
            self.ada = ada
            self.keys = [] if keys is None else list(keys)
        assert isinstance(self.ada, _Adaptor)

    def get(self, *args):
        """
        返回数据
        """
        return self.ada.get(*self.keys, *args)

    def put(self, *args):
        """
        放入数据
        """
        if self.ada.put(*self.keys, *args):
            self.ada.save()
            return True
        else:
            return False

    def fill(self, *args):
        """
        在空白的位置填入数据
        """
        if self.ada.fill(*self.keys, *args):
            self.ada.save()
            return True
        else:
            return False

    @property
    def data(self):
        """
        文件数据 (self.keys所对应的分支)
        """
        return self.get()

    @data.setter
    def data(self, value):
        """
        文件数据 (self.keys所对应的分支)
        """
        self.put(value)

    @property
    def path(self):
        return self.ada.path

    def __getitem__(self, *keys):
        """
        返回其中一个分支
        """
        return PTree(ada=self, keys=keys)

    def __call__(self, *keys, cast=None, doc=None, default=None):
        """
        读取数据. 注意当给定cast的时候，将对原始的数据进行转化.
            其中default为*keys位置的默认值，当*keys位置没有数据的时候，将使用default. 此default仍然需要经过cast之后再返回.
        """
        if doc is not None and not self.ada.get('disable_doc'):
            if self.ada.fill('doc', *self.keys, *keys, doc):
                self.ada.save()

        value = self.get(*keys)
        if value is None:
            value = default
        if value is None:
            return
        if cast is None:
            return value
        else:
            return cast(value)

    def find(self, filename):
        """
        查找已经存在的文件(或者文件夹)，并且返回文路径. 确保返回的类型为str
        """
        if not isinstance(filename, str):
            return ''

        if exists(filename):
            return filename

        my_dir = dirname(self.ada.path) if isdir(dirname(self.ada.path)) else None  # 文件所在文件夹

        path = join(my_dir, filename)
        if exists(path):
            return path

        dirs = self.ada.get('search_dirs')
        if isinstance(dirs, list):
            for name in dirs:
                folder = None
                if isinstance(name, str):
                    if isdir(name):
                        folder = name
                    else:
                        path = join(my_dir, name)
                        if isdir(path):
                            folder = path
                if folder is not None:
                    path = join(folder, filename)
                    if exists(path):
                        return path

        return ''

    def opath(self, *args):
        """
        返回输出文件目录
        """
        root = self.ada.get('opath')  # 定义输出目录 (绝对路径)
        if not isinstance(root, str):
            root = None
        if root is None:
            my_dir = dirname(self.ada.path) if isdir(dirname(self.ada.path)) else None  # 文件所在文件夹
            root = my_dir if my_dir is not None else os.getcwd()
        path = join(root, *args)
        if path is not None:
            return make_parent(path)


def _open_json(filename):
    """
    将Json文件作为一个PTree来使用
    """
    return PTree(ada=_Adaptor(data=None, path=filename, read=read_json, write=write_json))


def _open_py(filename):
    """
    将Python文件作为一个PTree来使用
    """
    from zml import read_py, write_py

    def read(path):
        return read_py(path=path, data={}, encoding='utf-8', globals=None, text=None, key=None)

    return PTree(ada=_Adaptor(data=None, path=filename, read=read, write=write_py))


def open_pt(filename):
    if not isinstance(filename, str):
        return
    ext = os.path.splitext(filename)[-1]
    if ext is not None:
        if ext.lower() == '.json':
            return _open_json(filename)
        if ext.lower() == '.py' or ext.lower() == '.pyw':
            return _open_py(filename)


def as_ptree(data, path=None):
    ada = _Adaptor(data=data, path=path)
    return PTree(ada=ada)


def _test():
    pt = PTree()
    pt.data = {
        "y": 123,
        "x": 123
    }
    print(pt['y'](cast=lambda x: f'this is {x}', doc='The y'))
    print(pt['x']())
    print(pt.data)


if __name__ == '__main__':
    _test()
