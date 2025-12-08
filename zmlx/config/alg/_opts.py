def merge_opts(*opts, **kwargs):
    """
    合并字典，并且后面的字典会覆盖前面的字典。
    Args:
        *opts:

    Returns:
        dict
    """
    res = {}
    for opt in opts:
        if isinstance(opt, dict):
            res.update(opt)
    res.update(kwargs)
    return res


def test():
    a = dict(x=1, y=2, z=3)
    b = dict(y=4)
    c = None
    d = 123
    opts = merge_opts(a, b, c, d, q=6)
    print(opts)


if __name__ == '__main__':
    test()
