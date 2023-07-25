from io import StringIO

from zmlx.io.load_txt import load_txt


def load_col(fname=None, index=0, dtype=float, text=None):
    """
    从给定的数据文件导入一列数据。 其中index为列的编号. 和 numpy.loadtxt的主要不同，在于参数名称略有不同，另外返回值的类型不同.
    """
    if text is not None:
        fname = StringIO(text)
    assert fname is not None
    return load_txt(fname, dtype=dtype, usecols=index)


def test():
    text = """1 2
    3 4
    5 6
    7 8
    """
    print(load_col(index=1, text=text))


if __name__ == '__main__':
    test()
