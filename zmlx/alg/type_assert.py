def type_assert(o, dtype):
    """
    类型断言

    断言给定的数据o是给定的类型dtype. 相对于assert isinstance，使用这个函数，可以显示错误。
    但是，使用此函数，PyCharm无法识别o的类型，从而无法给出类型提示.
    """
    assert isinstance(o, dtype), f'type assert failed: {dtype} required, but {type(o)} with value = {o} is given'


if __name__ == '__main__':
    type_assert('x', int)
