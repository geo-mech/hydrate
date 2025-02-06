from zmlx.filesys import opath as op


def set_output(folder=None):
    """
    设置demo执行的输出路径
    """
    op.set_opath(folder=folder, key='demo_output')


def opath(*args):
    """
    返回输出目录 (如果不成功，则返回None)
    """
    return op.opath(*args, key='demo_output')


if __name__ == '__main__':
    print(opath())
