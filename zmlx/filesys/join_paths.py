import os


def join_paths(*args):
    """
    连接路径。当任意一个为None的时候，或者没有给定任何参数的时候，就返回None
    """
    for arg in args:
        if arg is None:
            return
    if len(args) > 0:
        return os.path.join(*args)


if __name__ == '__main__':
    print(join_paths('x', 'y'))
