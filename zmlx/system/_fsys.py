import os
from typing import Optional


def make_dirs(folder: Optional[str] = None):
    """递归创建目录结构。

    Args:
        folder (str, optional): 要创建的目录路径

    Note:
        - 自动创建所有不存在的父目录
        - 使用exist_ok参数避免目录已存在的错误
        - 包含异常处理，失败时静默退出
    """
    try:
        if folder is not None:
            if not os.path.isdir(folder):
                os.makedirs(folder, exist_ok=True)
    except:
        pass


def make_parent(path: str) -> str:
    """确保指定文件路径的父目录存在。

    Args:
        path (str): 文件路径

    Returns:
        str: 原始输入路径

    Note:
        - 通过调用make_dirs实现目录创建
        - 始终返回输入路径以便链式调用
        - 包含异常处理机制保证程序健壮性
    """
    try:
        name = os.path.dirname(path)
        if not os.path.isdir(name):
            make_dirs(name)
        return path
    except:
        return path
