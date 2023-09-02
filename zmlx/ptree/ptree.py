from zmlx.filesys.path import *
from zmlx.filesys.make_parent import make_parent
from zmlx.io.json_ex import read as read_json, write as write_json
from zml import app_data
import os


def remove_doc(data):
    if not isinstance(data, dict):
        return

    doc = data.get('doc', None)
    if isinstance(doc, dict):
        data.pop('doc')

    for key, val in data.items():
        remove_doc(val)


class Adaptor:
    def __init__(self, data=None, path=None, read=None, write=None):
        """
        关联数据/文件
        """
        if not isinstance(data, dict) and read is not None and isfile(path):
            data = read(path)

        if not isinstance(data, dict):
            self.data = {}
        else:
            self.data = data

        self.path = path
        self.write = write

    def save(self):
        """
        保存到文件
        """
        assert isinstance(self.data, dict)
        if self.write is not None and self.path is not None and not self.data.get('readonly', False):
            self.write(self.path, self.data)

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
        if len(args) == 0:
            return
        if len(args) == 1:
            assert isinstance(args[0], dict)
            self.data = args[0]
            return
        assert len(args) >= 2
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


class PTree:
    """
    配置文件
    """

    def __init__(self, ada, keys=None):
        """
        初始化
        """
        if isinstance(ada, PTree):
            self.ada = ada.ada
            self.keys = ada.keys + list(keys)
        else:
            assert isinstance(ada, Adaptor)
            self.ada = ada
            self.keys = [] if keys is None else list(keys)
        assert isinstance(self.ada, Adaptor)

    @property
    def data(self):
        """
        文件数据 (self.keys所对应的分支)
        """
        return self.ada.get(*self.keys)

    @data.setter
    def data(self, value):
        """
        文件数据 (self.keys所对应的分支)
        """
        assert isinstance(value, dict)
        self.ada.put(*self.keys, value)
        self.ada.save()

    def remove_doc(self):
        """
        删除所有的doc
        """
        remove_doc(self.data)
        self.ada.save()

    def put(self, key, value):
        """
        存入数据(和get对应)
        """
        assert isinstance(self.ada, Adaptor)
        self.ada.put(*self.keys, key, value)
        self.ada.save()

    def get(self, key, default=None, doc=None, cast=None):
        """
        读取数据(和put对应)
        """
        assert isinstance(self.ada, Adaptor)

        if doc is not None:
            if self.ada.get(*self.keys, 'doc', key) is None:
                self.ada.put(*self.keys, 'doc', key, doc)
                self.ada.save()

        value = self.ada.get(*self.keys, key)
        if value is not None:
            if cast is None:
                return value
            else:
                try:
                    return cast(value)
                except:
                    pass

        if default is None and doc is None:
            return

        if default is not None:
            self.ada.put(*self.keys, key, default)
            self.ada.save()

        if default is not None:
            if cast is None:
                return default
            else:
                try:
                    return cast(default)
                except:
                    pass

    def __call__(self, key, default=None, doc=None, cast=None):
        """
        读取数据(和put对应)
        """
        return self.get(key, default=default, doc=doc, cast=cast)

    def child(self, key, doc=None):
        """
        返回其中一个分支
        """
        assert isinstance(self.keys, list)
        pt = PTree(self, [key, ])
        if doc is not None:
            value = self.ada.get(*self.keys, 'doc', key)
            if value is None:
                self.ada.put(*self.keys, 'doc', key, doc)
                self.ada.save()
        return pt

    def __getitem__(self, key):
        """
        返回其中一个分支
        """
        return self.child(key)

    @property
    def path(self):
        """
        文件路径
        """
        assert isinstance(self.ada, Adaptor)
        return self.ada.path

    @property
    def folder(self):
        """
        文件所在文件夹
        """
        path = dirname(self.path)
        if isdir(path):
            return path

    def set_dirs(self, *args):
        """
        设置数据目录
        """
        assert isinstance(self.ada, Adaptor)
        self.ada.put('data_dirs', list(args))
        self.ada.save()

    def add_dirs(self, *args):
        """
        添加数据目录
        """
        assert isinstance(self.ada, Adaptor)
        if len(args) > 0:
            value = self.ada.get('data_dirs')
            if not isinstance(value, list):
                value = []
            count = 0
            for name in args:
                if isinstance(name, str):
                    value.append(name)
                    count += 1
            if count > 0:
                self.set_dirs(*value)

    def get_dirs(self):
        """
        返回数据目录(确保返回的目录必然是存在的)
        """
        assert isinstance(self.ada, Adaptor)
        dirs = self.ada.get('data_dirs')
        if isinstance(dirs, list):
            folders = []
            for name in dirs:
                if isinstance(name, str):
                    if isdir(name):
                        folders.append(name)
                    else:
                        path = join(self.folder, name)
                        if isdir(path):
                            folders.append(path)
            return folders

    def find_file(self, filename=None, key=None, default=None, doc=None):
        """
        查找已经存在的文件(或者文件夹)，并且返回文路径. 确保返回的类型为str
        """
        if filename is None:
            if key is not None:
                if default is None:
                    default = ''
                filename = self.get(key=key, default=default, doc=doc)

        if filename is None:
            return ''

        if isinstance(self.folder, str):
            path = join(self.folder, filename)
            if exists(path):
                return path

        dirs = self.get_dirs()
        if dirs is not None:
            for folder in dirs:
                path = join(folder, filename)
                assert path is not None
                if exists(path):
                    return path

        path = app_data.find(filename)
        if path is not None:
            if exists(path):
                return path

        return ''

    def opath(self, *args):
        """
        返回输出文件目录
        """
        root = self.folder if self.folder is not None else os.getcwd()
        path = join(root, *args)
        if path is not None:
            return make_parent(path)


def get_child(pt, key, doc=None):
    if pt is not None:
        return pt.child(key=key, doc=doc)


def json_file(filename):
    """
    将Json文件作为一个PTree来使用
    """
    return PTree(ada=Adaptor(data=None, path=filename, read=read_json, write=write_json))


def python_file(filename):
    """
    将Python文件作为一个PTree来使用
    """
    from zml import read_py, write_py

    def read(path):
        return read_py(path=path, data={}, encoding='utf-8', globals=None, text=None, key=None)

    return PTree(ada=Adaptor(data=None, path=filename, read=read, write=write_py))


def open_pt(filename):
    ext = os.path.splitext(filename)[-1]
    if ext is not None:
        if ext.lower() == '.json':
            return json_file(filename)
        if ext.lower() == '.py' or ext.lower() == '.pyw':
            return python_file(filename)

