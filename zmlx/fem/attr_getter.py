def attr_getter(index, left, right, default=None):
    """
    用以生成获取属性的函数.
    Args:
        index: 索引
        left: 左边界
        right: 右边界
        default: 默认值
    Returns:
        一个函数，该函数接受一个对象，返回该对象的属性值. 如果属性值不在[left, right]之间，则返回default.
        如果index为None，则返回一个函数，该函数总是返回default.
    """
    if index is None:
        def f(o):
            return default

        return f
    else:
        def f(o):
            return o.get_attr(index=index, left=left, right=right, default_val=default)

        return f
