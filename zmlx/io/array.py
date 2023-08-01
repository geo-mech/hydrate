"""
导入numpy的array
"""
import os
from io import StringIO
import numpy as np
from zmlx.io.json_ex import ConfigFile


def from_json(json=None, data=None, text=None, file=None):
    """
    读取并生成numpy的array。将首先读取data，然后尝试text，最后是读取文件file，直到得到一个非空的array
    并返回。
    注意，返回的array必然是非空的；输入的参数data、text和file均为读取json的默认值，如果json中有相应
    的定义，则最终使用json中的定义。
    """
    if json is not None:
        if not isinstance(json, ConfigFile):
            json = ConfigFile(json)

    if data is None:
        data = []

    if json is not None:
        data = json(key='data', default=data,
                    doc='The data that will be converted to numpy array')

    data = np.asarray(data)

    if len(data.flatten()) > 0:
        return data

    if text is None:
        text = ''

    if json is not None:
        text = json(key='text', default=text,
                    doc='The text that will be converted to numpy array')

    if len(text) > 0:
        data = np.loadtxt(StringIO(text))

    if len(data.flatten()) > 0:
        return data

    if file is None:
        file = ''

    if json is not None:
        file = json.find_file(key='file', default=file,
                              doc='The file that will be read to numpy array')

    if os.path.isfile(file):
        data = np.loadtxt(file)
        if len(data.flatten()) > 0:
            return data
