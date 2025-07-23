import os


def get_path(*args):
    """
    返回数据目录
    """
    return os.path.join(os.path.dirname(__file__), *args)
