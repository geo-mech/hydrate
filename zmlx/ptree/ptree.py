from zmlx.filesys.path import *
from zmlx.filesys.make_parent import make_parent
from zmlx.io.json_ex import read as read_json, write as write_json
import os

__all__ = ['PTree', 'Buffer', 'get_child', 'json_file']


class Buffer:
    def __init__(self, data=None, path=None, read=None, write=None):
        """
        关联数据/文件
        """
        self.data = data if isinstance(data, dict) else {}
        self.path = path
        self.read = read
        self.write = write
        if self.read is not None:
            if isfile(self.path):
                self.data = read(self.path)
                if not isinstance(self.data, dict):
                    self.data = {}

    def save(self):
        """
        保存到文件
        """
        assert isinstance(self.data, dict)
        try:
            readonly = self.data.get('readonly', False)
        except:
            readonly = False

        if self.write is not None and self.path is not None and not readonly:
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

    def __init__(self, buf, keys=None):
        """
        初始化
        """
        if isinstance(buf, PTree):
            self.buf = buf.buf
            self.keys = buf.keys + list(keys)
        else:
            assert isinstance(buf, Buffer)
            self.buf = buf
            self.keys = [] if keys is None else list(keys)
        assert isinstance(self.buf, Buffer)

    def put(self, key, value):
        """
        存入数据(和get对应)
        """
        assert isinstance(self.buf, Buffer)
        self.buf.put(*self.keys, key, 'value', value)
        self.buf.save()

    def get(self, key, default=None, doc=None, cast=None):
        """
        读取数据(和put对应)
        """
        assert isinstance(self.buf, Buffer)

        value = self.buf.get(*self.keys, key, 'value')
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
            self.buf.put(*self.keys, key, 'value', default)

        if default is not None or doc is not None:
            summary = f'default = {default}, type = {type(default)}, doc = {doc}'
            self.buf.put(*self.keys, key, 'doc', summary)

        self.buf.save()

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
            value = pt.buf.get(*pt.keys, 'doc')
            if value is None:
                pt.buf.put(*pt.keys, 'doc', doc)
                pt.buf.save()
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
        assert isinstance(self.buf, Buffer)
        return self.buf.path

    @property
    def folder(self):
        """
        文件所在文件夹
        """
        path = dirname(self.path)
        if isdir(path):
            return path

    @property
    def data(self):
        """
        文件数据 (self.keys所对应的分支)
        """
        assert isinstance(self.buf, Buffer)
        return self.buf.get(*self.keys) if len(self.keys) > 0 else self.buf.data

    def set_dirs(self, *args):
        """
        设置数据目录
        """
        assert isinstance(self.buf, Buffer)
        self.buf.put('data_dirs', list(args))
        self.buf.save()

    def add_dirs(self, *args):
        """
        添加数据目录
        """
        assert isinstance(self.buf, Buffer)
        if len(args) > 0:
            value = self.buf.get('data_dirs')
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
        assert isinstance(self.buf, Buffer)
        dirs = self.buf.get('data_dirs')
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
    return PTree(buf=Buffer(data=None, path=filename, read=read_json, write=write_json))
