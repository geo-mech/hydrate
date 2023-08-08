"""
导入numpy的array
"""
import os
from io import StringIO
import numpy as np
from zmlx.ptree.linspace import linspace


def filter_0d(data):
    if len(data.shape) == 0:
        return data.flatten()
    else:
        return data


def array(pt, data=None, text=None, file=None, doc=None):
    """
    读取并生成numpy的array。将首先读取data，然后尝试text，最后是读取文件file，直到得到一个非空的array
    并返回。
    注意，返回的array必然是非空的；输入的参数data、text和file均为读取json的默认值，如果json中有相应
    的定义，则最终使用json中的定义。
    """
    data = pt(key='data', default=data if data is not None else [],
              doc='The data that will be converted to numpy array' if doc is None else doc)

    data = np.asarray(data)

    if len(data.flatten()) > 0:
        return filter_0d(data)

    text = pt(key='text', default=text if text is not None else '',
              doc='The text that will be converted to numpy array' if doc is None else doc)

    if len(text) > 0:
        data = np.loadtxt(StringIO(text))

    if len(data.flatten()) > 0:
        return filter_0d(data)

    file = pt.find_file(key='file', default=file if file is not None else '',
                        doc='The file that will be read to numpy array' if doc is None else doc)
    assert isinstance(file, str)

    if os.path.isfile(file):
        data = np.loadtxt(file)
        if len(data.flatten()) > 0:
            return filter_0d(data)

    data = linspace(pt.child('linspace'), num=0)
    if len(data.flatten()) > 0:
        return filter_0d(data)
