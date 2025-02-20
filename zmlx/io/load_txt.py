import numpy as np


def load_txt(*args, **kwargs):
    """
    将文本读取到list (非numpy数组)。返回值类型的不同，是这个函数和 numpy.loadtxt唯一的不同.
    """
    return np.loadtxt(*args, **kwargs).tolist()


def test():
    from io import StringIO
    text = """1 2
    3 4
    5 6
    7 8
    """
    print(load_txt(StringIO(text)))


if __name__ == '__main__':
    test()
