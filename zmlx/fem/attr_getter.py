def attr_getter(index, min, max, default):
    """
    用以生成获取属性的函数
    """
    if index is None:
        def f(o):
            return default

        return f
    else:
        def f(o):
            return o.get_attr(index=index, min=min, max=max, default_val=default)

        return f
