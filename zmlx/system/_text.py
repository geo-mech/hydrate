import os
from typing import Optional

from zmlx.system._fsys import make_dirs


def read_text(path: str, encoding: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
    """从文本文件中读取内容。

    Args:
        path (str): 目标文件路径
        encoding (str, optional): 文件编码格式，默认使用系统编码
        default (Any, optional): 读取失败时的默认返回值，默认为None

    Returns:
        Optional[str]: 成功时返回文件内容字符串，失败返回default值

    Note:
        - 自动处理文件不存在的情况
        - 静默处理所有I/O异常
        - 支持任意文本编码格式
    """
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        return default
    except:
        return default


def write_text(path: str, text: Optional[str] = None, encoding: Optional[str] = None):
    """将文本内容写入指定文件。

    Args:
        path (str): 目标文件路径
        text (str, optional): 要写入的文本内容，默认为None(写入空字符串)
        encoding (str, optional): 文件编码格式，默认使用系统编码

    Note:
        - 自动创建不存在的父目录
        - 静默处理所有I/O异常
        - 当text为None时写入空字符串
        - 使用原子写操作避免数据损坏
    """
    folder = os.path.dirname(path)
    if len(folder) > 0 and not os.path.isdir(folder):
        make_dirs(folder)
    with open(path, 'w', encoding=encoding) as f:
        if text is None:
            f.write('')
        else:
            f.write(text)
