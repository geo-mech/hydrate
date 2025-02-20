from zmlx.io.path import get_path, set_path


def set_output(folder=None):
    """
    设置demo执行的输出路径
    """
    set_path(folder=folder, key='demo_output')


def opath(*args):
    """
    返回输出目录 (如果不成功，则返回None)
    """
    return get_path(*args, key='demo_output')


if __name__ == '__main__':
    print(opath())
